"""领域日志器测试。"""

from src.logging.adapter import NullAdapter
from src.logging.agent import AgentLogger, EventLogger, LLMLogger, MemoryLogger, ToolLogger


class TestAgentLogger:
    def setup_method(self) -> None:
        self.logger = AgentLogger(NullAdapter())

    def test_thought(self) -> None:
        self.logger.thought("思考中", iteration=1)

    def test_decision(self) -> None:
        self.logger.decision("调用工具", reasoning="需要数据")

    def test_reflection(self) -> None:
        self.logger.reflection("学到了新东西")

    def test_with_extra_payload(self) -> None:
        self.logger.thought("思考", iteration=2, confidence=0.9)


class TestToolLogger:
    def setup_method(self) -> None:
        self.logger = ToolLogger(NullAdapter())

    def test_log_call(self) -> None:
        self.logger.log_call("web_search", {"query": "天气"})

    def test_log_result(self) -> None:
        self.logger.log_result("web_search", "结果内容", duration_ms=100.0)

    def test_log_error(self) -> None:
        self.logger.log_error("web_search", "超时", duration_ms=5000.0)

    def test_context_manager_success(self) -> None:
        with self.logger.call("calc", {"expr": "1+1"}):
            pass

    def test_context_manager_error(self) -> None:
        class TestError(Exception):
            pass

        try:
            with self.logger.call("failing_tool"):
                raise TestError("工具失败")
        except TestError:
            pass


class TestLLMLogger:
    def setup_method(self) -> None:
        self.logger = LLMLogger(NullAdapter())

    def test_prompt(self) -> None:
        self.logger.prompt("deepseek-chat", [{"role": "user", "content": "hi"}])

    def test_prompt_with_tools(self) -> None:
        self.logger.prompt("deepseek-chat", [{"role": "user", "content": "hi"}], tools=[{"type": "function"}])

    def test_response(self) -> None:
        self.logger.response(
            "deepseek-chat", "response text",
            prompt_tokens=50, completion_tokens=100, latency_ms=500.0,
        )

    def test_stream_token(self) -> None:
        self.logger.stream_token("deepseek-chat", "Hello")

    def test_error(self) -> None:
        self.logger.error("deepseek-chat", "API timeout", latency_ms=10000.0)

    def test_duration_ms(self) -> None:
        import time
        start = time.monotonic()
        time.sleep(0.01)
        dur = LLMLogger.duration_ms(start)
        assert dur >= 10


class TestMemoryLogger:
    def setup_method(self) -> None:
        self.logger = MemoryLogger(NullAdapter())

    def test_retrieval(self) -> None:
        self.logger.retrieval("user preference", results_count=5, latency_ms=30.0)

    def test_store(self) -> None:
        self.logger.store("episodic", "用户喜欢篮球", importance=0.8)

    def test_decay(self) -> None:
        self.logger.decay("semantic", archived=3, removed=1)


class TestEventLogger:
    def setup_method(self) -> None:
        self.logger = EventLogger(NullAdapter())

    def test_session_start(self) -> None:
        self.logger.session_start("session-1")

    def test_session_end(self) -> None:
        self.logger.session_end("session-1", turns=5, duration_ms=30000.0)

    def test_heartbeat(self) -> None:
        self.logger.heartbeat(status="running")

    def test_context_build(self) -> None:
        self.logger.context_build(2048, sources=["memory", "tools"])

    def test_context_trim(self) -> None:
        self.logger.context_trim(5000, 3000)

    def test_error(self) -> None:
        self.logger.error("系统异常")
