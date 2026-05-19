"""事件总线 — 事件驱动型日志处理。

EventBus 提供发布/订阅模式，允许异步监听器响应日志事件。
典型用途：OTel Span 处理器、Replay Recorder、Metrics 收集器。
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from src.logging.schema import LogRecord

EventHandler = Callable[[LogRecord], Any] | Callable[[LogRecord], Awaitable[Any]]


class EventBus:
    """异步事件总线。

    用法::

        bus = EventBus()
        bus.subscribe("llm.prompt", handler)
        bus.publish(record)
    """

    def __init__(self, async_mode: bool = True) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._wildcard_handlers: list[EventHandler] = []
        self._async_mode = async_mode

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type.endswith(".*") or event_type == "*":
            self._wildcard_handlers.append(handler)
        else:
            self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, record: LogRecord) -> None:
        """发布日志记录到所有匹配的处理器。"""
        handlers = list(self._wildcard_handlers)
        handlers.extend(self._handlers.get(record.event_type, []))
        for handler in handlers:
            try:
                result = handler(record)
                if self._async_mode and isinstance(result, Awaitable):
                    asyncio.ensure_future(result)
            except Exception:
                pass

    async def publish_async(self, record: LogRecord) -> None:
        """异步发布，等待所有处理器完成。"""
        handlers = list(self._wildcard_handlers)
        handlers.extend(self._handlers.get(record.event_type, []))
        for handler in handlers:
            try:
                result = handler(record)
                if isinstance(result, Awaitable):
                    await result
            except Exception:
                pass
