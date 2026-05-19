"""日志系统常量和枚举定义。"""

from enum import Enum


class EventType(str, Enum):
    """统一日志事件类型 — 覆盖 AI Agent 全场景。"""

    # Agent 生命周期
    AGENT_THOUGHT = "agent.thought"
    AGENT_DECISION = "agent.decision"
    AGENT_REFLECTION = "agent.reflection"
    AGENT_EVENT = "agent.event"

    # 工具调用
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"

    # LLM 交互
    LLM_PROMPT = "llm.prompt"
    LLM_RESPONSE = "llm.response"
    LLM_STREAM = "llm.stream"
    LLM_ERROR = "llm.error"

    # 记忆系统
    MEMORY_RETRIEVAL = "memory.retrieval"
    MEMORY_STORE = "memory.store"
    MEMORY_DECAY = "memory.decay"

    # 系统事件
    SESSION_START = "session.start"
    SESSION_END = "session.end"
    CONTEXT_BUILD = "context.build"
    CONTEXT_TRIM = "context.trim"
    HTTP_REQUEST = "http.request"
    ERROR = "system.error"
    AUDIT = "system.audit"


class LogLevel(str, Enum):
    """日志级别。"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_LEVEL_NUMBERS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def level_number(name: str) -> int:
    return _LEVEL_NUMBERS.get(name.upper(), 20)
