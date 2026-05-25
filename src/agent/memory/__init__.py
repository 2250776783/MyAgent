"""Agent 记忆系统。

分层记忆架构：
- WorkingMemory: 短期工作记忆（token 滑动窗口）
- EpisodicMemory: 情景记忆（会话摘要 + 关键事件）
- SemanticMemory: 语义记忆（实体 + 偏好）
- MemoryRetriever: 多层检索（query expansion + rerank）
- ReflectionSystem: 反思系统（洞察提取）
- ForgettingMechanism: 遗忘衰减
- PromptInjector: 记忆注入
- MemoryManager: 统一 Facade

用法::

    from src.agent.memory import MemoryManager

    memory = MemoryManager(llm=llm, embedder=embedder)
    memory.start_session()
    memory.on_chat_start(user_input)
    memory.on_chat_end(messages)
    memory.trim_messages(messages)
"""

from .manager import MemoryManager

try:
    from .async_manager import AsyncMemoryManager
except ImportError:
    AsyncMemoryManager = None  # type: ignore[assignment, misc]

from .types import MemoryItem, MemoryInput, MemoryQuery, Episode, Reflection
from .working import WorkingMemory
from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .retrieval import MemoryRetriever
from .injector import PromptInjector
from .reflection import ReflectionSystem
from .decay import ForgettingMechanism
from .scorer import ImportanceScorer
from .resolver import ConflictResolver

__all__ = [
    "MemoryManager",
    "AsyncMemoryManager",
    "MemoryItem",
    "MemoryInput",
    "MemoryQuery",
    "Episode",
    "Reflection",
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "MemoryRetriever",
    "PromptInjector",
    "ReflectionSystem",
    "ForgettingMechanism",
    "ImportanceScorer",
    "ConflictResolver",
]
