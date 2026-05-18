"""Agent 主类。

统一的 ReAct 智能体，双模式运行：
1. Function calling 模式（默认）：LLM 返回 tool_calls 时执行工具
2. 文本 ReAct 模式（回退）：LLM 返回 Thought/Action 文本时解析并执行工具
"""

import json
import logging
import re
from collections.abc import Generator
from typing import Any

from src.agent.context import ContextManager
from src.agent.memory import MemoryManager
from src.agent.tools.base import BaseTool, ToolRegistry
from src.llm import LLMClient, Message

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "你是一个智能助手，可以使用工具来获取信息或执行操作。"
    "如果工具返回了结果，根据结果回答用户的问题。"
    "如果不需要使用工具，直接回答即可。"
)


class Agent:
    """统一的 ReAct 智能体主类。

    双模式运行：
    - 优先使用 function calling（LLM 返回 tool_calls）
    - 回退到文本 ReAct 格式（Thought → Action: ToolName[input] → Observation）

    Args:
        llm: LLM 客户端
        tools: 可选工具列表
        system_prompt: 系统提示词
        max_iterations: 最大循环次数
        memory: 可选记忆系统（传给 ContextManager）
        context_manager: 可选上下文管理器（优先级高于 memory）
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: list[BaseTool] | None = None,
        system_prompt: str = _SYSTEM_PROMPT,
        max_iterations: int = 10,
        memory: MemoryManager | None = None,
        context_manager: ContextManager | None = None,
    ) -> None:
        self.llm = llm
        self.max_iterations = max_iterations
        self.memory = memory
        self._base_system_prompt = system_prompt
        self.messages: list[Message] = [Message(role="system", content=system_prompt)]
        self.tool_registry = ToolRegistry()
        if tools:
            for tool in tools:
                self.tool_registry.register(tool)

        self.context = context_manager or ContextManager(llm=llm, memory=memory)
        self.context.start_session()

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def chat(self, message: str) -> str:
        """处理用户消息，返回回答。

        内部 ReAct 循环：function calling 优先，文本 ReAct 回退。
        """
        # 上下文系统：记忆检索 + 系统提示增强
        self.context.on_chat_start(message)
        augmentation = self.context.build_system_augmentation(message)
        if augmentation:
            self.messages[0] = Message(
                role="system",
                content=f"{self._base_system_prompt}\n\n{augmentation}",
            )

        trimmed = self.context.trim_messages(self.messages)
        if trimmed is not self.messages:
            self.messages = trimmed

        self.messages.append(Message(role="user", content=message))

        for _ in range(self.max_iterations):
            response = self.llm.chat(
                self.messages,
                tools=self.tool_registry.to_openai_tools() or None,
                temperature=0.7,
            )

            if response.tool_calls:
                self._handle_tool_calls(response)
            elif _is_react_response(response.content):
                action = _parse_react_action(response.content)
                if action and action.startswith("Finish"):
                    self.messages.append(response)
                    self.messages.append(Message(role="tool", content="[已完成]"))
                    m = re.search(r"Finish\[(.*)\]$", action)
                    result = m.group(1) if m else action
                    self.context.on_chat_end(self.messages)
                    return result
                self._handle_react(response)
            else:
                self.messages.append(response)
                self.context.on_chat_end(self.messages)
                return response.content

        self.context.on_chat_end(self.messages)
        return "已达最大迭代次数，请简化问题或重试。"

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """流式处理用户消息，逐块返回文本。"""
        # 上下文系统：记忆检索 + 系统提示增强
        self.context.on_chat_start(message)
        augmentation = self.context.build_system_augmentation(message)
        if augmentation:
            self.messages[0] = Message(
                role="system",
                content=f"{self._base_system_prompt}\n\n{augmentation}",
            )

        trimmed = self.context.trim_messages(self.messages)
        if trimmed is not self.messages:
            self.messages = trimmed

        self.messages.append(Message(role="user", content=message))
        tools_list = self.tool_registry.to_openai_tools() or None

        for _ in range(self.max_iterations):
            response = self.llm.chat(
                self.messages,
                tools=tools_list,
                temperature=0.7,
            )

            if response.tool_calls:
                self._handle_tool_calls(response)
            elif _is_react_response(response.content):
                action = _parse_react_action(response.content)
                if action and action.startswith("Finish"):
                    self.messages.append(response)
                    self.messages.append(Message(role="tool", content="[已完成]"))
                    m = re.search(r"Finish\[(.*)\]$", action)
                    result = m.group(1) if m else action
                    self.context.on_chat_end(self.messages)
                    yield result
                    return
                self._handle_react(response)
            else:
                self.messages.append(response)
                self.context.on_chat_end(self.messages)
                yield response.content
                return

        yield "已达最大迭代次数，请简化问题或重试。"

    def reset(self) -> None:
        """重置对话历史（保留 system prompt）。"""
        self.context.on_reset()
        self.messages = [Message(role="system", content=self._base_system_prompt)]

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _handle_tool_calls(self, response: Message) -> None:
        """处理 function calling 工具调用。"""
        self.messages.append(response)
        for tc in response.tool_calls:
            tool_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            call_id = self.context.on_tool_call(tool_name, args)

            result = self._execute_tool_call(tc)
            success = not result.startswith("工具执行错误")
            self.context.on_tool_result(call_id, result, success, 0.0)

            self.messages.append(
                Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tc["id"],
                )
            )

    def _handle_react(self, response: Message) -> None:
        """处理文本 ReAct 格式的响应。"""
        self.messages.append(response)
        action = _parse_react_action(response.content)
        if not action:
            return

        tool_name, tool_input = _parse_tool_call(action)
        if not tool_name:
            return

        call_id = self.context.on_tool_call(tool_name, {"input": tool_input})
        result = self._execute_tool_by_name(tool_name, tool_input)
        success = not result.startswith("工具执行错误")
        self.context.on_tool_result(call_id, result, success, 0.0)

        self.messages.append(
            Message(role="tool", content=str(result))
        )

    def _execute_tool_call(self, tc: dict[str, Any]) -> str:
        """执行 function calling 格式的工具调用。"""
        try:
            tool = self.tool_registry.get(tc["function"]["name"])
            args = json.loads(tc["function"]["arguments"])
            return str(tool.run(**args))
        except Exception as e:
            return f"工具执行错误: {e}"

    def _execute_tool_by_name(self, name: str, input_text: str) -> str:
        """执行文本 ReAct 格式的工具调用。"""
        try:
            tool = self.tool_registry.get(name)
            return str(tool.run(query=input_text))
        except Exception as e:
            return f"工具执行错误: {e}"


# ------------------------------------------------------------------
# 模块级辅助函数
# ------------------------------------------------------------------

def _is_react_response(text: str) -> bool:
    """判断是否为文本 ReAct 格式（包含 Thought 和 Action）。"""
    return bool(re.search(r"Thought:", text)) and bool(re.search(r"Action:", text))


def _parse_react_action(text: str) -> str | None:
    """从文本 ReAct 响应中提取 Action 内容。"""
    m = re.search(r"Action:\s*(.*)", text, re.DOTALL)
    return m.group(1).strip() if m else None


def _parse_tool_call(action: str) -> tuple[str | None, str | None]:
    """解析 Action 文本中的工具调用，格式: ToolName[input]。"""
    m = re.match(r"(\w+)\[(.*)\]", action, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return None, None
