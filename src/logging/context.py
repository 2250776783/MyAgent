"""Trace 上下文管理器 — 基于 contextvars 的隐式上下文传播。

通过 contextvars 自动跨 asyncio 任务传播 trace_id/session_id/span_id，
业务代码无需手动传递这些参数。

用法::

    TraceContext.init(trace_id="abc123", session_id="s1")
    with TraceContext.span("llm_call", model="deepseek") as span:
        logger.info(...)  # 自动携带 trace_id, span_id
"""

import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Generator


@dataclass
class Span:
    """一个追踪跨度，代表一个原子操作单元。"""
    trace_id: str
    span_id: str
    parent_span_id: str | None
    agent_name: str
    operation: str
    start_time: float
    end_time: float | None = None
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is not None:
            return (self.end_time - self.start_time) * 1000
        return None

    def finish(self) -> None:
        self.end_time = time.time()


class _ContextVars:
    trace_id: ContextVar[str] = ContextVar("trace_id", default="")
    session_id: ContextVar[str] = ContextVar("session_id", default="")
    span_id: ContextVar[str] = ContextVar("span_id", default="")
    parent_span_id: ContextVar[str] = ContextVar("parent_span_id", default="")
    agent_name: ContextVar[str] = ContextVar("agent_name", default="")
    user_id: ContextVar[str] = ContextVar("user_id", default="")


_ctx = _ContextVars()


class TraceContext:
    """Trace 上下文管理器。使用静态方法，不要实例化。"""

    @staticmethod
    def init(
        trace_id: str | None = None,
        session_id: str | None = None,
        agent_name: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """初始化上下文。通常在请求入口处调用。"""
        if trace_id:
            _ctx.trace_id.set(trace_id)
        else:
            _ctx.trace_id.set(uuid.uuid4().hex[:12])
        if session_id:
            _ctx.session_id.set(session_id)
        if agent_name:
            _ctx.agent_name.set(agent_name)
        if user_id:
            _ctx.user_id.set(user_id)

    @staticmethod
    def get_trace_id() -> str:
        return _ctx.trace_id.get()

    @staticmethod
    def get_session_id() -> str:
        return _ctx.session_id.get()

    @staticmethod
    def get_span_id() -> str:
        return _ctx.span_id.get()

    @staticmethod
    def get_parent_span_id() -> str:
        return _ctx.parent_span_id.get()

    @staticmethod
    def get_agent_name() -> str:
        return _ctx.agent_name.get()

    @staticmethod
    def get_user_id() -> str:
        return _ctx.user_id.get()

    @staticmethod
    def to_dict() -> dict[str, str]:
        return {
            "trace_id": _ctx.trace_id.get(),
            "session_id": _ctx.session_id.get(),
            "span_id": _ctx.span_id.get(),
            "parent_span_id": _ctx.parent_span_id.get(),
            "agent_name": _ctx.agent_name.get(),
        }

    @staticmethod
    @contextmanager
    def span(operation: str, **tags: str) -> Generator[Span, Any, None]:
        """创建一个子 Span，自动管理 parent/child 关系和上下文恢复。

        Args:
            operation: 操作名称，如 "llm_call", "tool_execute"
            **tags: 额外标签

        Yields:
            Span 实例
        """
        parent_span_id = _ctx.span_id.get()
        span_id = uuid.uuid4().hex[:12]
        _ctx.parent_span_id.set(parent_span_id)
        _ctx.span_id.set(span_id)

        span = Span(
            trace_id=_ctx.trace_id.get(),
            span_id=span_id,
            parent_span_id=parent_span_id or None,
            agent_name=_ctx.agent_name.get(),
            operation=operation,
            start_time=time.time(),
            tags=tags,
        )
        try:
            yield span
        finally:
            span.finish()
            _ctx.span_id.set(parent_span_id)
