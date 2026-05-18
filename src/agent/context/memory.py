"""Memory Context - 记忆上下文桥接层。

连接 Context System 与现有 Memory System。
"""

from __future__ import annotations

import logging

from src.agent.memory import MemoryManager
from src.agent.memory.types import MemoryQuery
from src.llm import TokenCounter

from .types import ContextSegment, ContextType, InjectionPhase

logger = logging.getLogger(__name__)


class MemoryContext:
    """记忆上下文桥接器。

    Args:
        memory: MemoryManager 实例
        token_counter: Token 计数器
        max_memories: 最大注入记忆数
    """

    def __init__(
        self,
        memory: MemoryManager | None = None,
        token_counter: TokenCounter | None = None,
        max_memories: int = 5,
    ) -> None:
        self.memory = memory
        self.token_counter = token_counter or TokenCounter()
        self.max_memories = max_memories

    def retrieve(self, query: str, k: int | None = None) -> list[ContextSegment]:
        if not self.memory:
            return []
        try:
            k = k or self.max_memories
            result = self.memory.on_chat_start(query, max_memories=k)
            if isinstance(result, str):
                seg = ContextSegment.create(
                    ContextType.MEMORY, result,
                    priority=0.5, phase=InjectionPhase.MEMORY,
                )
                seg.token_count = self.token_counter.count(result)
                return [seg]
            return self._to_segments(result)
        except Exception as e:
            logger.warning("Memory retrieval failed: %s", e)
            return []

    def on_chat_end(self, messages: list) -> None:
        if self.memory:
            try:
                self.memory.on_chat_end(messages)
            except Exception as e:
                logger.warning("Memory on_chat_end failed: %s", e)

    def _to_segments(self, memories: list) -> list[ContextSegment]:
        segments = []
        for mem in memories:
            content = mem.content if hasattr(mem, "content") else str(mem)
            importance = getattr(mem, "importance", 0.5)
            seg = ContextSegment.create(
                ContextType.MEMORY, content,
                priority=importance,
                phase=InjectionPhase.MEMORY,
                metadata={"memory_id": getattr(mem, "id", "")},
            )
            seg.token_count = self.token_counter.count(content)
            segments.append(seg)
        return segments
