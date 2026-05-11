"""Agent 主类。

实现简单的 ReAct 循环：LLM 思考 → 工具执行 → 观察结果 → 继续/结束。
"""

import json
import logging
from collections.abc import Generator
from typing import Any

from src.agent.tools.base import BaseTool, ToolRegistry
from src.llm import LLMClient, Message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个智能助手，可以使用工具来获取信息或执行操作。"
    "如果工具返回了结果，根据结果回答用户的问题。"
    "如果不需要使用工具，直接回答即可。"
)


class Agent:
    """Agent 主类。

    集成 LLM + 工具，通过 ReAct 循环处理用户请求。

    Args:
        llm: LLM 客户端
        tools: 可选，工具列表
        system_prompt: 系统提示词
        max_iterations: 最大思考-行动循环次数
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: list[BaseTool] | None = None,
        system_prompt: str = SYSTEM_PROMPT,
        max_iterations: int = 10,
    ) -> None:
        self.llm = llm
        self.max_iterations = max_iterations
        self.messages: list[Message] = [Message(role="system", content=system_prompt)]

        self.tool_registry = ToolRegistry()
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)

    def chat(self, message: str) -> str:
        """处理用户消息并返回回答。

        内部循环：调用 LLM → 若返回工具调用则执行 → 继续循环。
        """
        self.messages.append(Message(role="user", content=message))

        for _ in range(self.max_iterations):
            response = self.llm.chat(
                self.messages,
                tools=self.tool_registry.to_openai_tools() or None,
                temperature=0.7,
            )

            if response.tool_calls:
                self.messages.append(response)
                for tc in response.tool_calls:
                    result = self._execute_tool(tc)
                    self.messages.append(
                        Message(
                            role="tool",
                            content=str(result),
                            tool_call_id=tc["id"],
                        )
                    )
            else:
                self.messages.append(response)
                return response.content

        return "已达最大迭代次数，请简化问题或重试。"

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """流式处理用户消息，逐块返回文本。"""
        self.messages.append(Message(role="user", content=message))
        tools_list = self.tool_registry.to_openai_tools() or None

        for _ in range(self.max_iterations):
            response = self.llm.chat(
                self.messages,
                tools=tools_list,
                temperature=0.7,
            )

            if response.tool_calls:
                self.messages.append(response)
                for tc in response.tool_calls:
                    result = self._execute_tool(tc)
                    self.messages.append(
                        Message(
                            role="tool",
                            content=str(result),
                            tool_call_id=tc["id"],
                        )
                    )
            else:
                self.messages.append(response)
                yield response.content
                return

        yield "已达最大迭代次数，请简化问题或重试。"

    def reset(self) -> None:
        """重置对话历史（保留 system prompt）。"""
        self.messages = [self.messages[0]]

    def _execute_tool(self, tc: dict[str, Any]) -> str:
        """执行单个工具调用并返回结果字符串。"""
        try:
            tool = self.tool_registry.get(tc["function"]["name"])
            args = json.loads(tc["function"]["arguments"])
            return tool.run(**args)
        except Exception as e:
            return f"工具执行错误: {e}"
