"""MemoryManager - 记忆系统统一 Facade。

供 Agent 调用的高层接口，协调所有记忆模块：
1. on_chat_start: 检索相关记忆并注入到 prompt
2. on_chat_end: 更新情景记忆和语义记忆，触发反思
3. trim_messages: 工作记忆窗口裁剪
4. on_reset: 重置工作记忆
"""

import logging
import time
import uuid
from pathlib import Path

from src.llm import LLMClient, Message, TokenCounter
from src.rag.embed import EmbeddingClient

from .decay import ForgettingMechanism
from .episodic import EpisodicMemory
from .injector import PromptInjector
from .reflection import ReflectionSystem
from .retrieval import MemoryRetriever
from .router import MemoryRouter
from .semantic import SemanticMemory
from .stores.base import MemoryStore
from .stores.chroma_store import ChromaMemoryStore
from .stores.sql_store import SQLMemoryStore
from .types import MemoryItem, MemoryQuery
from .working import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """记忆系统管理器 - 供 Agent 调用的统一 Facade。

    用法::

        memory = MemoryManager(llm=llm, embedder=embedder)
        memory.start_session()
        memory.on_chat_start(user_input)   # 检索记忆
        memory.on_chat_end(messages)       # 存储记忆
        memory.trim_messages(messages)     # 裁剪窗口
    """

    def __init__(
        self,
        llm: LLMClient,
        embedder: EmbeddingClient | None = None,
        chroma_path: str | Path | None = None,
        sqlite_path: str | Path = "memory.db",
        enable_chroma: bool = True,
        enable_sqlite: bool = True,
        enable_reflection: bool = True,
        enable_decay: bool = True,
        max_working_tokens: int = 4096,
    ) -> None:
        self.llm = llm
        self.embedder = embedder
        self._enable_reflection = enable_reflection
        self._enable_decay = enable_decay

        self.token_counter = TokenCounter()

        # 存储后端
        self.chroma_store: MemoryStore | None = None
        self.sql_store: SQLMemoryStore | None = None

        if enable_chroma:
            try:
                self.chroma_store = ChromaMemoryStore(
                    collection_name="memories", persist_path=chroma_path,
                )
            except Exception as e:
                logger.warning("ChromaDB init failed: %s", e)

        if enable_sqlite:
            try:
                self.sql_store = SQLMemoryStore(db_path=sqlite_path)
            except Exception as e:
                logger.warning("SQLite init failed: %s", e)

        self._store: MemoryStore = self.chroma_store or self.sql_store

        # 记忆层
        self.working = WorkingMemory(max_tokens=max_working_tokens, token_counter=self.token_counter)
        self.episodic = EpisodicMemory(store=self._store, llm=llm)
        self.semantic = SemanticMemory(store=self._store, llm=llm)
        self.retriever = MemoryRetriever(episodic=self.episodic, semantic=self.semantic, store=self._store, llm=llm)
        self.router = MemoryRouter(episodic=self.episodic, semantic=self.semantic, store=self._store, working=self.working)
        self.injector = PromptInjector(token_counter=self.token_counter)
        self.reflection = ReflectionSystem(store=self._store, llm=llm)
        self.decay = ForgettingMechanism()

        self._session_id: str = ""
        self._session_start: float = 0.0

    def start_session(self) -> str:
        self._session_id = str(uuid.uuid4())
        self._session_start = time.time()
        return self._session_id

    def on_chat_start(self, user_input: str, max_memories: int = 5) -> str:
        if not self._store:
            return ""

        query = MemoryQuery(
            query_text=user_input,
            k=max_memories,
            memory_types=["episode", "entity", "preference", "reflection"],
        )

        query_embedding = None
        if self.embedder:
            try:
                query_embedding = self.embedder.embed(user_input)
            except Exception as e:
                logger.debug("Embedding failed: %s", e)

        memories = self.retriever.retrieve(query, query_embedding=query_embedding)
        if not memories:
            return ""

        return self.injector.inject_memory("", memories, max_tokens=1024)

    def on_chat_end(self, messages: list[Message]) -> None:
        if not self._store or not messages:
            return

        if len(messages) > 2:
            try:
                episode = self.episodic.store_session(messages, session_id=self._session_id or None)
                if self.sql_store:
                    self.sql_store.save_session(
                        session_id=episode.session_id, summary=episode.summary,
                        message_count=episode.message_count, token_count=episode.token_count,
                        start_time=episode.start_time, end_time=episode.end_time,
                        importance=episode.importance,
                    )
            except Exception as e:
                logger.warning("Failed to store episode: %s", e)

        try:
            extracted = self.semantic.extract_from_messages(messages)
            if extracted:
                self.semantic.merge(extracted)
        except Exception as e:
            logger.warning("Failed to extract entities: %s", e)

        if self._enable_reflection:
            try:
                if self.reflection.should_reflect():
                    reflections = self.reflection.run()
                    if reflections and self.sql_store:
                        for ref in reflections:
                            self.sql_store.save_reflection(
                                content=ref.content, reflection_type=ref.reflection_type,
                                source_ids=ref.source_ids, importance=ref.importance,
                            )
            except Exception as e:
                logger.warning("Reflection failed: %s", e)

        if self._enable_decay:
            try:
                if self.decay.should_run():
                    self.decay.run_maintenance(self._store)
            except Exception as e:
                logger.warning("Decay failed: %s", e)

    def trim_messages(self, messages: list[Message]) -> list[Message]:
        return self.working.trim(messages)

    def on_reset(self) -> None:
        self.working.reset()
        self._session_id = ""

    def get_memory_context(self, query_text: str, k: int = 5) -> str:
        memories = self.retriever.retrieve(MemoryQuery(query_text=query_text, k=k))
        if not memories:
            return ""
        return self.injector.inject_memory("", memories, max_tokens=1024)

    @property
    def session_id(self) -> str:
        return self._session_id

    def close(self) -> None:
        if self.sql_store:
            self.sql_store.close()
