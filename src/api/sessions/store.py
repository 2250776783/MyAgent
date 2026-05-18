"""Session 存储层。

提供内存 SessionStore，支持创建、查询、删除和 TTL 过期清理。
后续可扩展 Redis 实现。
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from src.agent.async_agent import AsyncAgent


@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    agent: AsyncAgent | None = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """内存 Session 存储。

    每个 Session 持有独立的 AsyncAgent 实例，隔离天然实现。
    通过 TTL 过期清理机制防止内存泄漏。
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl_seconds

    async def get_or_create(
        self,
        session_id: str | None = None,
        agent_factory=None,
    ) -> Session:
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_active = time.time()
            return session

        session = Session(id=session_id or uuid.uuid4().hex)
        if agent_factory:
            session.agent = agent_factory()
        self._sessions[session.id] = session
        return session

    async def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def delete(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        return session is not None

    async def list_active(self) -> list[Session]:
        now = time.time()
        return [
            s for s in self._sessions.values()
            if now - s.last_active < self._ttl
        ]

    async def cleanup_expired(self) -> int:
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_active > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)
