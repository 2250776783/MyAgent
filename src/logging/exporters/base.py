"""导出器基类 — 连接 EventBus 与外部系统的桥梁。

所有导出器通过 subscribe 到 EventBus 接收 LogRecord，
在后台异步转发到外部系统（OTel、ES、Loki）。
"""

from abc import ABC, abstractmethod
from typing import Any

from src.logging.schema import LogRecord


class BaseExporter(ABC):
    """导出器抽象基类。

    EventBus 的事件处理器，收到 LogRecord 后批量调用 export()。

    用法::

        bus.subscribe("*", exporter)
    """

    def __init__(self, batch_size: int = 100) -> None:
        self.batch_size = batch_size
        self._buffer: list[LogRecord] = []

    def __call__(self, record: LogRecord) -> None:
        """EventBus 兼容的事件处理器。"""
        self._buffer.append(record)
        if len(self._buffer) >= self.batch_size:
            self._flush()

    @abstractmethod
    def export(self, records: list[LogRecord]) -> None:
        """批量导出日志记录到外部系统。"""

    def flush(self) -> None:
        """强制刷新缓冲区。"""
        if self._buffer:
            self._flush()

    def _flush(self) -> None:
        try:
            self.export(list(self._buffer))
            self._buffer.clear()
        except Exception:
            pass
