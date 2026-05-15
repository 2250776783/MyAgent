"""工作记忆 - 短期滑动窗口。

管理当前会话的消息列表，按 token 预算自动裁剪窗口。
是 Agent 的"工作台"，位于 LLM 上下文的最前沿。
"""

import logging
from collections.abc import Sequence

from src.llm import Message, TokenCounter

logger = logging.getLogger(__name__)


class WorkingMemory:
    """工作记忆 - 基于 token 预算的消息窗口。

    维护 Agent 的短期工作记忆：
    - 滑动窗口保留最近的消息
    - 按 token 预算淘汰旧消息
    - 保留 reserve_tokens 给 system prompt 和检索注入

    Args:
        max_tokens: 工作记忆最大 token 数
        reserve_tokens: 为 system prompt + 检索保留的 token 数
        token_counter: TokenCounter 实例
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        reserve_tokens: int = 1024,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.token_counter = token_counter or TokenCounter()

    @property
    def budget(self) -> int:
        """实际可用 token 预算。"""
        return self.max_tokens - self.reserve_tokens

    def trim(self, messages: list[Message]) -> list[Message]:
        """裁剪消息列表到 token 预算内。

        保留 system prompt（索引 0），从后往前贪心选择消息，
        确保至少保留最后 1 条 user 消息。
        """
        if not messages:
            return messages

        keep_system = messages[:1]
        candidates = messages[1:]

        if self._count_tokens(messages) <= self.max_tokens:
            return messages

        selected: list[Message] = []
        used = 0

        for msg in reversed(candidates):
            tokens = self._count_tokens([msg])

            if used + tokens > self.budget and len(selected) > 0:
                if not any(m.role == "user" for m in selected):
                    selected.insert(0, msg)
                    used += tokens
                break

            selected.insert(0, msg)
            used += tokens

        if not any(m.role == "user" for m in selected):
            last_user = next((m for m in reversed(candidates) if m.role == "user"), None)
            if last_user and last_user not in selected:
                selected.insert(0, last_user)

        return keep_system + selected

    def _count_tokens(self, messages: list[Message]) -> int:
        total = 0
        for msg in messages:
            total += self.token_counter.count(msg.content or "")
            total += self.token_counter.count(msg.role or "")
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += self.token_counter.count(str(tc))
        return total

    def reset(self) -> None:
        """重置工作记忆（清空状态）。"""
        pass
