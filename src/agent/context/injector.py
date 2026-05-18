"""Dynamic Context Injection - 动态上下文注入器。

支持注意力引导、上下文切换、焦点强化、反重复推理。
"""

from __future__ import annotations

from src.llm import TokenCounter

from .types import ContextSegment, ContextType, InjectionPhase


class DynamicInjector:
    """动态上下文注入器。"""

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self.token_counter = token_counter or TokenCounter()
        self._injection_count: int = 0

    def build_attention_guide(
        self,
        active_goal: str = "",
        current_task: str = "",
        warnings: list[str] | None = None,
    ) -> ContextSegment | None:
        parts = []
        if active_goal:
            parts.append(f"请专注于当前目标: {active_goal[:100]}")
        if current_task:
            parts.append(f"当前步骤: {current_task[:100]}")
        if warnings:
            for w in warnings:
                parts.append(f"[注意] {w}")
        if not parts:
            return None
        text = "\n".join(parts)
        seg = ContextSegment.create(
            ContextType.SYSTEM, text,
            priority=0.95, phase=InjectionPhase.SYSTEM,
            metadata={"type": "attention_guide"},
        )
        seg.token_count = self.token_counter.count(text)
        self._injection_count += 1
        return seg

    def build_context_switch(self, from_goal: str, to_goal: str) -> ContextSegment:
        text = (
            f"[上下文切换] 目标已从「{from_goal[:50]}」切换为「{to_goal[:50]}」。"
            f"请重置注意力，专注于新目标。"
        )
        seg = ContextSegment.create(
            ContextType.SYSTEM, text,
            priority=0.9, phase=InjectionPhase.SYSTEM,
            metadata={"type": "context_switch"},
        )
        seg.token_count = self.token_counter.count(text)
        return seg

    def build_focus_reinforcement(self, goal_description: str) -> ContextSegment:
        text = (
            f"回顾目标: {goal_description[:100]}\n"
            f"请确保当前操作与上述目标一致。如果已经偏离，请重新规划。"
        )
        seg = ContextSegment.create(
            ContextType.REFLECTION, text,
            priority=0.85, phase=InjectionPhase.REFLECTION,
            metadata={"type": "focus_reinforcement"},
        )
        seg.token_count = self.token_counter.count(text)
        return seg

    def build_anti_repetition(self, repeat_count: int) -> ContextSegment | None:
        if repeat_count < 2:
            return None
        text = (
            f"[注意] 检测到重复推理（{repeat_count} 次）。"
            f"如果当前方法无效，请尝试完全不同的策略。"
        )
        seg = ContextSegment.create(
            ContextType.REFLECTION, text,
            priority=0.7, phase=InjectionPhase.REFLECTION,
            metadata={"type": "anti_repetition"},
        )
        seg.token_count = self.token_counter.count(text)
        return seg
