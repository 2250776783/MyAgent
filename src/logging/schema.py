"""结构化日志数据模型。

LogRecord 是贯穿整个日志系统的统一数据结构，
所有日志类型共享此 schema，通过 event_type 区分。
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class LogRecord:
    """统一结构化日志记录。

    系统字段（自动从 contextvars 填充）:
        timestamp: ISO 8601 时间戳
        trace_id: 追踪 ID
        session_id: 会话 ID
        span_id: 当前 span ID
        parent_span_id: 父 span ID
        agent_name: Agent 名称
        level: 日志级别

    业务字段:
        event_type: 事件类型
        message: 人类可读描述
        payload: 结构化数据
        duration_ms: 操作耗时
        exception: 异常信息
    """
    timestamp: str = ""
    trace_id: str = ""
    session_id: str = ""
    span_id: str = ""
    parent_span_id: str = ""
    agent_name: str = ""
    level: str = "INFO"
    event_type: str = ""
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None
    exception: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（含 @timestamp 字段用于 ELK）。"""
        return {"@timestamp": self.timestamp, **asdict(self)}

    def to_json(self) -> str:
        """序列化为 JSON 字符串。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def create(
        cls,
        level: str,
        event_type: str,
        message: str,
        *,
        payload: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        exception: str | None = None,
    ) -> "LogRecord":
        """工厂方法，自动从 contextvars 填充上下文字段。"""
        from src.logging.context import TraceContext as TC

        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trace_id=TC.get_trace_id(),
            session_id=TC.get_session_id(),
            span_id=TC.get_span_id(),
            parent_span_id=TC.get_parent_span_id(),
            agent_name=TC.get_agent_name(),
            level=level,
            event_type=event_type,
            message=message,
            payload=payload or {},
            duration_ms=duration_ms,
            exception=exception,
        )
