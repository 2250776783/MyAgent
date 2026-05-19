"""TraceContext 上下文传播测试。"""

import asyncio

from src.logging.context import TraceContext


class TestTraceContext:
    def test_init_sets_trace_id(self) -> None:
        TraceContext.init(trace_id="abc123")
        assert TraceContext.get_trace_id() == "abc123"

    def test_init_session_id(self) -> None:
        TraceContext.init(session_id="session-1")
        assert TraceContext.get_session_id() == "session-1"

    def test_init_agent_name(self) -> None:
        TraceContext.init(agent_name="test-agent")
        assert TraceContext.get_agent_name() == "test-agent"

    def test_auto_generates_trace_id(self) -> None:
        TraceContext.init()
        tid = TraceContext.get_trace_id()
        assert len(tid) == 12

    def test_to_dict_returns_all_fields(self) -> None:
        TraceContext.init(trace_id="t1", session_id="s1", agent_name="a1")
        d = TraceContext.to_dict()
        assert d["trace_id"] == "t1"
        assert d["session_id"] == "s1"
        assert d["agent_name"] == "a1"

    def test_span_manages_parent_child(self) -> None:
        TraceContext.init(trace_id="span-test")
        parent_span_before = TraceContext.get_span_id()

        with TraceContext.span("op1") as span:
            assert span.operation == "op1"
            assert TraceContext.get_parent_span_id() == parent_span_before
            child_span_id = TraceContext.get_span_id()
            assert child_span_id != parent_span_before

        assert TraceContext.get_span_id() == parent_span_before

    def test_span_duration(self) -> None:
        TraceContext.init(trace_id="dur-test")
        import time

        with TraceContext.span("slow") as span:
            time.sleep(0.01)

        assert span.duration_ms is not None
        assert span.duration_ms >= 10

    def test_async_propagation(self) -> None:
        TraceContext.init(trace_id="async-test", session_id="async-s1")

        async def worker() -> tuple[str, str]:
            await asyncio.sleep(0.01)
            return TraceContext.get_trace_id(), TraceContext.get_session_id()

        async def run() -> None:
            results = await asyncio.gather(worker(), worker())
            for tid, sid in results:
                assert tid == "async-test"
                assert sid == "async-s1"

        asyncio.run(run())

    def test_span_nested_restores_correctly(self) -> None:
        TraceContext.init(trace_id="nested")
        orig = TraceContext.get_span_id()

        with TraceContext.span("outer"):
            outer_id = TraceContext.get_span_id()
            with TraceContext.span("inner"):
                inner_id = TraceContext.get_span_id()
                assert inner_id != outer_id
            assert TraceContext.get_span_id() == outer_id

        assert TraceContext.get_span_id() == orig
