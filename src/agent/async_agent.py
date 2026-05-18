"""异步 Agent 主类。

与同步 Agent 功能完全一致的异步版本，使用 AsyncLLMClient 驱动 ReAct 循环。
ContextManager/MemoryManager 通过 AsyncLLMClient.sync 获取同步 LLM 引用。

设计目标：
- 不修改任何现有同步代码
- Tool 执行通过 run_in_executor 避免阻塞事件循环
- 使用 ToolExecutor（同步 Agent 中绕过的执行器层）
"""

import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from src.agent.agent import _is_react_response, _parse_react_action, _parse_tool_call
from src.agent.context import ContextManager
from src.agent.memory import MemoryManager
from src.agent.tools.base import BaseTool, ToolRegistry
from src.agent.tools.runtime import ToolExecutor
from src.llm import AsyncLLMClient, Message

logger = logging.getLogger(__name__)

@dataclass
class StreamEvent:
    """结构化流式事件，用于 WebSocket/SSE 传输。

    Attributes:
        type: 事件类型 (token/tool_call/tool_result/error/done)
        data: 事件数据字典
    """
    type: str
    data: dict = field(default_factory=dict)


_SYSTEM_PROMPT = (
    "你是一个智能助手，可以使用工具来获取信息或执行操作。"
    "如果工具返回了结果，根据结果回答用户的问题。"
    "如果不需要使用工具，直接回答即可。"
)


class AsyncAgent:
    """异步 ReAct 智能体。

    用法::

        llm = AsyncLLMClient()
        agent = AsyncAgent(llm=llm, tools=[...])
        result = await agent.chat("你好")
        # 或流式
        async for chunk in agent.chat_stream("你好"):
            ...

    Args:
        llm: 异步 LLM 客户端
        tools: 可选工具列表
        system_prompt: 系统提示词
        max_iterations: 最大循环次数
        memory: 可选记忆系统（传给 ContextManager）
        context_manager: 可选上下文管理器（优先级高于 memory）
    """

    def __init__(
        self,
        llm: AsyncLLMClient,
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

        # ContextManager/MemoryManager 接收同步 LLM 引用
        self.context = context_manager or ContextManager(llm=llm.sync, memory=memory)
        self.context.start_session()

        # 使用 ToolExecutor（修复同步 Agent 绕过执行器的问题）
        self._executor = ToolExecutor(timeout=30.0, max_retries=0)

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    async def chat(self, message: str) -> str:
        """异步处理用户消息，返回回答。"""
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
            response = await self.llm.async_chat(
                self.messages,
                tools=self.tool_registry.to_openai_tools() or None,
                temperature=0.7,
            )

            if response.tool_calls:
                await self._handle_tool_calls(response)
            elif _is_react_response(response.content):
                action = _parse_react_action(response.content)
                if action and action.startswith("Finish"):
                    self.messages.append(response)
                    self.messages.append(Message(role="tool", content="[已完成]"))
                    import re
                    m = re.search(r"Finish\[(.*)\]$", action)
                    result = m.group(1) if m else action
                    self.context.on_chat_end(self.messages)
                    return result
                await self._handle_react(response)
            else:
                self.messages.append(response)
                self.context.on_chat_end(self.messages)
                return response.content

        self.context.on_chat_end(self.messages)
        return "已达最大迭代次数，请简化问题或重试。"

    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """异步流式处理用户消息，逐块返回文本。"""
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
            response = await self.llm.async_chat(
                self.messages,
                tools=tools_list,
                temperature=0.7,
            )

            if response.tool_calls:
                await self._handle_tool_calls(response)
            elif _is_react_response(response.content):
                action = _parse_react_action(response.content)
                if action and action.startswith("Finish"):
                    self.messages.append(response)
                    self.messages.append(Message(role="tool", content="[已完成]"))
                    import re
                    m = re.search(r"Finish\[(.*)\]$", action)
                    result = m.group(1) if m else action
                    self.context.on_chat_end(self.messages)
                    yield result
                    return
                await self._handle_react(response)
            else:
                self.messages.append(response)
                self.context.on_chat_end(self.messages)
                yield response.content
                return

        yield "已达最大迭代次数，请简化问题或重试。"

    async def chat_stream_events(self, message: str) -> AsyncGenerator[StreamEvent, None]:
        """产出结构化流式事件（用于 WebSocket 中继）。

        事件类型:
        - token:      {"text": "..."} — 文本块
        - tool_call:  {"id": "...", "name": "...", "args": "..."} — 工具调用
        - tool_result:{"name": "...", "output": "..."} — 工具结果
        - error:      {"message": "..."} — 错误
        - done:       {"session_id": "..."} — 完成
        """
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
            response = await self.llm.async_chat(
                self.messages,
                tools=tools_list,
                temperature=0.7,
            )

            if response.tool_calls:
                self.messages.append(response)
                for tc in response.tool_calls:
                    tool_name = tc["function"]["name"]
                    yield StreamEvent("tool_call", {
                        "id": tc["id"],
                        "name": tool_name,
                        "args": tc["function"]["arguments"],
                    })

                    args = json.loads(tc["function"]["arguments"])
                    call_id = self.context.on_tool_call(tool_name, args)
                    result = await self._execute_tool_call(tc)
                    success = not result.startswith("工具执行错误")
                    self.context.on_tool_result(call_id, result, success, 0.0)

                    yield StreamEvent("tool_result", {
                        "name": tool_name,
                        "output": str(result),
                    })

                    self.messages.append(
                        Message(role="tool", content=str(result), tool_call_id=tc["id"])
                    )

            elif _is_react_response(response.content):
                action = _parse_react_action(response.content)
                if action and action.startswith("Finish"):
                    self.messages.append(response)
                    self.messages.append(Message(role="tool", content="[已完成]"))
                    m = re.search(r"Finish\[(.*)\]$", action)
                    result = m.group(1) if m else action
                    self.context.on_chat_end(self.messages)
                    yield StreamEvent("token", {"text": result})
                    yield StreamEvent("done", {"session_id": self.context.session_id})
                    return

                self.messages.append(response)
                action = _parse_react_action(response.content)
                if action:
                    tool_name, tool_input = _parse_tool_call(action)
                    if tool_name:
                        yield StreamEvent("tool_call", {
                            "id": "", "name": tool_name, "args": tool_input or "",
                        })
                        call_id = self.context.on_tool_call(tool_name, {"input": tool_input})
                        result = await self._execute_tool_by_name(tool_name, tool_input or "")
                        success = not result.startswith("工具执行错误")
                        self.context.on_tool_result(call_id, result, success, 0.0)
                        yield StreamEvent("tool_result", {
                            "name": tool_name, "output": str(result),
                        })
                        self.messages.append(Message(role="tool", content=str(result)))
            else:
                self.messages.append(response)
                self.context.on_chat_end(self.messages)
                content = response.content
                if content:
                    yield StreamEvent("token", {"text": content})
                yield StreamEvent("done", {"session_id": self.context.session_id})
                return

        yield StreamEvent("error", {"message": "已达最大迭代次数，请简化问题或重试。"})

    def reset(self) -> None:
        """重置对话历史（保留 system prompt）。"""
        self.context.on_reset()
        self.messages = [Message(role="system", content=self._base_system_prompt)]

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _handle_tool_calls(self, response: Message) -> None:
        """异步处理 function calling 工具调用。"""
        self.messages.append(response)
        for tc in response.tool_calls:
            tool_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            call_id = self.context.on_tool_call(tool_name, args)

            result = await self._execute_tool_call(tc)
            success = not result.startswith("工具执行错误")
            self.context.on_tool_result(call_id, result, success, 0.0)

            self.messages.append(
                Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tc["id"],
                )
            )

    async def _handle_react(self, response: Message) -> None:
        """异步处理文本 ReAct 格式的响应。"""
        self.messages.append(response)
        action = _parse_react_action(response.content)
        if not action:
            return

        tool_name, tool_input = _parse_tool_call(action)
        if not tool_name:
            return

        call_id = self.context.on_tool_call(tool_name, {"input": tool_input})
        result = await self._execute_tool_by_name(tool_name, tool_input)
        success = not result.startswith("工具执行错误")
        self.context.on_tool_result(call_id, result, success, 0.0)

        self.messages.append(Message(role="tool", content=str(result)))

    async def _execute_tool_call(self, tc: dict[str, Any]) -> str:
        """通过 ToolExecutor 异步执行 function calling 格式的工具调用。"""
        try:
            tool = self.tool_registry.get(tc["function"]["name"])
            args = json.loads(tc["function"]["arguments"])
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, lambda: self._executor.execute(tool, **args)
            )
            return str(result)
        except Exception as e:
            return f"工具执行错误: {e}"

    async def _execute_tool_by_name(self, name: str, input_text: str) -> str:
        """通过 ToolExecutor 异步执行文本 ReAct 格式的工具调用。"""
        try:
            tool = self.tool_registry.get(name)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, lambda: self._executor.execute(tool, query=input_text)
            )
            return str(result)
        except Exception as e:
            return f"工具执行错误: {e}"
