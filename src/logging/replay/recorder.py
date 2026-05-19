"""日志记录器 — 将日志流持久化到文件，用于后续重放。

以 JSONL 格式（每行一个 JSON LogRecord）写入磁盘。
每个 session 可独立记录到单独文件。

用法::

    recorder = LogRecorder(log_dir="./replay_logs")
    event_bus.subscribe("*", recorder)
    # ...
    recorder.close()
"""

from pathlib import Path
from typing import Any

from src.logging.schema import LogRecord


class LogRecorder:
    """日志记录器。

    将所有 LogRecord 序列化为 JSONL 文件。
    支持按 session_id 拆分文件或写入单个全局文件。
    """

    def __init__(self, log_dir: str | Path = "./replay_logs", split_by_session: bool = False) -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._split_by_session = split_by_session
        self._files: dict[str, Any] = {}

    def __call__(self, record: LogRecord) -> None:
        self._write(record)

    def _write(self, record: LogRecord) -> None:
        key = record.session_id if self._split_by_session and record.session_id else "_global"
        f = self._files.get(key)
        if f is None:
            name = f"replay_{key}.jsonl" if key != "_global" else "replay_all.jsonl"
            path = self._log_dir / name
            f = open(path, "a", encoding="utf-8")
            self._files[key] = f
        f.write(record.to_json() + "\n")
        f.flush()

    def close(self) -> None:
        for f in self._files.values():
            f.close()
        self._files.clear()
