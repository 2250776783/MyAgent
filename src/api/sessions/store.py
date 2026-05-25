"""Session 存储层。

提供内存 SessionStore 和 RedisSessionStore：
- SessionStore: 内存实现，适合开发/测试
- RedisSessionStore: Redis 实现，适合生产（支持持久化、分布式、TTL）
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


class RedisSessionStore:
    """基于 Redis 的 Session 存储（生产推荐）。

    支持：
    - Session 元数据持久化
    - Agent 状态快照缓存
    - 自动 TTL 过期
    - 分布式共享（多实例）

    依赖: redis>=5.2.0

    用法::

        store = RedisSessionStore()
        await store.connect()
        session = await store.get_or_create("session_id", agent_factory)
        await store.set_agent_state("session_id", {"key": "value"})
        state = await store.get_agent_state("session_id")
        await store.close()
    """

    TTL_SESSION = 3600       # 1h: session 元数据
    TTL_STATE = 7200         # 2h: Agent 状态快照
    TTL_INACTIVE = 604800    # 7d: 非活跃 session 清理阈值

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int = 1,
        password: str | None = None,
        key_prefix: str = "agent",
        env: str = "prod",
    ) -> None:
        from src.agent.memory.stores.redis_cache import RedisCache
        self._cache = RedisCache(
            host=host, port=port, db=db, password=password,
            key_prefix=key_prefix, env=env,
        )
        self._local_sessions: dict[str, Session] = {}

    async def connect(self) -> None:
        await self._cache.connect()

    async def close(self) -> None:
        await self._cache.close()

    async def get_or_create(
        self,
        session_id: str | None = None,
        agent_factory=None,
    ) -> Session:
        sid = session_id or uuid.uuid4().hex

        cached = await self._cache.get_session(sid)
        if cached:
            session = Session(
                id=sid,
                created_at=cached.get("created_at", time.time()),
                last_active=time.time(),
                metadata=cached.get("metadata", {}),
            )
            if sid not in self._local_sessions and agent_factory:
                session.agent = agent_factory()
                self._local_sessions[sid] = session
            elif sid in self._local_sessions:
                session.agent = self._local_sessions[sid].agent
                self._local_sessions[sid].last_active = time.time()
            return session

        session = Session(id=sid)
        if agent_factory:
            session.agent = agent_factory()
        self._local_sessions[sid] = session

        await self._cache.set_session(sid, {
            "created_at": session.created_at,
            "metadata": session.metadata,
        })
        return session

    async def get(self, session_id: str) -> Session | None:
        session = self._local_sessions.get(session_id)
        if session:
            session.last_active = time.time()
            return session

        cached = await self._cache.get_session(session_id)
        if cached:
            session = Session(
                id=session_id,
                created_at=cached.get("created_at", time.time()),
                last_active=time.time(),
                metadata=cached.get("metadata", {}),
            )
            return session
        return None

    async def delete(self, session_id: str) -> bool:
        self._local_sessions.pop(session_id, None)
        await self._cache.delete_session_cache(session_id)
        return True

    async def list_active(self) -> list[Session]:
        now = time.time()
        return [
            s for s in self._local_sessions.values()
            if now - s.last_active < self.TTL_INACTIVE
        ]

    async def cleanup_expired(self) -> int:
        now = time.time()
        expired = [
            sid for sid, s in self._local_sessions.items()
            if now - s.last_active > self.TTL_INACTIVE
        ]
        for sid in expired:
            self._local_sessions.pop(sid, None)
            await self._cache.delete_session_cache(sid)
        return len(expired)

    async def set_agent_state(
        self, session_id: str, state: dict, ttl: int | None = None
    ) -> None:
        await self._cache.set_agent_state(
            "session", session_id, state, ttl=ttl
        )

    async def get_agent_state(self, session_id: str) -> dict | None:
        return await self._cache.get_agent_state("session", session_id)

    async def save_session_metadata(
        self, session_id: str, metadata: dict
    ) -> None:
        if session_id in self._local_sessions:
            self._local_sessions[session_id].metadata.update(metadata)
        await self._cache.set_session(session_id, {
            "created_at": time.time(),
            "metadata": metadata,
        })
