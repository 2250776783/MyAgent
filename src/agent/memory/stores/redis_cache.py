"""Redis 缓存层 — Agent 记忆的热缓存与短期工作记忆。

负责：
- Hot Memory: 高频访问的记忆，避免重复 PG 查询
- Session Cache: 当前活跃会话的状态缓存
- 分布式锁: 并发安全的记忆写入
- 消息缓存: 最近 N 条消息的临时存储
- 嵌入缓存: 避免重复调用 embedding API
- Rate Limit: LLM 调用频率控制

依赖:
    redis>=5.2.0

用法::

    cache = RedisCache()
    await cache.connect()

    # 热记忆
    await cache.set_hot_memories(user_id, memories)
    cached = await cache.get_hot_memories(user_id)

    # 分布式锁
    async with cache.lock("memory:write:user_123"):
        ...

    await cache.close()
"""

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from src.config import settings

from ..types import MemoryItem

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]


class RedisCache:
    """Agent 记忆系统的 Redis 缓存层。

    提供热记忆缓存、会话状态缓存、分布式锁、消息缓存等功能。
    所有操作均为异步，需先调用 connect() 初始化连接池。
    """

    TTL_HOT_MEMORY = 900        # 15min: 热记忆
    TTL_RECENT_MEMORY = 300     # 5min: 最近记忆
    TTL_SESSION = 3600          # 1h: 会话缓存
    TTL_SESSION_MESSAGES = 1800 # 30min: 最近消息
    TTL_AGENT_STATE = 7200      # 2h: Agent 状态
    TTL_EMBEDDING_CACHE = 86400 # 24h: 嵌入缓存
    TTL_LOCK = 10               # 10s: 分布式锁
    TTL_RATE_LIMIT = 60         # 60s: 限流窗口
    TTL_KNOWLEDGE_CACHE = 3600  # 1h: RAG 缓存

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        key_prefix: str = "agent",
        env: str = "prod",
    ) -> None:
        if aioredis is None:
            raise ImportError(
                "redis is required. Install: uv add redis"
            )

        self._host = host or settings.redis_host
        self._port = port or settings.redis_port
        self._db = db or settings.redis_db
        self._password = password or settings.redis_password or None
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._key_prefix = key_prefix
        self._env = env
        self._pool: aioredis.ConnectionPool | None = None
        self._redis: aioredis.Redis | None = None

    # ── 连接管理 ──────────────────────────────────────────────────────

    async def connect(self) -> None:
        """初始化 Redis 连接池。"""
        if self._redis is not None:
            return
        self._pool = aioredis.ConnectionPool(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            max_connections=self._max_connections,
            socket_timeout=self._socket_timeout,
            decode_responses=True,
        )
        self._redis = aioredis.Redis(connection_pool=self._pool)
        await self._redis.ping()
        logger.info(
            "RedisCache connected (%s:%s/%d, pool=%d)",
            self._host, self._port, self._db, self._max_connections,
        )

    async def close(self) -> None:
        """关闭连接池。"""
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None
            logger.info("RedisCache disconnected")

    @property
    def _connected(self) -> bool:
        return self._redis is not None

    async def _ensure_conn(self) -> aioredis.Redis:
        if self._redis is None:
            await self.connect()
        assert self._redis is not None
        return self._redis

    def _key(self, *parts: str) -> str:
        return f"{self._key_prefix}:{self._env}:" + ":".join(parts)

    def _serialize(self, obj: Any) -> str:
        return json.dumps(obj, default=str)

    def _deserialize(self, data: str | None) -> Any:
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data

    # ── Hot Memory 缓存 ──────────────────────────────────────────────

    async def set_hot_memories(
        self, user_id: str, memories: list[MemoryItem], ttl: int | None = None
    ) -> None:
        """缓存用户的热记忆（Top-K 高频记忆）。"""
        redis = await self._ensure_conn()
        key = self._key("memory", "hot", user_id)
        data = [
            {
                "id": m.id,
                "content": m.content,
                "type": m.type,
                "importance": m.importance,
                "timestamp": m.timestamp,
                "access_count": m.access_count,
                "source_session": m.source_session,
                "metadata": m.metadata,
            }
            for m in memories
        ]
        await redis.setex(key, ttl or self.TTL_HOT_MEMORY, self._serialize(data))

    async def get_hot_memories(
        self, user_id: str, k: int = 10
    ) -> list[dict]:
        """获取用户的热记忆缓存。"""
        redis = await self._ensure_conn()
        key = self._key("memory", "hot", user_id)
        data = await redis.get(key)
        if data is None:
            return []
        memories = self._deserialize(data)
        return memories[:k] if memories else []

    async def set_recent_memories(
        self, user_id: str, memories: list[MemoryItem], ttl: int | None = None
    ) -> None:
        """缓存用户最近创建的记忆。"""
        redis = await self._ensure_conn()
        key = self._key("memory", "recent", user_id)
        data = [
            {
                "id": m.id,
                "content": m.content,
                "type": m.type,
                "importance": m.importance,
                "timestamp": m.timestamp,
            }
            for m in memories[-20:]
        ]
        await redis.setex(key, ttl or self.TTL_RECENT_MEMORY, self._serialize(data))

    async def get_recent_memories(self, user_id: str) -> list[dict]:
        redis = await self._ensure_conn()
        key = self._key("memory", "recent", user_id)
        data = await redis.get(key)
        return self._deserialize(data) or []

    async def delete_memory_cache(self, user_id: str) -> None:
        redis = await self._ensure_conn()
        await redis.delete(
            self._key("memory", "hot", user_id),
            self._key("memory", "recent", user_id),
        )

    # ── Session 缓存 ─────────────────────────────────────────────────

    async def set_session(
        self, session_id: str, data: dict, ttl: int | None = None
    ) -> None:
        redis = await self._ensure_conn()
        key = self._key("session", session_id)
        await redis.setex(key, ttl or self.TTL_SESSION, self._serialize(data))

    async def get_session(self, session_id: str) -> dict | None:
        redis = await self._ensure_conn()
        key = self._key("session", session_id)
        data = await redis.get(key)
        return self._deserialize(data)

    async def cache_session_messages(
        self, session_id: str, messages: list[dict], ttl: int | None = None
    ) -> None:
        redis = await self._ensure_conn()
        key = self._key("session", session_id, "messages")
        data = messages[-50:]
        await redis.setex(key, ttl or self.TTL_SESSION_MESSAGES, self._serialize(data))

    async def get_session_messages(self, session_id: str) -> list[dict] | None:
        redis = await self._ensure_conn()
        key = self._key("session", session_id, "messages")
        data = await redis.get(key)
        return self._deserialize(data)

    async def delete_session_cache(self, session_id: str) -> None:
        redis = await self._ensure_conn()
        await redis.delete(
            self._key("session", session_id),
            self._key("session", session_id, "messages"),
        )

    # ── Agent 状态缓存 ────────────────────────────────────────────────

    async def set_agent_state(
        self, agent_id: str, session_id: str, state: dict, ttl: int | None = None
    ) -> None:
        redis = await self._ensure_conn()
        key = self._key("state", agent_id, session_id)
        await redis.setex(key, ttl or self.TTL_AGENT_STATE, self._serialize(state))

    async def get_agent_state(
        self, agent_id: str, session_id: str
    ) -> dict | None:
        redis = await self._ensure_conn()
        key = self._key("state", agent_id, session_id)
        data = await redis.get(key)
        return self._deserialize(data)

    # ── 分布式锁 ─────────────────────────────────────────────────────

    async def acquire_lock(
        self, lock_key: str, ttl: int | None = None, owner: str | None = None
    ) -> bool:
        redis = await self._ensure_conn()
        key = self._key("lock", lock_key)
        owner = owner or str(uuid.uuid4())
        result = await redis.set(key, owner, nx=True, ex=ttl or self.TTL_LOCK)
        return result is not None

    async def release_lock(self, lock_key: str, owner: str | None = None) -> bool:
        redis = await self._ensure_conn()
        key = self._key("lock", lock_key)
        if owner is None:
            await redis.delete(key)
            return True
        lua = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        result = await redis.eval(lua, 1, key, owner)
        return bool(result)

    @asynccontextmanager
    async def lock(
        self, lock_key: str, ttl: int | None = None
    ) -> AsyncIterator[bool]:
        """分布式锁上下文管理器。"""
        owner = str(uuid.uuid4())
        acquired = await self.acquire_lock(lock_key, ttl, owner)
        try:
            yield acquired
        finally:
            if acquired:
                await self.release_lock(lock_key, owner)

    async def extend_lock(
        self, lock_key: str, owner: str, ttl: int = 10
    ) -> bool:
        redis = await self._ensure_conn()
        key = self._key("lock", lock_key)
        lua = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("EXPIRE", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        result = await redis.eval(lua, 1, key, owner, str(ttl))
        return bool(result)

    # ── Rate Limit ───────────────────────────────────────────────────

    async def check_rate_limit(
        self, user_id: str, action: str, max_calls: int, window: int = 60
    ) -> tuple[bool, int]:
        """检查速率限制。返回 (allowed, remaining)。"""
        redis = await self._ensure_conn()
        key = self._key("ratelimit", user_id, action)
        now = int(time.time())
        window_start = now - window

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)

        _, count, _, _ = await pipe.execute()

        allowed = int(count) < max_calls
        remaining = max(0, max_calls - int(count) - 1)
        return allowed, remaining

    # ── 嵌入缓存 ─────────────────────────────────────────────────────

    async def get_embedding_cache(self, text_hash: str) -> list[float] | None:
        redis = await self._ensure_conn()
        key = self._key("cache", "embedding", text_hash)
        data = await redis.get(key)
        if data is None:
            return None
        return self._deserialize(data)

    async def set_embedding_cache(
        self, text_hash: str, embedding: list[float], ttl: int | None = None
    ) -> None:
        redis = await self._ensure_conn()
        key = self._key("cache", "embedding", text_hash)
        await redis.setex(
            key, ttl or self.TTL_EMBEDDING_CACHE, self._serialize(embedding)
        )

    # ── 缓存统计与清理 ─────────────────────────────────────────────

    async def get_cache_stats(self) -> dict[str, int]:
        redis = await self._ensure_conn()
        info = await redis.info("keyspace")
        total_keys = 0
        for db_info in info.values():
            if isinstance(db_info, dict) and "keys" in db_info:
                total_keys += int(db_info["keys"])
        return {
            "total_keys": total_keys,
            "connected": self._connected,
            "db": self._db,
        }

    async def clear_all(self) -> int:
        """清除所有 Agent 相关缓存（仅当前 db）。"""
        redis = await self._ensure_conn()
        pattern = f"{self._key_prefix}:{self._env}:*"
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted += await redis.delete(*keys)
            if cursor == 0:
                break
        logger.info("RedisCache cleared %d keys", deleted)
        return deleted

    # ── 批量操作 ─────────────────────────────────────────────────────

    async def mget_as_dict(self, keys: list[str]) -> dict[str, Any]:
        redis = await self._ensure_conn()
        if not keys:
            return {}
        values = await redis.mget(keys)
        result = {}
        for k, v in zip(keys, values, strict=False):
            if v is not None:
                result[k] = self._deserialize(v)
        return result
