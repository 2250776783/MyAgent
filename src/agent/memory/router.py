"""Memory Router - 统一读写入口。

路由所有记忆读写请求到正确的记忆层，
协调 EpisodicMemory、SemanticMemory、WorkingMemory 和多存储后端。
"""

import logging

from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .stores.base import MemoryStore
from .types import MemoryInput, MemoryItem, MemoryQuery
from .working import WorkingMemory

logger = logging.getLogger(__name__)


class MemoryRouter:
    """记忆路由器。

    统一入口，根据记忆类型路由到正确的记忆层：
    - "episode" → EpisodicMemory
    - "entity"/"preference" → SemanticMemory
    - 其他 → MemoryStore 直接存取
    """

    def __init__(
        self,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        store: MemoryStore,
        working: WorkingMemory,
    ) -> None:
        self.episodic = episodic
        self.semantic = semantic
        self.store = store
        self.working = working

    def write(self, memory_input: MemoryInput) -> str | None:
        item = MemoryItem(
            id="",
            content=memory_input.content,
            type=memory_input.type,
            importance=memory_input.importance,
            timestamp=0,
            metadata=memory_input.metadata,
            source_session=memory_input.source_session,
        )

        if memory_input.type == "episode":
            return self.episodic.store_session([]).session_id
        elif memory_input.type in ("entity", "preference"):
            saved = self.semantic.merge([item])
            return saved[0].id if saved else None
        else:
            from .scorer import ImportanceScorer
            scorer = ImportanceScorer()
            item.importance = scorer.estimate_llm_importance(memory_input.content)
            import time
            import uuid
            item.id = str(uuid.uuid4())
            item.timestamp = time.time()
            return self.store.save(item)

    def read(self, query: MemoryQuery) -> list[MemoryItem]:
        from .retrieval import MemoryRetriever
        retriever = MemoryRetriever(
            self.episodic, self.semantic, self.store, self.episodic.llm
        )
        return retriever.retrieve(query)
