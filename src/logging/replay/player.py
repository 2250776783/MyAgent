"""日志播放器 — 读取记录的 JSONL 文件并按时间顺序重放。

可用于调试、测试回放、审计检查等场景。

用法::

    player = LogPlayer("./replay_logs/replay_all.jsonl")
    for record in player.replay():
        print(record.event_type, record.message)
"""

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

from src.logging.schema import LogRecord


class LogPlayer:
    """日志播放器。

    读取 JSONL 格式的日志文件，重建 LogRecord 对象。
    支持按 event_type 过滤和时间排序。
    """

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)

    def replay(self, event_filter: set[str] | None = None) -> Generator[LogRecord, None, None]:
        """按时间顺序回放日志。

        Args:
            event_filter: 可选的事件类型白名单

        Yields:
            LogRecord 对象
        """
        if not self._file_path.exists():
            return

        with open(self._file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                record = self._dict_to_record(data)
                if event_filter and record.event_type not in event_filter:
                    continue
                yield record

    def replay_sorted(self, event_filter: set[str] | None = None) -> list[LogRecord]:
        """返回按时间戳排序的日志记录列表。"""
        records = list(self.replay(event_filter=event_filter))
        records.sort(key=lambda r: r.timestamp)
        return records

    @staticmethod
    def _dict_to_record(data: dict[str, Any]) -> LogRecord:
        return LogRecord(
            timestamp=data.get("timestamp", ""),
            trace_id=data.get("trace_id", ""),
            session_id=data.get("session_id", ""),
            span_id=data.get("span_id", ""),
            parent_span_id=data.get("parent_span_id", ""),
            agent_name=data.get("agent_name", ""),
            level=data.get("level", "INFO"),
            event_type=data.get("event_type", ""),
            message=data.get("message", ""),
            payload=data.get("payload", {}),
            duration_ms=data.get("duration_ms"),
            exception=data.get("exception"),
        )
