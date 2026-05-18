"""Context Builder - 上下文构建器。

从多个来源构建上下文片段列表：
协调 Router/Ranker/WindowManager 完成上下文的
构建→排序→选择→组装全流程。
"""

from __future__ import annotations

import logging

from src.llm import Message, TokenCounter

from .router import ContextRouter
from .ranker import ContextRanker
from .window import ContextWindowManager
from .types import (
    ContextAssembly,
    ContextSegment,
    ContextType,
    Goal,
    Task,
    ToolCallRecord,
    InjectionPhase,
)

logger = logging.getLogger(__name__)


class ContextBuilder:
    """上下文构建器。

    Args:
        router: 上下文路由器
        ranker: 上下文排名器
        window_manager: 上下文窗口管理器
        token_counter: Token 计数器
    """

    def __init__(
        self,
        router: ContextRouter | None = None,
        ranker: ContextRanker | None = None,
        window_manager: ContextWindowManager | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.router = router or ContextRouter()
        self.ranker = ranker or ContextRanker()
        self.window = window_manager or ContextWindowManager()
        self.token_counter = token_counter or TokenCounter()

    def build(
        self,
        system_prompt: str,
        messages: list[Message],
        active_types: list[ContextType],
        goal: Goal | None = None,
        tasks: list[Task] | None = None,
        tool_records: list[ToolCallRecord] | None = None,
        memory_segments: list[ContextSegment] | None = None,
        reflection_segments: list[ContextSegment] | None = None,
        environment_segment: ContextSegment | None = None,
        compressed_segments: list[ContextSegment] | None = None,
    ) -> ContextAssembly:
        """构建完整上下文。"""
        assembly = ContextAssembly(budget=self.window.budget)
        all_candidates: list[ContextSegment] = []

        # 1. 系统指令
        system_seg = ContextSegment.create(
            ContextType.SYSTEM, system_prompt,
            priority=1.0, phase=InjectionPhase.SYSTEM,
        )
        system_seg.token_count = self.token_counter.count(system_prompt)
        all_candidates.append(system_seg)

        # 2. 目标上下文
        if goal and ContextType.GOAL in active_types:
            gs = goal.to_context()
            gs.token_count = self.token_counter.count(gs.content)
            all_candidates.append(gs)

        # 3. 任务上下文
        if tasks and ContextType.TASK in active_types:
            for task in tasks:
                ts = task.to_context()
                ts.token_count = self.token_counter.count(ts.content)
                all_candidates.append(ts)

        # 4. 工具调用记录
        if tool_records and ContextType.TOOL_OUTPUT in active_types:
            for record in tool_records[-5:]:
                ts = record.to_context()
                ts.token_count = self.token_counter.count(ts.content)
                all_candidates.append(ts)

        # 5. 记忆片段
        if memory_segments and ContextType.MEMORY in active_types:
            all_candidates.extend(memory_segments)

        # 6. 反思片段
        if reflection_segments and ContextType.REFLECTION in active_types:
            all_candidates.extend(reflection_segments)

        # 7. 环境信息
        if environment_segment and ContextType.ENVIRONMENT in active_types:
            environment_segment.token_count = self.token_counter.count(
                environment_segment.content
            )
            all_candidates.append(environment_segment)

        # 8. 压缩的历史上下文
        if compressed_segments and ContextType.COMPRESSED in active_types:
            all_candidates.extend(compressed_segments)

        # 9. 工作记忆（消息历史）
        working_text = self._format_messages(messages)
        if messages and ContextType.WORKING in active_types:
            ws = ContextSegment.create(
                ContextType.WORKING, working_text,
                priority=0.8, phase=InjectionPhase.WORKING,
            )
            ws.token_count = self.token_counter.count(working_text)
            all_candidates.append(ws)

        # 排名 & 选择
        goal_text = goal.description if goal else ""
        ranked = self.ranker.rank(all_candidates, current_goal=goal_text)

        for seg in ranked:
            self.window.update_usage(seg)
            if self.window.check_overflow():
                budget = self.window.budget.get(seg.type)
                if seg.token_count > budget and seg.type != ContextType.SYSTEM:
                    self.window.current_usage.total -= seg.token_count
                    assembly.dropped_count += 1
                    continue
            assembly.add(seg)

        assembly.usage = self.window.current_usage
        return assembly

    def _format_messages(self, messages: list[Message]) -> str:
        """将消息列表格式化为文本。"""
        parts = []
        for msg in messages:
            if msg.role == "system":
                continue
            if msg.role == "user":
                parts.append(f"用户: {msg.content}")
            elif msg.role == "assistant":
                if msg.content:
                    parts.append(f"助手: {msg.content}")
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        fn = tc.get("function", {})
                        parts.append(
                            f"调用工具: {fn.get('name', '')}"
                            f"({fn.get('arguments', '')})"
                        )
            elif msg.role == "tool":
                parts.append(f"工具返回: {msg.content[:200]}")
        return "\n".join(parts)
