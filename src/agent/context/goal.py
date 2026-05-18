"""Goal Context - 目标上下文管理器。

维护 Agent 的高层次目标，检测目标漂移，支持目标优先级管理。
"""

from __future__ import annotations

import logging
from typing import Any

from .types import Goal, GoalStatus, ContextSegment, ContextType, InjectionPhase

logger = logging.getLogger(__name__)


class GoalContext:
    """目标上下文管理器。

    Args:
        max_active_goals: 最大同时活跃目标数
    """

    def __init__(self, max_active_goals: int = 3) -> None:
        self._goals: list[Goal] = []
        self.max_active_goals = max_active_goals

    @property
    def active_goal(self) -> Goal | None:
        active = [g for g in self._goals if g.status == GoalStatus.ACTIVE]
        if not active:
            return None
        return max(active, key=lambda g: g.progress)

    @property
    def all_goals(self) -> list[Goal]:
        return list(self._goals)

    def set_goal(self, description: str, criteria: list[str] | None = None) -> Goal:
        goal = Goal(description=description, criteria=criteria or [])
        self._goals.append(goal)
        if len([g for g in self._goals if g.status == GoalStatus.ACTIVE]) > self.max_active_goals:
            for g in self._goals:
                if g.status == GoalStatus.ACTIVE and g is not goal:
                    g.status = GoalStatus.PAUSED
                    break
        logger.info("Goal set: %s", description)
        return goal

    def update_progress(self, goal_id: str, progress: float) -> None:
        for goal in self._goals:
            if goal.id == goal_id:
                goal.update_progress(progress)
                break

    def complete_goal(self, goal_id: str) -> None:
        for goal in self._goals:
            if goal.id == goal_id:
                goal.status = GoalStatus.COMPLETED
                goal.progress = 1.0
                break

    def detect_drift(self, user_input: str) -> bool:
        """检测用户输入是否偏离当前目标。"""
        goal = self.active_goal
        if not goal or goal.status != GoalStatus.ACTIVE:
            return False
        goal_keywords = set(goal.description.lower().split())
        input_keywords = set(user_input.lower().split())
        overlap = goal_keywords & input_keywords
        if len(goal_keywords) > 3 and len(overlap) == 0 and len(input_keywords) < 5:
            logger.info("Potential goal drift detected: input=%s", user_input)
            return True
        return False

    def build_context(self) -> ContextSegment | None:
        goal = self.active_goal
        if not goal:
            return None
        return goal.to_context()
