"""AsyncMemoryManager - 异步记忆系统统一 Facade。

专为 AsyncAgent 设计，配合 PGVectorMemoryStore + RedisCache 使用。

生命周期:
    await manager.start()
    await manager.start_session()
    context = await manager.on_chat_start(user_input)
    await manager.on_chat_end(messages)
    messages = await manager.trim_messages(messages)
    await manager.on_reset()
    await manager.stop()
"""

import logging
import time
import uuid
from typing import Any

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
from .stores.pgvector_store import PGVectorMemoryStore
from .stores.redis_cache import RedisCache
from .types import MemoryItem, MemoryQuery
from .working import WorkingMemory

logger = logging.getLogger(__name__)


class AsyncMemoryManager:
    """异步记忆系统管理器 - 供 AsyncAgent 调用的统一 Facade。

    使用 PGVectorMemoryStore 作为主存储后端，RedisCache 作为热缓存层。

    用法::

        manager = AsyncMemoryManager(llm=llm, embedder=embedder)
        await manager.start()
        await manager.start_session()

        await manager.on_chat_start(user_input)
        await manager.on_chat_end(messages)
        messages = await manager.trim_messages(messages)
        await manager.on_reset()
        await manager.stop()
    """

    def __init__(
        self,
        llm: LLMClient,
        embedder: EmbeddingClient | None = None,
        enable_pgvector: bool = True,
        enable_redis: bool = True,
        enable_reflection: bool = True,
        enable_decay: bool = True,
        max_working_tokens: int = 4096,
        pg_dsn: str | None = None,
    ) -> None:
        self.llm = llm
        self.embedder = embedder
        self._enable_reflection = enable_reflection
        self._enable_decay = enable_decay

        self.token_counter = TokenCounter()

        self.pg_store: PGVectorMemoryStore | None = None
        self.cache: RedisCache | None = None
        self._store: MemoryStore | None = None

        if enable_pgvector:
            try:
                self.pg_store = PGVectorMemoryStore(dsn=pg_dsn)
                self._store = self.pg_store
            except Exception as e:
                logger.warning("PGVectorMemoryStore init failed: %s", e)

        if enable_redis:
            try:
                self.cache = RedisCache()
            except Exception as e:
                logger.warning("RedisCache init failed: %s", e)

        self.working = WorkingMemory(
            max_tokens=max_working_tokens, token_counter=self.token_counter
        )
        self.episodic = EpisodicMemory(store=self._store, llm=llm)
        self.semantic = SemanticMemory(store=self._store, llm=llm)
        self.retriever = MemoryRetriever(
            episodic=self.episodic, semantic=self.semantic,
            store=self._store, llm=llm,
        )
        self.router = MemoryRouter(
            episodic=self.episodic, semantic=self.semantic,
            store=self._store, working=self.working,
        )
        self.injector = PromptInjector(token_counter=self.token_counter)
        self.reflection = ReflectionSystem(store=self._store, llm=llm)
        self.decay = ForgettingMechanism()

        self._session_id: str = ""
        self._session_start: float = 0.0
        self._started = False

    async def start(self) -> None:
        """启动所有异步连接。"""
        if self._started:
            return
        if self.pg_store:
            await self.pg_store.connect()
            logger.info("AsyncMemoryManager: PG store connected")
        if self.cache:
            await self.cache.connect()
            logger.info("AsyncMemoryManager: Redis cache connected")
        self._started = True

    async def stop(self) -> None:
        """关闭所有异步连接。"""
        if self.pg_store:
            await self.pg_store.aclose()
        if self.cache:
            await self.cache.close()
        self._started = False
        logger.info("AsyncMemoryManager stopped")

    def start_session(self) -> str:
        self._session_id = str(uuid.uuid4())
        self._session_start = time.time()
        return self._session_id

    async def on_chat_start(
        self, user_input: str, max_memories: int = 5
    ) -> str:
        """异步检索相关记忆并注入 prompt。"""
        if not self._store:
            return ""

        cached_memories: list[dict] = []
        if self.cache:
            try:
                cached_memories = await self.cache.get_hot_memories(
                    self._session_id, k=max_memories
                )
            except Exception as e:
                logger.debug("Redis hot memory miss: %s", e)

        if cached_memories:
            memories = [
                MemoryItem(
                    id=m.get("id", ""),
                    content=m.get("content", ""),
                    type=m.get("type", "unknown"),
                    importance=m.get("importance", 0.5),
                    timestamp=m.get("timestamp", 0.0),
                    metadata=m.get("metadata", {}),
                )
                for m in cached_memories
                if m.get("content")
            ]
        else:
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

            memories = self.retriever.retrieve(
                query, query_embedding=query_embedding
            )

            if memories and self.cache:
                try:
                    await self.cache.set_hot_memories(
                        self._session_id, memories
                    )
                except Exception as e:
                    logger.debug("Redis cache update failed: %s", e)

        if not memories:
            return ""

        return self.injector.inject_memory("", memories, max_tokens=1024)

    async def on_chat_end(self, messages: list[Message]) -> None:
        """异步存储记忆、提取实体、触发反思和衰减。"""
        if not self._store or not messages:
            return

        if len(messages) > 2:
            try:
                episode = self.episodic.store_session(
                    messages, session_id=self._session_id or None
                )
                if self.pg_store:
                    await self.pg_store.save_session(
                        session_id=episode.session_id,
                        summary=episode.summary,
                        message_count=episode.message_count,
                        token_count=episode.token_count,
                    )
                    for i, msg in enumerate(messages):
                        await self.pg_store.save_message(
                            session_id=episode.session_id,
                            role=msg.role,
                            content=msg.content or "",
                            message_index=i,
                            token_count=msg.token_count or 0,
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
                    if reflections and self.pg_store:
                        for ref in reflections:
                            await self.pg_store.save_memory_link(
                                source_id=self._session_id,
                                target_id=ref.reflection_type,
                                relation_type="reflection",
                                strength=ref.importance,
                            )
            except Exception as e:
                logger.warning("Reflection failed: %s", e)

        if self._enable_decay and self.pg_store:
            try:
                if self.decay.should_run():
                    deleted = await self.pg_store.adecay_memories()
                    if deleted:
                        logger.info("Decay removed %d memories", deleted)
            except Exception as e:
                logger.warning("Decay failed: %s", e)

        if self.cache and self._session_id:
            try:
                await self.cache.delete_memory_cache(self._session_id)
            except Exception as e:
                logger.debug("Redis cache invalidation failed: %s", e)

    async def trim_messages(
        self, messages: list[Message]
    ) -> list[Message]:
        return self.working.trim(messages)

    async def on_reset(self) -> None:
        self.working.reset()
        if self.cache and self._session_id:
            try:
                await self.cache.delete_session_cache(self._session_id)
            except Exception as e:
                logger.debug("Redis session cache clear failed: %s", e)
        self._session_id = ""

    async def get_memory_context(
        self, query_text: str, k: int = 5
    ) -> str:
        if not self._store:
            return ""
        query = MemoryQuery(query_text=query_text, k=k)
        query_embedding = None
        if self.embedder:
            try:
                query_embedding = self.embedder.embed(query_text)
            except Exception as e:
                logger.debug("Embedding failed: %s", e)
        memories = self.retriever.retrieve(
            query, query_embedding=query_embedding
        )
        if not memories:
            return ""
        return self.injector.inject_memory("", memories, max_tokens=1024)

    async def save_tool_execution(
        self,
        tool_name: str,
        tool_args: dict,
        result: str | None = None,
        status: str = "success",
        duration_ms: int | None = None,
        error: str | None = None,
        trace_id: str | None = None,
    ) -> str | None:
        if not self.pg_store:
            return None
        return await self.pg_store.save_tool_call(
            session_id=self._session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            status=status,
            tool_result=result,
            duration_ms=duration_ms,
            error_message=error,
            trace_id=trace_id,
        )

    async def save_summary(
        self,
        summary_text: str,
        summary_type: str = "auto",
        importance: float = 0.5,
        embedding: list[float] | None = None,
    ) -> str | None:
        if not self.pg_store:
            return None
        return await self.pg_store.save_summary(
            session_id=self._session_id,
            summary_text=summary_text,
            summary_type=summary_type,
            importance=importance,
            embedding=embedding,
        )

    async def agent_state(self) -> dict[str, Any]:
        return {
            "session_id": self._session_id,
            "session_start": self._session_start,
            "started": self._started,
            "pg_connected": self.pg_store._connected if self.pg_store else False,
            "redis_connected": self.cache._connected if self.cache else False,
            "reflection_enabled": self._enable_reflection,
            "decay_enabled": self._enable_decay,
        }

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def pg(self) -> PGVectorMemoryStore | None:
        return self.pg_store

    @property
    def redis(self) -> RedisCache | None:
        return self.cache
