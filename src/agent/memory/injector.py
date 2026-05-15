"""Prompt 注入策略。

将检索到的记忆注入到 LLM 的 system prompt 中，
以结构化的方式呈现在上下文中。
"""

import logging

from src.llm import TokenCounter

from .types import MemoryItem

logger = logging.getLogger(__name__)


class PromptInjector:
    """Prompt 注入器。

    将检索到的记忆格式化为结构化的 memory context，
    并注入到 system prompt 中。管理 token 预算，
    确保不超出上下文窗口限制。
    """

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self.token_counter = token_counter or TokenCounter()

    def inject_memory(
        self,
        system_prompt: str,
        memories: list[MemoryItem],
        max_tokens: int = 1024,
    ) -> str:
        """将记忆注入到 system prompt。

        Args:
            system_prompt: 原始 system prompt
            memories: 检索到的记忆列表
            max_tokens: 记忆上下文的最大 token 数

        Returns:
            注入了记忆的 system prompt
        """
        if not memories:
            return system_prompt

        memory_lines = []
        budget = max_tokens

        for item in sorted(memories, key=lambda x: x.importance, reverse=True):
            line = self._format_memory(item)
            line_tokens = self.token_counter.count(line) + 5
            if line_tokens > budget:
                break
            memory_lines.append(line)
            budget -= line_tokens

        if not memory_lines:
            return system_prompt

        memory_block = "\n".join(memory_lines)
        return f"{system_prompt}\n\n=== 记忆上下文 ===\n{memory_block}"

    def _format_memory(self, item: MemoryItem) -> str:
        """格式化单条记忆为一行。"""
        return f"[{item.type}] {item.content} (重要度: {item.importance:.1f})"
