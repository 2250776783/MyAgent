"""工具执行追踪。

记录每次工具调用的输入、输出、耗时等信息，用于调试和监控。
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceEntry:
    """单次工具调用的追踪记录。"""

    tool_name: str
    args: dict[str, Any]
    result: str = ""
    error: str = ""
    success: bool = False
    duration_ms: float = 0.0
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)


class ToolTracer:
    """工具调用追踪器。

    记录每次工具调用的详细信息，支持导出和统计。
    """

    def __init__(self) -> None:
        self._entries: list[TraceEntry] = []

    @property
    def entries(self) -> list[TraceEntry]:
        return list(self._entries)

    def record(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: str = "",
        error: str = "",
        success: bool = False,
        duration_ms: float = 0.0,
    ) -> TraceEntry:
        entry = TraceEntry(
            tool_name=tool_name,
            args=args,
            result=result,
            error=error,
            success=success,
            duration_ms=duration_ms,
        )
        self._entries.append(entry)
        return entry

    def clear(self) -> None:
        self._entries.clear()

    def summary(self) -> dict[str, Any]:
        total = len(self._entries)
        success_count = sum(1 for e in self._entries if e.success)
        return {
            "total_calls": total,
            "success_count": success_count,
            "failure_count": total - success_count,
            "avg_duration_ms": sum(e.duration_ms for e in self._entries) / total if total else 0.0,
        }
