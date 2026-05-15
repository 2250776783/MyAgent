"""记忆摘要模块。

将多条原始记忆压缩为一条摘要记忆，或将会话消息压缩为摘要。
"""

import logging

from src.llm import LLMClient, Message

from .types import MemoryItem

logger = logging.getLogger(__name__)


class MemorySummarizer:
    """记忆摘要器。

    使用 LLM 将多条相关记忆压缩为一段连贯的摘要，
    或者将会话消息流压缩为会话摘要。
    """

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def summarize_memories(self, memories: list[MemoryItem], max_chars: int = 300) -> str:
        """将多条记忆压缩为摘要。

        Args:
            memories: 待摘要的记忆列表
            max_chars: 摘要最大字符数

        Returns:
            摘要文本
        """
        if not memories:
            return ""

        total_chars = sum(len(m.content) for m in memories)
        if total_chars <= max_chars:
            return " | ".join(m.content for m in memories)

        prompt = (
            f"请将以下 {len(memories)} 条相关记忆压缩为一段连贯的摘要"
            f"（不超过 {max_chars} 字），保持关键信息：\n\n"
            + "\n---\n".join(f"[{m.type}] {m.content}" for m in memories)
        )

        response = self.llm.chat([Message(role="user", content=prompt)])
        return response.content

    def summarize_messages(self, messages: list[Message]) -> str:
        """将消息列表摘要为一段文字。

        Args:
            messages: 消息列表

        Returns:
            摘要文本
        """
        if not messages:
            return ""

        if len(messages) <= 6:
            first = next((m.content for m in messages if m.role == "user"), "")
            return f"简短对话: {first[:100]}"

        text = self._format_messages(messages)
        prompt = (
            "请总结以下对话的核心内容、用户需求和关键决策，不超过 150 字：\n\n"
            f"{text}"
        )

        response = self.llm.chat([Message(role="user", content=prompt)])
        return response.content

    def _format_messages(self, messages: list[Message]) -> str:
        lines = []
        for m in messages:
            role = {"user": "用户", "assistant": "助手", "tool": "工具"}.get(m.role, m.role)
            content = m.content[:200] if m.content else ""
            if m.tool_calls:
                tools = [tc["function"]["name"] for tc in m.tool_calls]
                content = f"[调用工具: {', '.join(tools)}]"
            lines.append(f"{role}: {content}")
        return "\n".join(lines[-20:])
