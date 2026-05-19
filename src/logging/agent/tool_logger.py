"""工具调用日志器 — 完整生命周期追踪。

记录工具调用的开始、结果和错误，支持 context manager 自动追踪。
"""

import time
from contextlib import contextmanager
from typing import Any, Generator

from src.logging.adapter import LoggerAdapter
from src.logging.constants import EventType


class ToolLogger:
    """工具调用生命周期日志器。

    用法::

        tool_logger = ToolLogger(adapter)
        with tool_logger.call("web_search", {"query": "天气"}):
            result = search_tool.run("天气")
        # 自动记录 call + result，含 duration

        # 或手动记录:
        tool_logger.log_call("calc", {"expr": "1+1"})
        ...
        tool_logger.log_result("calc", "2")
    """

    def __init__(self, adapter: LoggerAdapter) -> None:
        self._adapter = adapter

    def log_call(self, tool_name: str, args: dict[str, Any] | None = None) -> None:
        """记录工具调用开始。"""
        self._adapter.info(
            EventType.TOOL_CALL,
            f"工具调用: {tool_name}",
            tool_name=tool_name,
            args=args or {},
        )

    def log_result(self, tool_name: str, output: str = "", *, duration_ms: float | None = None) -> None:
        """记录工具调用结果。"""
        self._adapter.info(
            EventType.TOOL_RESULT,
            f"工具结果: {tool_name}",
            tool_name=tool_name,
            duration_ms=duration_ms,
        )

    def log_error(self, tool_name: str, error: str, *, duration_ms: float | None = None) -> None:
        """记录工具调用错误。"""
        self._adapter.error(
            EventType.TOOL_ERROR,
            f"工具错误: {tool_name}",
            exception=error,
            tool_name=tool_name,
            duration_ms=duration_ms,
        )

    @contextmanager
    def call(self, tool_name: str, args: dict[str, Any] | None = None) -> Generator[None, Any, None]:
        """工具调用的 context manager，自动记录开始和结束。

        用法::

            with tool_logger.call("web_search", {"query": "天气"}):
                result = search_tool.run("天气")
        """
        self.log_call(tool_name, args)
        start = time.monotonic()
        try:
            yield
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            self.log_error(tool_name, str(e), duration_ms=duration)
            raise
        else:
            duration = (time.monotonic() - start) * 1000
            self.log_result(tool_name, "", duration_ms=duration)
