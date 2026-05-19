"""记忆系统日志器 — 检索/存储/衰减。

记录记忆系统的所有操作，便于调试记忆检索效果和存储行为。
"""

from typing import Any

from src.logging.adapter import LoggerAdapter
from src.logging.constants import EventType


class MemoryLogger:
    """记忆系统日志器。

    用法::

        mem_logger = MemoryLogger(adapter)
        mem_logger.retrieval("user_preference", results_count=3, latency_ms=45)
        mem_logger.store("episodic", "用户提到喜欢篮球", importance=0.8)
        mem_logger.decay("semantic", archived=5, removed=2)
    """

    def __init__(self, adapter: LoggerAdapter) -> None:
        self._adapter = adapter

    def retrieval(
        self,
        query: str,
        *,
        results_count: int = 0,
        source: str = "",
        latency_ms: float | None = None,
        **extra: Any,
    ) -> None:
        """记录记忆检索。"""
        self._adapter.info(
            EventType.MEMORY_RETRIEVAL,
            f"记忆检索: {query}",
            query=query,
            results_count=results_count,
            source=source,
            latency_ms=latency_ms,
            **extra,
        )

    def store(
        self,
        memory_type: str,
        content_preview: str,
        *,
        importance: float | None = None,
        **extra: Any,
    ) -> None:
        """记录记忆存储。"""
        self._adapter.info(
            EventType.MEMORY_STORE,
            f"记忆存储 [{memory_type}]",
            memory_type=memory_type,
            content_preview=content_preview[:200],
            importance=importance,
            **extra,
        )

    def decay(self, memory_type: str, *, archived: int = 0, removed: int = 0, **extra: Any) -> None:
        """记录记忆衰减。"""
        self._adapter.info(
            EventType.MEMORY_DECAY,
            f"记忆衰减 [{memory_type}]",
            memory_type=memory_type,
            archived=archived,
            removed=removed,
            **extra,
        )
