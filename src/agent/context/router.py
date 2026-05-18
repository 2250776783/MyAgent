"""Context Router - 上下文路由器。

根据当前 Agent 状态和用户输入，决定哪些类型的上下文需要被激活、
注入或压缩。防止 irrelevant retrieval 和 context pollution。
"""

from __future__ import annotations

import logging

from .types import ContextType

logger = logging.getLogger(__name__)


class ContextRouter:
    """上下文路由器。

    职责:
    - 决定当前轮需要激活哪些上下文类型
    - 控制上下文的注入优先级和频率
    - 防止无关上下文污染

    Args:
        enable_types: 启用的上下文类型集合（默认全部）
        max_active_types: 每轮最多激活的类型数
    """

    def __init__(
        self,
        enable_types: set[ContextType] | None = None,
        max_active_types: int = 6,
    ) -> None:
        self.enable_types = enable_types or set(ContextType)
        self.max_active_types = max_active_types
        self._round_robin: dict[ContextType, int] = {
            t: 0 for t in ContextType
        }

    def route(
        self,
        user_input: str,
        has_tool_calls: bool = False,
        has_errors: bool = False,
        goal_active: bool = False,
        task_count: int = 0,
        rounds_since_last_reflection: int = 0,
        is_overflow: bool = False,
    ) -> list[ContextType]:
        """根据当前状态决定激活哪些上下文类型。"""
        active: list[ContextType] = []

        # 系统指令始终激活
        active.append(ContextType.SYSTEM)

        # 目标上下文：有活跃目标时
        if goal_active:
            active.append(ContextType.GOAL)
            if task_count > 0:
                active.append(ContextType.TASK)

        # 工具上下文：有工具调用时
        if has_tool_calls:
            active.append(ContextType.TOOL)
            active.append(ContextType.TOOL_OUTPUT)

        # 记忆上下文：用户输入有意义内容时（每 3 轮至少激活一次）
        memory_interval = self._round_robin.get(ContextType.MEMORY, 0)
        if len(user_input.strip()) > 5 or memory_interval >= 3:
            active.append(ContextType.MEMORY)
            self._round_robin[ContextType.MEMORY] = 0
        else:
            self._round_robin[ContextType.MEMORY] = memory_interval + 1

        # 环境上下文：长时间未更新时
        env_interval = self._round_robin.get(ContextType.ENVIRONMENT, 0)
        if env_interval >= 5:
            active.append(ContextType.ENVIRONMENT)
            self._round_robin[ContextType.ENVIRONMENT] = 0
        else:
            self._round_robin[ContextType.ENVIRONMENT] = env_interval + 1

        # 反思上下文：有错误或距离上次反思较远时
        if has_errors or rounds_since_last_reflection >= 8:
            active.append(ContextType.REFLECTION)

        # 溢出时启用压缩上下文
        if is_overflow:
            active.append(ContextType.COMPRESSED)

        # 裁剪到最大激活数
        if len(active) > self.max_active_types:
            essential = {ContextType.SYSTEM, ContextType.GOAL, ContextType.TASK}
            must_keep = [t for t in active if t in essential]
            optional = [t for t in active if t not in essential]
            active = must_keep + optional[:self.max_active_types - len(must_keep)]

        return active
