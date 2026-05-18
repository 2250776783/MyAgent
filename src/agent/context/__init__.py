"""Context System - LLM Agent 上下文系统。

提供完整的上下文生命周期管理，支持：
- 多源上下文构建与路由
- 目标/任务追踪（防止 long-horizon drift）
- 工具输出管理（防 tool output explosion）
- 上下文压缩与排名
- 动态上下文注入
- 与记忆系统协同
- 反思驱动

用法::

    from src.agent.context import ContextManager

    ctx = ContextManager(llm=llm, memory=memory_manager)
    ctx.start_session()
    ctx.set_goal("查询用户订单信息")
    ctx.on_chat_start("帮我查一下最近三个月的订单")
    ctx.on_tool_call("search_orders", {"user_id": "123"})
    ctx.on_tool_result("search_orders", ToolOutput(success=True, output="..."))
    prompt = ctx.build_prompt(messages)
    ctx.on_chat_end(messages)
"""

from .manager import ContextManager
from .types import (
    ContextType,
    ContextSegment,
    ContextAssembly,
    ContextBudget,
    ContextState,
    Goal,
    GoalStatus,
    Task,
    TaskStatus,
    ToolCallRecord,
    InjectionPhase,
    CompressionStrategy,
    TokenUsage,
)
from .builder import ContextBuilder
from .router import ContextRouter
from .ranker import ContextRanker
from .compressor import ContextCompressor
from .window import ContextWindowManager
from .assembler import PromptAssembler
from .working import WorkingContext
from .goal import GoalContext
from .task import TaskTracker
from .tool import ToolContext
from .environment import EnvironmentContext
from .memory import MemoryContext
from .reflection import ReflectionContext
from .injector import DynamicInjector

__all__ = [
    "ContextManager",
    "ContextType", "ContextSegment", "ContextAssembly", "ContextBudget",
    "ContextState", "Goal", "GoalStatus", "Task", "TaskStatus",
    "ToolCallRecord", "InjectionPhase", "CompressionStrategy", "TokenUsage",
    "ContextBuilder", "ContextRouter", "ContextRanker", "ContextCompressor",
    "ContextWindowManager", "PromptAssembler",
    "WorkingContext", "GoalContext", "TaskTracker", "ToolContext",
    "EnvironmentContext", "MemoryContext", "ReflectionContext", "DynamicInjector",
]
