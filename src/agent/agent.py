"""Agent 主类。

实现简单的 ReAct 循环：LLM 思考 → 工具执行 → 观察结果 → 继续/结束。
"""

import json
import logging
from collections.abc import Generator
from typing import Any
import re

from src.agent.tools.base import BaseTool, ToolRegistry
from src.llm import LLMClient, Message
from src.agent.tools import ToolExecutor

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个智能助手，可以使用工具来获取信息或执行操作。"
    "如果工具返回了结果，根据结果回答用户的问题。"
    "如果不需要使用工具，直接回答即可。"
)

REACT_PROMPT_TEMPLATE = """
请注意。你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 这是你的思考过程，用于分析问题、拆解任务和规划下一步行动。

Action: 你决定财务的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`: 调用工具，tool_name 是工具名称，tool_input 是传递给工具的输入。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action: 字段后面使用 Finish[你的最终答案] 来输出最终答案

现在，请开始解决问题：
Question: {question}
History: {history}
"""

class ReActAgent:
    def __init__(self, llm_client: LLMClient, tool_executor: ToolExecutor, max_iterations: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
        self.history = []

    def _parse_output(self, text: str):
        """
        解析LLM的输出，提取Thought和Action
        """
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*)", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action
    
    def _parse_action(self, action_text: str):
        """
        解析Action文本，提取工具名称和输入
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def run(self, question: str):
        """
        运行ReAct智能体来回答一个问题
        """

        self.history = [] # 重置历史记录
        current_iteration = 0

        while(current_iteration < self.max_iterations):
            current_iteration += 1
            print(f"\n--- 第 {current_iteration} 轮迭代---")

            # 1. 格式化提示词
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # 2. 调用LLM获取思考和行动
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.think(messages=messages)

            if not response:
                print("LLM未返回内容，结束循环。")
                break

            # ... 后续的解析、执行、整合步骤
            # 3. 解析LLM的输出
            thought, action = self._parse_output(response)

            if thought:
                print(f"LLM的思考 (Thought): {thought}")

            if not action:
                print("警告：未能解析处有效的Action，流程终止。")
                break

            # 4. 执行Action
            if action.startswith("Finish["):
                final_answer = re.match(r"Finish\[(.*)\]", action).group(1)
                print(f"最终答案: {final_answer}")
                return final_answer
            
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                # ... 处理无效Action格式 ...
                print("警告：Action格式不正确，无法解析工具调用，流程终止。")
                continue

            print(f"LLM决定调用工具: {tool_name}，输入: {tool_input}")

            tool_func = self.tool_executor.getTool(tool_name)
            if not tool_func:
                observation = f"错误: 未找到名为 '{tool_name}' 的工具。"
            else:
                observation = tool_func(tool_input)

            print(f"工具执行结果 (Observation): {observation}")

            # 5. 将本轮的 Action 和 Observation 添加到历史记录中，供下一轮思考使用
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        # 循环结束
        print("已达最大迭代次数, 流程终止。")
        return None



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
            result = tool.run(**args)
            return str(result)
        except Exception as e:
            return f"工具执行错误: {e}"
