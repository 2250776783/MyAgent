"""日志适配器接口与实现。

通过 LoggerAdapter 抽象接口解耦业务代码与具体日志库。
业务代码面向接口编程，不直接依赖 loguru 或标准 logging。
"""

from abc import ABC, abstractmethod
from typing import Any


class LoggerAdapter(ABC):
    """日志适配器抽象接口。

    所有业务代码通过此接口记录日志，不直接依赖 loguru/logging。
    通过依赖注入方式传入具体实现。
    """

    @abstractmethod
    def log(
        self,
        level: str,
        event_type: str,
        message: str,
        *,
        payload: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        exception: str | None = None,
    ) -> None: ...

    def trace(self, event_type: str, message: str, **payload: Any) -> None:
        self.log("TRACE", event_type, message, payload=payload)

    def debug(self, event_type: str, message: str, **payload: Any) -> None:
        self.log("DEBUG", event_type, message, payload=payload)

    def info(self, event_type: str, message: str, **payload: Any) -> None:
        self.log("INFO", event_type, message, payload=payload)

    def warning(self, event_type: str, message: str, **payload: Any) -> None:
        self.log("WARNING", event_type, message, payload=payload)

    def error(
        self,
        event_type: str,
        message: str,
        *,
        exception: str | None = None,
        **payload: Any,
    ) -> None:
        self.log("ERROR", event_type, message, payload=payload, exception=exception)

    def critical(
        self,
        event_type: str,
        message: str,
        *,
        exception: str | None = None,
        **payload: Any,
    ) -> None:
        self.log("CRITICAL", event_type, message, payload=payload, exception=exception)


class NullAdapter(LoggerAdapter):
    """空适配器，所有日志丢弃。用于测试或关闭日志的场景。"""

    def log(
        self,
        level: str = "INFO",
        event_type: str = "",
        message: str = "",
        *,
        payload: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        exception: str | None = None,
    ) -> None:
        pass


class LoguruAdapter(LoggerAdapter):
    """基于 loguru 的日志适配器实现。

    将 LogRecord 同时发送到 Pipeline 和 EventBus。
    """

    def __init__(self) -> None:
        self._pipeline: Any = None
        self._event_bus: Any = None

    def set_pipeline(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    def set_event_bus(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def log(
        self,
        level: str,
        event_type: str,
        message: str,
        *,
        payload: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        exception: str | None = None,
    ) -> None:
        from src.logging.schema import LogRecord

        record = LogRecord.create(
            level=level,
            event_type=event_type,
            message=message,
            payload=payload,
            duration_ms=duration_ms,
            exception=exception,
        )

        if self._pipeline:
            self._pipeline.emit(record)
        if self._event_bus:
            self._event_bus.publish(record)
