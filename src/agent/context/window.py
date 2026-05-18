"""Context Window Management - 上下文窗口管理。

管理 LLM 的上下文窗口，按 token 预算分配各类型上下文的配额，
监控上下文使用情况，在接近限制时触发压缩。
"""

from __future__ import annotations

import logging
from typing import Any

from src.llm import TokenCounter

from .types import ContextBudget, ContextSegment, ContextType, TokenUsage

logger = logging.getLogger(__name__)


class ContextWindowManager:
    """上下文窗口管理器。

    职责:
    - 跟踪 token 使用情况
    - 检查是否接近上下文限制
    - 触发压缩信号
    - 管理 buffer 区域

    Args:
        budget: Token 预算配置
        token_counter: Token 计数器
        overflow_threshold: 触发压缩的阈值比例 (0-1)
    """

    def __init__(
        self,
        budget: ContextBudget | None = None,
        token_counter: TokenCounter | None = None,
        overflow_threshold: float = 0.85,
    ) -> None:
        self.budget = budget or ContextBudget()
        self.token_counter = token_counter or TokenCounter()
        self.overflow_threshold = overflow_threshold

        self.current_usage = TokenUsage()
        self._overflow_count: int = 0
        self._compression_count: int = 0

    def count_tokens(self, text: str) -> int:
        return self.token_counter.count(text)

    def update_usage(self, segment: ContextSegment) -> None:
        """更新某片段的使用统计。"""
        if segment.token_count == 0:
            segment.token_count = self.count_tokens(segment.content)
        self.current_usage.total += segment.token_count
        current = self.current_usage.by_type.get(segment.type, 0)
        self.current_usage.by_type[segment.type] = current + segment.token_count

    def check_overflow(self) -> bool:
        """检测是否接近上下文溢出。"""
        ratio = self.current_usage.total / self.budget.total_max
        if ratio >= self.overflow_threshold:
            self._overflow_count += 1
            return True
        return False

    def get_available(self) -> int:
        """返回当前可用 token 数。"""
        return self.budget.total_max - self.current_usage.total

    def get_usage_report(self) -> str:
        """生成 token 使用报告。"""
        lines = [f"Token 使用: {self.current_usage.total}/{self.budget.total_max}"]
        for type_, count in sorted(
            self.current_usage.by_type.items(), key=lambda x: -x[1]
        ):
            budget = self.budget.get(type_)
            pct = (count / budget * 100) if budget else 0
            bar = "#" * int(pct / 10) + "." * (10 - int(pct / 10))
            lines.append(f"  {type_.value:12s} {count:6d}/{budget:6d} {bar} {pct:.0f}%")
        lines.append(f"  压缩次数: {self._compression_count}")
        lines.append(f"  溢出次数: {self._overflow_count}")
        return "\n".join(lines)

    def record_compression(self, saved: int) -> None:
        """记录一次压缩操作。"""
        self._compression_count += 1
        self.current_usage.compression_saved += saved
        self.current_usage.total -= saved

    def select_for_compression(
        self, segments: list[ContextSegment], target_reduction: int
    ) -> list[ContextSegment]:
        """选择需要压缩的上下文片段（低优先级优先）。"""
        candidates = sorted(
            [s for s in segments if s.type != ContextType.SYSTEM],
            key=lambda s: (s.priority, -s.token_count),
        )
        selected: list[ContextSegment] = []
        reduction = 0
        for seg in candidates:
            if reduction >= target_reduction:
                break
            if seg.token_count < 50:
                continue
            selected.append(seg)
            reduction += seg.token_count
        return selected

    def should_compress(self, segments: list[ContextSegment]) -> bool:
        """判断是否需要压缩。"""
        if self.check_overflow():
            return True
        working_tokens = self.current_usage.by_type.get(ContextType.WORKING, 0)
        if working_tokens > self.budget.reserved_working * 0.9:
            return True
        return False
