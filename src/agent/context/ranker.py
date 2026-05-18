"""Context Ranking - 上下文排名引擎。

基于多维度评分对上下文片段进行排序和选择：
- 优先级（priority）
- 时效性（recency）
- 相关性（relevance to current goal）
- 历史效用（historical usefulness）
"""

from __future__ import annotations

import math
import time
from typing import Any

from .types import ContextSegment, ContextType


class ContextRanker:
    """上下文排名器。

    对 ContextSegment 列表进行多维度评分和排序，
    选出最相关的片段注入 prompt。

    Scoring 权重:
    - priority_weight: 显式优先级 (0.3)
    - recency_weight: 时间衰减 (0.2)
    - type_boost: 类型偏置 (0.2)
    - diversity_penalty: 多样性惩罚 (0.15)
    - novelty_bonus: 新鲜度奖励 (0.15)
    """

    def __init__(
        self,
        priority_weight: float = 0.30,
        recency_weight: float = 0.20,
        type_boost: float = 0.20,
        diversity_penalty: float = 0.15,
        novelty_bonus: float = 0.15,
    ) -> None:
        self.priority_weight = priority_weight
        self.recency_weight = recency_weight
        self.type_boost = type_boost
        self.diversity_penalty = diversity_penalty
        self.novelty_bonus = novelty_bonus

        self._type_boost_map: dict[ContextType, float] = {
            ContextType.GOAL: 0.3,
            ContextType.TASK: 0.2,
            ContextType.PLAN: 0.2,
            ContextType.TOOL_OUTPUT: 0.1,
            ContextType.REFLECTION: 0.1,
            ContextType.MEMORY: 0.05,
            ContextType.ENVIRONMENT: 0.0,
            ContextType.WORKING: -0.1,
            ContextType.TOOL: -0.2,
        }

    def rank(
        self,
        segments: list[ContextSegment],
        current_goal: str = "",
        seen_ids: set[str] | None = None,
    ) -> list[ContextSegment]:
        """对上下文片段排序，返回按分数降序的列表。"""
        if not segments:
            return []

        seen = seen_ids or set()
        now = time.time()

        scored: list[tuple[ContextSegment, float]] = []
        for seg in segments:
            if seg.id in seen:
                continue
            score = self._score(seg, now, current_goal)
            scored.append((seg, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [seg for seg, _ in scored]

    def select_top_k(
        self,
        segments: list[ContextSegment],
        k: int,
        current_goal: str = "",
        min_score: float = 0.1,
    ) -> list[ContextSegment]:
        """选择 top-K 片段，同时保证多样性。"""
        ranked = self.rank(segments, current_goal)
        selected: list[ContextSegment] = []
        seen_types: set[ContextType] = set()

        for seg in ranked:
            if len(selected) >= k:
                break
            if seg.type == ContextType.SYSTEM:
                selected.append(seg)
                continue
            score = self._score(seg, time.time(), current_goal)
            if score < min_score and seg.type not in (
                ContextType.GOAL, ContextType.TASK
            ):
                continue

            selected.append(seg)
            seen_types.add(seg.type)

        return selected

    def _score(
        self, seg: ContextSegment, now: float, current_goal: str
    ) -> float:
        """计算单一片段的综合得分。"""
        # 1. 优先级分
        priority_score = seg.priority

        # 2. 时效分（指数衰减）
        age_hours = (now - seg.timestamp) / 3600
        recency_score = math.exp(-age_hours / 24.0)

        # 3. 类型偏置
        type_score = self._type_boost_map.get(seg.type, 0.0)

        # 4. 与当前目标的相关性
        relevance = 0.0
        if current_goal and seg.content:
            goal_keywords = set(current_goal.lower().split())
            content_lower = seg.content.lower()
            matches = sum(1 for kw in goal_keywords if kw in content_lower)
            relevance = min(matches / max(len(goal_keywords), 1), 1.0)

        return (
            priority_score * self.priority_weight
            + recency_score * self.recency_weight
            + type_score * self.type_boost
            + relevance * self.diversity_penalty
        )
