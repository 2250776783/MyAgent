"""记忆系统数据模型。

定义 MemoryItem、MemoryInput、MemoryQuery 等核心数据结构，
以及 Episode、Reflection 等高层记忆类型。
"""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryItem:
    """记忆条目 - 系统中所有记忆的统一表示。"""
    id: str
    content: str
    type: str  # "episode" | "entity" | "preference" | "reflection"
    importance: float  # 0-1
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source_session: str | None = None


@dataclass
class MemoryInput:
    """记忆写入请求。"""
    content: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    source_session: str | None = None


@dataclass
class MemoryQuery:
    """记忆检索请求。"""
    query_text: str
    memory_types: list[str] | None = None
    k: int = 5
    recency_weight: float = 0.3
    relevance_weight: float = 0.5
    importance_weight: float = 0.2
    min_relevance: float = 0.6
    recency_decay_hours: float = 24.0


@dataclass
class Episode:
    """会话情景记忆。"""
    session_id: str
    summary: str
    message_count: int
    token_count: int
    start_time: float
    end_time: float
    importance: float = 0.5
    key_events: list[dict[str, Any]] = field(default_factory=list)

    def to_memory_item(self) -> MemoryItem:
        return MemoryItem(
            id=self.session_id,
            content=f"[会话] {self.summary} ({self.message_count}条消息)",
            type="episode",
            importance=self.importance,
            timestamp=self.end_time,
            metadata={
                "session_id": self.session_id,
                "message_count": self.message_count,
                "token_count": self.token_count,
                "start_time": self.start_time,
                "key_events": self.key_events,
            },
            source_session=self.session_id,
        )


@dataclass
class Reflection:
    """反思结果。"""
    content: str
    reflection_type: str
    source_ids: list[str] = field(default_factory=list)
    importance: float = 0.5
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    def to_memory_item(self) -> MemoryItem:
        return MemoryItem(
            id=f"refl_{int(self.timestamp)}_{abs(hash(self.content)) % 10000}",
            content=f"[{self.reflection_type}] {self.content}",
            type="reflection",
            importance=self.importance,
            timestamp=self.timestamp,
            metadata={
                "reflection_type": self.reflection_type,
                "source_ids": self.source_ids,
            },
        )
