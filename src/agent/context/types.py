"""Context System 核心数据类型。

定义 Context System 中所有数据结构和枚举类型，
作为整个上下文系统的类型基础。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ContextType(str, Enum):
    """上下文类型枚举 - 标识不同来源的上下文片段。"""
    SYSTEM = "system"
    WORKING = "working"
    GOAL = "goal"
    TASK = "task"
    MEMORY = "memory"
    TOOL = "tool"
    TOOL_OUTPUT = "tool_output"
    ENVIRONMENT = "environment"
    REFLECTION = "reflection"
    PLAN = "plan"
    COMPRESSED = "compressed"


class CompressionStrategy(str, Enum):
    """压缩策略枚举。"""
    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"
    STRUCTURED = "structured"
    DROP = "drop"
    MERGE = "merge"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    PAUSED = "paused"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class InjectionPhase(str, Enum):
    """注入阶段枚举 - 控制 prompt 中各上下文的出现顺序。"""
    SYSTEM = "system"
    GOAL = "goal"
    MEMORY = "memory"
    TASK = "task"
    ENVIRONMENT = "environment"
    TOOL = "tool"
    WORKING = "working"
    REFLECTION = "reflection"


# ---------------------------------------------------------------------------
# Core Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ContextSegment:
    """上下文片段 - 上下文系统的最小单元。

    每个片段代表一个独立、可管理的上下文块，
    带有类型、来源、优先级、token 数等元数据。
    """
    id: str
    type: ContextType
    content: str
    priority: float = 0.5
    token_count: int = 0
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    phase: InjectionPhase = InjectionPhase.WORKING

    @classmethod
    def create(
        cls,
        type_: ContextType,
        content: str,
        priority: float = 0.5,
        phase: InjectionPhase | None = None,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ContextSegment:
        return cls(
            id=uuid.uuid4().hex[:12],
            type=type_,
            content=content,
            priority=priority,
            token_count=0,
            source=source,
            metadata=metadata or {},
            phase=phase or _default_phase(type_),
        )


def _default_phase(type_: ContextType) -> InjectionPhase:
    mapping: dict[ContextType, InjectionPhase] = {
        ContextType.SYSTEM: InjectionPhase.SYSTEM,
        ContextType.GOAL: InjectionPhase.GOAL,
        ContextType.MEMORY: InjectionPhase.MEMORY,
        ContextType.TASK: InjectionPhase.TASK,
        ContextType.ENVIRONMENT: InjectionPhase.ENVIRONMENT,
        ContextType.TOOL: InjectionPhase.TOOL,
        ContextType.WORKING: InjectionPhase.WORKING,
        ContextType.REFLECTION: InjectionPhase.REFLECTION,
        ContextType.TOOL_OUTPUT: InjectionPhase.TOOL,
        ContextType.PLAN: InjectionPhase.GOAL,
        ContextType.COMPRESSED: InjectionPhase.MEMORY,
    }
    return mapping.get(type_, InjectionPhase.WORKING)


@dataclass
class ContextBudget:
    """上下文 Token 预算分配。"""
    total_max: int = 128_000
    reserved_system: int = 2048
    reserved_working: int = 8192
    budget_per_type: dict[ContextType, int] = field(default_factory=lambda: {
        ContextType.GOAL: 1024,
        ContextType.TASK: 2048,
        ContextType.MEMORY: 2048,
        ContextType.TOOL: 2048,
        ContextType.ENVIRONMENT: 512,
        ContextType.REFLECTION: 1024,
        ContextType.COMPRESSED: 1024,
        ContextType.TOOL_OUTPUT: 4096,
    })

    def get(self, type_: ContextType) -> int:
        return self.budget_per_type.get(type_, 1024)

    def total_allocated(self) -> int:
        return self.reserved_system + self.reserved_working + sum(self.budget_per_type.values())

    def total_available(self) -> int:
        return self.total_max - self.reserved_system

    def remaining(self) -> int:
        return self.total_max - self.total_allocated()

    def adjust(self, type_: ContextType, delta: int) -> None:
        current = self.budget_per_type.get(type_, 1024)
        self.budget_per_type[type_] = max(256, current + delta)


@dataclass
class TokenUsage:
    """Token 使用统计。"""
    total: int = 0
    by_type: dict[ContextType, int] = field(default_factory=dict)
    system: int = 0
    working: int = 0
    compression_saved: int = 0


# ---------------------------------------------------------------------------
# Goal & Task
# ---------------------------------------------------------------------------

@dataclass
class Goal:
    """高层次目标 - 维持任务焦点，防止 long-horizon drift。"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    progress: float = 0.0
    criteria: list[str] = field(default_factory=list)
    sub_goals: list[str] = field(default_factory=list)
    parent_goal: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_progress(self, progress: float) -> None:
        self.progress = min(1.0, max(0.0, progress))
        self.updated_at = time.time()
        if self.progress >= 1.0:
            self.status = GoalStatus.COMPLETED

    def to_context(self) -> ContextSegment:
        status_icons = {
            GoalStatus.ACTIVE: "[进行中]",
            GoalStatus.COMPLETED: "[已完成]",
            GoalStatus.FAILED: "[失败]",
            GoalStatus.SUPERSEDED: "[已取代]",
            GoalStatus.PAUSED: "[已暂停]",
        }
        icon = status_icons.get(self.status, "")
        progress_pct = int(self.progress * 100)
        content = f"当前目标{icon}: {self.description} (进度: {progress_pct}%)"
        if self.criteria:
            content += f"\n完成标准: {'; '.join(self.criteria[:3])}"
        return ContextSegment.create(
            type_=ContextType.GOAL,
            content=content,
            priority=0.9 if self.status == GoalStatus.ACTIVE else 0.3,
            phase=InjectionPhase.GOAL,
        )


@dataclass
class Task:
    """具体任务 - Goal 的分解步骤。"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    goal_id: str = ""
    depends_on: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: str = ""
    iteration: int = 0
    max_iterations: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_context(self) -> ContextSegment:
        status_icons = {
            TaskStatus.PENDING: "[待处理]",
            TaskStatus.IN_PROGRESS: "[处理中]",
            TaskStatus.COMPLETED: "[已完成]",
            TaskStatus.FAILED: "[失败]",
            TaskStatus.BLOCKED: "[阻塞]",
        }
        icon = status_icons.get(self.status, "")
        content = f"任务: {self.description} {icon}"
        if self.result:
            content += f"\n结果: {self.result[:200]}"
        priority_map = {
            TaskStatus.IN_PROGRESS: 0.9,
            TaskStatus.PENDING: 0.6,
            TaskStatus.BLOCKED: 0.7,
            TaskStatus.COMPLETED: 0.2,
            TaskStatus.FAILED: 0.4,
        }
        return ContextSegment.create(
            type_=ContextType.TASK,
            content=content,
            priority=priority_map.get(self.status, 0.5),
            phase=InjectionPhase.TASK,
        )


# ---------------------------------------------------------------------------
# Tool Call Record
# ---------------------------------------------------------------------------

@dataclass
class ToolCallRecord:
    """工具调用记录 - 追踪每次工具调用的完整信息。"""
    tool_name: str
    arguments: dict[str, Any]
    result: str = ""
    success: bool = False
    duration_ms: float = 0.0
    token_cost: int = 0
    timestamp: float = field(default_factory=time.time)
    call_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_context(self, max_chars: int = 2000) -> ContextSegment:
        """转为上下文片段，截断过长输出防 tool output explosion。"""
        truncated = self.result
        if len(truncated) > max_chars:
            truncated = truncated[:max_chars] + f"\n...(截断, 原始 {len(self.result)} 字符)"

        status = "成功" if self.success else "失败"
        content = (
            f"工具: {self.tool_name}\n"
            f"输入: {self.arguments}\n"
            f"状态: {status} ({self.duration_ms:.1f}ms)\n"
            f"输出: {truncated}"
        )
        return ContextSegment.create(
            type_=ContextType.TOOL_OUTPUT,
            content=content,
            priority=0.7 if self.success else 0.5,
            phase=InjectionPhase.TOOL,
            source=self.tool_name,
            metadata={"call_id": self.call_id, "success": self.success},
        )


# ---------------------------------------------------------------------------
# Context Assembly
# ---------------------------------------------------------------------------

@dataclass
class ContextAssembly:
    """已组装的上下文 - 最终注入到 LLM prompt 的完整结果。"""
    segments: list[ContextSegment] = field(default_factory=list)
    total_tokens: int = 0
    budget: ContextBudget = field(default_factory=ContextBudget)
    usage: TokenUsage = field(default_factory=TokenUsage)
    compressed_count: int = 0
    dropped_count: int = 0

    def to_prompt(self) -> str:
        """渲染最终 prompt。"""
        parts: list[str] = []
        phase_order = {p: i for i, p in enumerate(InjectionPhase)}
        sorted_segments = sorted(
            self.segments,
            key=lambda s: (phase_order.get(s.phase, 99), -s.priority),
        )
        for seg in sorted_segments:
            if seg.type == ContextType.SYSTEM:
                parts.insert(0, seg.content)
            else:
                label = _phase_label(seg.type)
                parts.append(f"{label}\n{seg.content}")
        return "\n".join(parts)

    def add(self, segment: ContextSegment) -> None:
        self.segments.append(segment)
        self.total_tokens += segment.token_count
        self.usage.by_type[segment.type] = (
            self.usage.by_type.get(segment.type, 0) + segment.token_count
        )


def _phase_label(type_: ContextType) -> str:
    labels = {
        ContextType.GOAL: "=== 当前目标 ===",
        ContextType.TASK: "=== 任务进度 ===",
        ContextType.MEMORY: "=== 相关记忆 ===",
        ContextType.ENVIRONMENT: "=== 环境信息 ===",
        ContextType.TOOL: "=== 可用工具 ===",
        ContextType.TOOL_OUTPUT: "=== 工具执行结果 ===",
        ContextType.REFLECTION: "=== 反思洞察 ===",
        ContextType.WORKING: "=== 对话历史 ===",
        ContextType.COMPRESSED: "=== 历史摘要 ===",
        ContextType.PLAN: "=== 执行计划 ===",
    }
    return labels.get(type_, f"=== {type_.value} ===")


# ---------------------------------------------------------------------------
# Context State Snapshot
# ---------------------------------------------------------------------------

@dataclass
class ContextState:
    """上下文状态快照 - 用于 Reflection 和状态恢复。"""
    active_goal: Goal | None = None
    active_tasks: list[Task] = field(default_factory=list)
    completed_tasks: list[Task] = field(default_factory=list)
    tool_call_count: int = 0
    total_tokens_used: int = 0
    current_iteration: int = 0
    drift_warning: bool = False
    repeated_failures: int = 0
    context_overflow_count: int = 0
