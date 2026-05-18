"""Tool Context - 工具调用上下文管理器。

管理工具调用记录，控制输出长度（防 tool output explosion），
检测工具调用循环。
"""

from __future__ import annotations

from typing import Any

from .types import ToolCallRecord, ContextSegment


class ToolContext:
    """工具上下文管理器。

    Args:
        max_records: 保留的最大记录数
        max_output_chars: 单条输出最大字符数
        max_chain_length: 连续工具调用链最大长度
    """

    def __init__(
        self,
        max_records: int = 20,
        max_output_chars: int = 2000,
        max_chain_length: int = 8,
    ) -> None:
        self._records: list[ToolCallRecord] = []
        self.max_records = max_records
        self.max_output_chars = max_output_chars
        self.max_chain_length = max_chain_length

    @property
    def records(self) -> list[ToolCallRecord]:
        return list(self._records)

    def record_call(self, tool_name: str, arguments: dict[str, Any]) -> str:
        record = ToolCallRecord(tool_name=tool_name, arguments=arguments)
        self._records.append(record)
        return record.call_id

    def record_result(
        self, call_id: str, result: str, success: bool, duration_ms: float = 0.0,
    ) -> None:
        for record in self._records:
            if record.call_id == call_id:
                record.result = result
                record.success = success
                record.duration_ms = duration_ms
                break
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

    def detect_tool_loop(self) -> bool:
        recent = self._records[-self.max_chain_length:]
        if len(recent) < 3:
            return False
        names = [r.tool_name for r in recent]
        if len(set(names)) <= 2 and len(recent) >= 5:
            return True
        return False

    def get_failures(self, count: int = 3) -> list[ToolCallRecord]:
        return [r for r in reversed(self._records) if not r.success][:count]

    def build_context(self) -> list[ContextSegment]:
        segments = []
        for record in self._records[-5:]:
            seg = record.to_context(max_chars=self.max_output_chars)
            segments.append(seg)
        return segments
