"""ContextManager - 上下文系统统一 Facade。

整合所有上下文模块，提供 Agent 可直接调用的高层接口。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.agent.memory import MemoryManager
from src.agent.memory.reflection import ReflectionSystem
from src.llm import LLMClient, Message, TokenCounter

from .builder import ContextBuilder
from .router import ContextRouter
from .ranker import ContextRanker
from .compressor import ContextCompressor
from .window import ContextWindowManager
from .assembler import PromptAssembler
from .goal import GoalContext
from .task import TaskTracker
from .tool import ToolContext
from .environment import EnvironmentContext
from .memory import MemoryContext
from .reflection import ReflectionContext
from .injector import DynamicInjector
from .types import (
    ContextAssembly,
    ContextBudget,
    ContextSegment,
    ContextState,
    ContextType,
    Goal,
    Task,
    CompressionStrategy,
)

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文系统管理器 - 统一 Facade。

    供 Agent 调用的高层接口，协调所有上下文模块：

    1. on_chat_start: 路由上下文类型 → 构建 → 组装 prompt
    2. on_tool_call / on_tool_result: 追踪工具调用
    3. set_goal / add_task: 目标/任务管理
    4. build_prompt: 渲染最终 prompt
    5. on_chat_end: 通知各子系统

    用法::

        cm = ContextManager(llm=llm, memory=memory_manager)
        cm.start_session()
        cm.set_goal("查询订单信息")
        prompt = cm.build_prompt(
            system_prompt="你是一个助手",
            messages=[...],
            user_input="帮我查订单",
        )

    Args:
        llm: LLM 客户端（用于压缩等）
        memory: MemoryManager 实例
        token_counter: Token 计数器
    """

    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: MemoryManager | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.llm = llm
        self.token_counter = token_counter or TokenCounter()

        # 预算和窗口
        self.budget = ContextBudget()
        self.window_manager = ContextWindowManager(
            budget=self.budget, token_counter=self.token_counter,
        )

        # 路由和排名
        self.router = ContextRouter()
        self.ranker = ContextRanker()
        self.compressor = ContextCompressor(
            llm=llm, token_counter=self.token_counter,
        )
        self.assembler = PromptAssembler(token_counter=self.token_counter)

        # 领域上下文
        self.goal_ctx = GoalContext()
        self.task_tracker = TaskTracker()
        self.tool_ctx = ToolContext()
        self.env_ctx = EnvironmentContext()
        self.memory_ctx = MemoryContext(
            memory=memory, token_counter=self.token_counter,
        )

        # 反思系统
        reflection_system: ReflectionSystem | None = None
        if memory and memory._store and llm:
            reflection_system = ReflectionSystem(
                store=memory._store, llm=llm,
            )
        self.reflection_ctx = ReflectionContext(
            reflection_system=reflection_system,
            token_counter=self.token_counter,
        )

        # 动态注入
        self.injector = DynamicInjector(token_counter=self.token_counter)

        # 构建器
        self.builder = ContextBuilder(
            router=self.router, ranker=self.ranker,
            window_manager=self.window_manager,
            token_counter=self.token_counter,
        )

        # 状态追踪
        self._state = ContextState()
        self._rounds_since_reflection: int = 0
        self._consecutive_tool_calls: int = 0
        self._last_assembly: ContextAssembly | None = None
        self._compressed_segments: list[ContextSegment] = []
        self._session_id: str = ""

    # ------------------------------------------------------------------
    # Session 生命周期
    # ------------------------------------------------------------------

    def start_session(self) -> str:
        self._session_id = f"ctx_{int(time.time())}"
        self._state = ContextState()
        self._rounds_since_reflection = 0
        self._consecutive_tool_calls = 0
        self._compressed_segments = []
        if self.memory_ctx and self.memory_ctx.memory:
            self.memory_ctx.memory.start_session()
        logger.info("Context session started: %s", self._session_id)
        return self._session_id

    # ------------------------------------------------------------------
    # 目标/任务管理
    # ------------------------------------------------------------------

    def set_goal(self, description: str, criteria: list[str] | None = None) -> Goal:
        return self.goal_ctx.set_goal(description, criteria)

    def update_goal_progress(self, goal_id: str, progress: float) -> None:
        self.goal_ctx.update_progress(goal_id, progress)

    def add_task(
        self, description: str, depends_on: list[str] | None = None,
    ) -> Task:
        goal_id = self.goal_ctx.active_goal.id if self.goal_ctx.active_goal else ""
        return self.task_tracker.add_task(description, goal_id=goal_id, depends_on=depends_on)

    def start_task(self, task_id: str) -> None:
        self.task_tracker.start_task(task_id)

    def complete_task(self, task_id: str, result: str = "") -> None:
        self.task_tracker.complete_task(task_id, result)

    def fail_task(self, task_id: str, error: str = "") -> None:
        self.task_tracker.fail_task(task_id, error)

    # ------------------------------------------------------------------
    # 工具调用追踪
    # ------------------------------------------------------------------

    def on_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> str:
        self._consecutive_tool_calls += 1
        self._state.tool_call_count += 1
        return self.tool_ctx.record_call(tool_name, arguments)

    def on_tool_result(self, call_id: str, result: str, success: bool,
                       duration_ms: float = 0.0) -> None:
        self.tool_ctx.record_result(call_id, result, success, duration_ms)
        if not success:
            self._state.repeated_failures += 1
        else:
            self._state.repeated_failures = 0

    # ------------------------------------------------------------------
    # Prompt 构建（核心流程）
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        system_prompt: str,
        messages: list[Message],
        user_input: str = "",
    ) -> str:
        """构建最终 prompt。

        完整流程:
        1. 判断状态 → 路由激活类型
        2. 收集各领域上下文片段
        3. 压缩历史（如需要）
        4. 排名 → 选择 → 组装
        5. 渲染 prompt
        """
        goal = self.goal_ctx.active_goal
        has_tool_calls = bool(
            messages and messages[-1].tool_calls
        ) if messages else False
        has_errors = self._state.repeated_failures > 0
        is_overflow = self.window_manager.check_overflow()

        # 1. 路由
        active_types = self.router.route(
            user_input=user_input,
            has_tool_calls=has_tool_calls,
            has_errors=has_errors,
            goal_active=(goal is not None),
            task_count=len(self.task_tracker.active_tasks),
            rounds_since_last_reflection=self._rounds_since_reflection,
            is_overflow=is_overflow,
        )

        # 2. 收集各领域上下文
        goal_seg = self.goal_ctx.build_context()
        task_segs = self.task_tracker.build_context()
        tool_segs = self.tool_ctx.build_context()
        env_seg = self.env_ctx.build()
        memory_segs = self.memory_ctx.retrieve(user_input) if user_input else []
        reflection_segs = self.reflection_ctx.run()

        # 3. 动态注入
        attention_guide = self.injector.build_attention_guide(
            active_goal=goal.description if goal else "",
            current_task=(
                self.task_tracker.active_tasks[0].description
                if self.task_tracker.active_tasks else ""
            ),
            warnings=self._build_warnings(),
        )
        anti_repeat = self.injector.build_anti_repetition(self._consecutive_tool_calls)

        # 4. 漂移检测
        drift_seg = None
        if user_input and goal and self.goal_ctx.detect_drift(user_input):
            drift_seg = self.reflection_ctx.build_drift_context(user_input)
            self._state.drift_warning = True

        # 5. 构建
        all_memory: list[ContextSegment] = (memory_segs or []) + (reflection_segs or [])
        all_extra: list[ContextSegment] = []
        if attention_guide:
            all_extra.append(attention_guide)
        if anti_repeat:
            all_extra.append(anti_repeat)
        if drift_seg:
            all_extra.append(drift_seg)

        assembly = self.builder.build(
            system_prompt=system_prompt,
            messages=messages,
            active_types=active_types,
            goal=goal,
            tasks=self.task_tracker.active_tasks,
            tool_records=self.tool_ctx.records,
            memory_segments=all_memory,
            reflection_segments=None,
            environment_segment=env_seg,
            compressed_segments=self._compressed_segments,
        )

        # 6. 压缩
        if self.window_manager.should_compress(assembly.segments):
            compressed = self.compressor.compress_batch(
                assembly.segments,
                self.budget.total_max - self.budget.reserved_system,
            )
            assembly.compressed_count = len(assembly.segments) - len(compressed)
            assembly.segments = compressed
            saved = sum(s.token_count for s in compressed) - sum(
                s.token_count for s in assembly.segments
            )
            self.window_manager.record_compression(saved)
            self._compressed_segments = compressed

        self._last_assembly = assembly
        self._state.total_tokens_used = assembly.total_tokens
        self._state.current_iteration += 1

        return self.assembler.assemble(assembly)

    # ------------------------------------------------------------------
    # 系统提示增强（供 Agent 注入 system prompt）
    # ------------------------------------------------------------------

    def build_system_augmentation(self, user_input: str = "") -> str:
        """构建系统提示增强文本，追加到 system prompt 后。

        与 build_prompt 不同，此方法仅返回上下文注入部分
        （目标、任务、记忆、反思、注意力引导等），
        不包含 system prompt 和对话历史。
        Agent 可将返回值追加到 system prompt 末尾。
        """
        goal = self.goal_ctx.active_goal
        has_errors = self._state.repeated_failures > 0
        is_overflow = self.window_manager.check_overflow()

        active_types = self.router.route(
            user_input=user_input,
            has_tool_calls=False,
            has_errors=has_errors,
            goal_active=(goal is not None),
            task_count=len(self.task_tracker.active_tasks),
            rounds_since_last_reflection=self._rounds_since_reflection,
            is_overflow=is_overflow,
        )

        parts = []

        if goal and ContextType.GOAL in active_types:
            seg = goal.to_context()
            parts.append(seg.content)

        if self.task_tracker.active_tasks and ContextType.TASK in active_types:
            for t in self.task_tracker.active_tasks:
                seg = t.to_context()
                parts.append(seg.content)

        if user_input:
            memory_segs = self.memory_ctx.retrieve(user_input)
            if memory_segs and ContextType.MEMORY in active_types:
                for s in memory_segs:
                    parts.append(f"[记忆] {s.content}")

        reflection_segs = self.reflection_ctx.run()
        if reflection_segs and ContextType.REFLECTION in active_types:
            for s in reflection_segs:
                parts.append(f"[反思] {s.content}")

        attention = self.injector.build_attention_guide(
            active_goal=goal.description if goal else "",
            current_task=(
                self.task_tracker.active_tasks[0].description
                if self.task_tracker.active_tasks else ""
            ),
            warnings=self._build_warnings(),
        )
        if attention:
            parts.append(attention.content)

        anti_repeat = self.injector.build_anti_repetition(self._consecutive_tool_calls)
        if anti_repeat:
            parts.append(anti_repeat.content)

        if user_input and goal and self.goal_ctx.detect_drift(user_input):
            parts.append(f"[警告] 检测到潜在的目标偏离: {user_input}")
            self._state.drift_warning = True

        if not parts:
            return ""
        return "\n\n".join(parts)

    def trim_messages(self, messages: list) -> list:
        """裁剪消息列表（委托给 MemoryManager）。"""
        if self.memory_ctx and self.memory_ctx.memory:
            return self.memory_ctx.memory.trim_messages(messages)
        return messages

    def _build_warnings(self) -> list[str]:
        warnings = []
        if self.tool_ctx.detect_tool_loop():
            warnings.append("检测到可能的工具调用循环，请考虑换一种方法")
        if self._state.repeated_failures >= 2:
            warnings.append(f"连续 {self._state.repeated_failures} 次操作失败")
        if self.window_manager.check_overflow():
            warnings.append("上下文接近容量上限")
        return warnings

    # ------------------------------------------------------------------
    # 生命周期回调
    # ------------------------------------------------------------------

    def on_chat_start(self, user_input: str) -> str:
        self._consecutive_tool_calls = 0
        return ""

    def on_chat_end(self, messages: list[Message]) -> None:
        self.memory_ctx.on_chat_end(messages)
        self._rounds_since_reflection += 1

    def on_reset(self) -> None:
        self.goal_ctx = GoalContext()
        self.task_tracker = TaskTracker()
        self.tool_ctx = ToolContext()
        self._state = ContextState()
        self._rounds_since_reflection = 0
        self._consecutive_tool_calls = 0
        self._compressed_segments = []
        self._last_assembly = None
        if self.memory_ctx and self.memory_ctx.memory:
            self.memory_ctx.memory.on_reset()

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    def get_state(self) -> ContextState:
        self._state.active_goal = self.goal_ctx.active_goal
        self._state.active_tasks = self.task_tracker.active_tasks
        self._state.completed_tasks = self.task_tracker.completed_tasks
        return self._state

    def get_token_report(self) -> str:
        return self.window_manager.get_usage_report()

    def get_assembly_report(self) -> str:
        if not self._last_assembly:
            return "No assembly yet"
        return self.assembler.get_token_breakdown(self._last_assembly)

    @property
    def session_id(self) -> str:
        return self._session_id
