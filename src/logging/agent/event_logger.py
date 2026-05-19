"""事件日志器 — Session 生命周期和系统事件。

记录 Session 开始/结束、心跳等系统级事件。
"""

from typing import Any

from src.logging.adapter import LoggerAdapter
from src.logging.constants import EventType


class EventLogger:
    """系统事件日志器。

    用法::

        event_logger = EventLogger(adapter)
        event_logger.session_start(session_id="s1")
        event_logger.session_end(session_id="s1", turns=5)
        event_logger.heartbeat(status="running", memory_usage="45%")
    """

    def __init__(self, adapter: LoggerAdapter) -> None:
        self._adapter = adapter

    def session_start(
        self,
        session_id: str,
        *,
        agent_name: str = "",
        **extra: Any,
    ) -> None:
        """记录 Session 开始。"""
        self._adapter.info(
            EventType.SESSION_START,
            f"Session 开始: {session_id}",
            session_id=session_id,
            agent_name=agent_name,
            **extra,
        )

    def session_end(
        self,
        session_id: str,
        *,
        turns: int = 0,
        duration_ms: float | None = None,
        **extra: Any,
    ) -> None:
        """记录 Session 结束。"""
        self._adapter.info(
            EventType.SESSION_END,
            f"Session 结束: {session_id}",
            session_id=session_id,
            turns=turns,
            duration_ms=duration_ms,
            **extra,
        )

    def heartbeat(self, status: str = "running", **extra: Any) -> None:
        """记录系统心跳。"""
        self._adapter.debug(
            EventType.AGENT_EVENT,
            f"心跳: {status}",
            status=status,
            **extra,
        )

    def context_build(self, context_size: int, *, sources: list[str] | None = None, **extra: Any) -> None:
        """记录上下文构建。"""
        self._adapter.info(
            EventType.CONTEXT_BUILD,
            f"上下文构建: {context_size} tokens",
            context_size=context_size,
            sources=sources,
            **extra,
        )

    def context_trim(self, before: int, after: int, **extra: Any) -> None:
        """记录上下文裁剪。"""
        self._adapter.info(
            EventType.CONTEXT_TRIM,
            f"上下文裁剪: {before} → {after} tokens",
            before=before,
            after=after,
            **extra,
        )

    def error(self, error_msg: str, **extra: Any) -> None:
        """记录系统错误。"""
        self._adapter.error(
            EventType.ERROR,
            error_msg,
            exception=error_msg,
            **extra,
        )
