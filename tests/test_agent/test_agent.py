"""测试 Agent 主类。"""

from unittest.mock import MagicMock

import pytest

from src.agent import Agent
from src.agent.tools.base import BaseTool, ToolOutput
from src.llm import Message


class EchoTool(BaseTool):
    name: str = "echo"
    description: str = "回显输入"

    def _run(self, **kwargs: str) -> ToolOutput:
        return ToolOutput(success=True, output=f"echo: {kwargs.get('text', '')}")


def make_fake_response(content: str = "", tool_calls: list | None = None) -> Message:
    return Message(role="assistant", content=content, tool_calls=tool_calls)


class TestAgentInit:
    def test_init_without_tools(self) -> None:
        llm = MagicMock()
        agent = Agent(llm=llm)
        assert agent.max_iterations == 10
        assert len(agent.messages) == 1
        assert agent.messages[0].role == "system"

    def test_init_with_tools(self) -> None:
        llm = MagicMock()
        tool = EchoTool()
        agent = Agent(llm=llm, tools=[tool])
        assert agent.tool_registry.get("echo") is tool

    def test_custom_system_prompt(self) -> None:
        llm = MagicMock()
        agent = Agent(llm=llm, system_prompt="自定义提示")
        assert agent.messages[0].content == "自定义提示"


class TestAgentChat:
    def test_direct_response_no_tools(self) -> None:
        """LLM 直接返回文本，不调用工具。"""
        llm = MagicMock()
        llm.chat.return_value = make_fake_response("你好！")
        agent = Agent(llm=llm)
        result = agent.chat("hi")
        assert result == "你好！"
        assert len(agent.messages) == 3  # system + user + assistant

    def test_single_tool_call(self) -> None:
        """LLM 调用一次工具后返回最终回答。"""
        llm = MagicMock()
        tool = EchoTool()
        first_response = make_fake_response(
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": '{"text": "hello"}'},
                }
            ]
        )
        second_response = make_fake_response("回显结果：echo: hello")
        llm.chat.side_effect = [first_response, second_response]

        agent = Agent(llm=llm, tools=[tool])
        result = agent.chat("帮我回显 hello")
        assert result == "回显结果：echo: hello"
        assert llm.chat.call_count == 2

    def test_max_iterations_exceeded(self) -> None:
        """超过最大迭代次数时返回提示。"""
        llm = MagicMock()
        tool = EchoTool()
        tool_call_response = make_fake_response(
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": '{"text": "x"}'},
                }
            ]
        )
        llm.chat.return_value = tool_call_response

        agent = Agent(llm=llm, tools=[tool], max_iterations=3)
        result = agent.chat("loop")
        assert "最大迭代次数" in result

    def test_tool_execution_error(self) -> None:
        """工具执行出错时返回错误信息。"""
        llm = MagicMock()

        class BrokenTool(BaseTool):
            name: str = "broken"
            description: str = "会出错的工具"

            def _run(self, **kwargs: str) -> ToolOutput:
                raise ValueError("出错了")

        tool_call_response = make_fake_response(
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "broken", "arguments": "{}"},
                }
            ]
        )
        second_response = make_fake_response("工具出错了")
        llm.chat.side_effect = [tool_call_response, second_response]

        agent = Agent(llm=llm, tools=[BrokenTool()])
        result = agent.chat("测试错误")
        assert result == "工具出错了"
        tool_msg = agent.messages[3]
        assert tool_msg.role == "tool"
        assert "错误" in tool_msg.content


class TestAgentChatStream:
    def test_stream_direct_response(self) -> None:
        llm = MagicMock()
        llm.chat.return_value = make_fake_response("流式回答")
        agent = Agent(llm=llm)
        chunks = list(agent.chat_stream("hi"))
        assert chunks == ["流式回答"]

    def test_stream_tool_then_response(self) -> None:
        llm = MagicMock()
        tool = EchoTool()
        first_response = make_fake_response(
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": '{"text": "x"}'},
                }
            ]
        )
        second_response = make_fake_response("最终回答")
        llm.chat.side_effect = [first_response, second_response]

        agent = Agent(llm=llm, tools=[tool])
        chunks = list(agent.chat_stream("hi"))
        assert chunks == ["最终回答"]

    def test_stream_max_iterations(self) -> None:
        llm = MagicMock()
        tool = EchoTool()
        tool_call = make_fake_response(
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "echo", "arguments": '{"text": "x"}'},
                }
            ]
        )
        llm.chat.return_value = tool_call
        agent = Agent(llm=llm, tools=[tool], max_iterations=2)
        chunks = list(agent.chat_stream("loop"))
        assert "最大迭代次数" in chunks[0]


class TestAgentReset:
    def test_reset_clears_history_except_system(self) -> None:
        llm = MagicMock()
        llm.chat.return_value = make_fake_response("ok")
        agent = Agent(llm=llm)
        agent.chat("hi")
        assert len(agent.messages) == 3
        agent.reset()
        assert len(agent.messages) == 1
        assert agent.messages[0].role == "system"
