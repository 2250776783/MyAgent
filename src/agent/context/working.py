"""Working Context - 工作记忆上下文。

管理当前轮次的对话上下文，格式化消息历史为上下文片段。
"""

from __future__ import annotations

from src.llm import Message, TokenCounter

from .types import ContextSegment, ContextType, InjectionPhase


class WorkingContext:
    """工作记忆上下文。

    Args:
        token_counter: Token 计数器
    """

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self.token_counter = token_counter or TokenCounter()

    def build(self, messages: list[Message], max_tokens: int = 8192) -> ContextSegment:
        text = self._format(messages, max_tokens)
        seg = ContextSegment.create(
            ContextType.WORKING, text,
            priority=0.8, phase=InjectionPhase.WORKING,
        )
        seg.token_count = self.token_counter.count(text)
        return seg

    def _format(self, messages: list[Message], max_tokens: int) -> str:
        parts = []
        used = 0
        for msg in reversed(messages):
            if msg.role == "system":
                continue
            line = self._format_message(msg)
            tokens = self.token_counter.count(line) + 10
            if used + tokens > max_tokens and parts:
                parts.insert(0, f"...(前文共 {used} tokens 已折叠)")
                break
            parts.insert(0, line)
            used += tokens
        return "\n".join(parts)

    def _format_message(self, msg: Message) -> str:
        if msg.role == "user":
            return f"用户: {msg.content}"
        elif msg.role == "assistant":
            text = f"助手: {msg.content}" if msg.content else ""
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn = tc.get("function", {})
                    text += f"\n[调用工具 {fn.get('name', '')}]"
            return text
        elif msg.role == "tool":
            content = msg.content[:300] if msg.content else ""
            return f"[工具结果: {content}]"
        return msg.content or ""
