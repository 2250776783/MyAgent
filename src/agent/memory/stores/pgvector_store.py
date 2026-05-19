"""PostgreSQL + pgvector 异步存储后端。

基于 asyncpg 实现 PostgreSQL 异步连接池 + pgvector 向量检索。
兼容 pydantic-settings 的 PG_* 环境变量配置。

依赖:
    asyncpg>=0.30.0, psycopg[binary]>=3.2.0

用法::

    store = PGVectorMemoryStore()
    await store.connect()

    item = MemoryItem(id="...", content="hello", type="entity", ...)
    mid = await store.asave(item)

    results = await store.asearch(embedding, k=5)
    await store.aclose()
"""

import json
import logging
import uuid
from typing import Any

from src.config import settings

from ..types import MemoryItem
from .base import MemoryStore

logger = logging.getLogger(__name__)

try:
    import asyncpg
except ImportError:  # pragma: no cover
    asyncpg = None  # type: ignore[assignment]


class PGVectorMemoryStore(MemoryStore):
    """基于 PostgreSQL + pgvector 的异步记忆存储。

    使用 ``long_term_memory`` 表存储记忆并通过 pgvector 进行向量检索。
    同时提供会话、消息、摘要等辅助表的操作方法。

    Args:
        dsn: PostgreSQL DSN（含 asyncpg 驱动前缀），缺省从 settings 自动构建
        min_size: 连接池最小连接数
        max_size: 连接池最大连接数
        table_name: 记忆表名（需含 pgvector 的 embedding 列）
    """

    def __init__(
        self,
        dsn: str | None = None,
        min_size: int | None = None,
        max_size: int | None = None,
        table_name: str = "long_term_memory",
    ) -> None:
        if asyncpg is None:
            raise ImportError(
                "asyncpg is required. Install: uv add asyncpg"
            )

        self._dsn = dsn or settings.pg_dsn
        self._min_size = min_size or settings.pg_min_size
        self._max_size = max_size or settings.pg_max_size
        self._table = table_name
        self._pool: asyncpg.Pool | None = None

    # ── 连接池管理 ────────────────────────────────────────────────────

    async def connect(self) -> None:
        """初始化连接池。"""
        if self._pool is not None:
            return
        self._pool = await asyncpg.create_pool(
            dsn=self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            command_timeout=30,
        )
        logger.info(
            "PGVectorMemoryStore pool created (min=%d, max=%s)",
            self._min_size, self._max_size,
        )

    async def aclose(self) -> None:
        """关闭连接池。"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("PGVectorMemoryStore pool closed")

    @property
    def _connected(self) -> bool:
        return self._pool is not None

    async def _ensure_conn(self) -> asyncpg.Pool:
        if self._pool is None:
            await self.connect()
        assert self._pool is not None
        return self._pool

    # ── 核心 CRUD ─────────────────────────────────────────────────────

    async def asave(self, item: MemoryItem) -> str:
        mid = item.id or str(uuid.uuid4())
        pool = await self._ensure_conn()

        embedding = item.embedding
        embedding_str = f"[{','.join(str(v) for v in embedding)}]" if embedding else None

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self._table}
                    (id, content, memory_type, importance, access_count,
                     last_access_at, embedding, source_session, metadata,
                     created_at, updated_at)
                VALUES
                    ($1, $2, $3, $4, $5,
                     NOW(), $6::vector, $7, $8::jsonb,
                     to_timestamp($9), to_timestamp($9))
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    importance = EXCLUDED.importance,
                    access_count = EXCLUDED.access_count,
                    last_access_at = NOW(),
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """,
                mid,
                item.content,
                item.type,
                item.importance,
                item.access_count,
                embedding_str,
                item.source_session,
                json.dumps(item.metadata),
                item.timestamp,
            )
        return mid

    async def asave_batch(self, items: list[MemoryItem]) -> list[str]:
        if not items:
            return []
        pool = await self._ensure_conn()
        ids: list[str] = []

        async with pool.acquire() as conn:
            async with conn.transaction():
                for item in items:
                    mid = item.id or str(uuid.uuid4())
                    embedding = item.embedding
                    embedding_str = (
                        f"[{','.join(str(v) for v in embedding)}]"
                        if embedding else None
                    )
                    await conn.execute(
                        f"""
                        INSERT INTO {self._table}
                            (id, content, memory_type, importance, access_count,
                             last_access_at, embedding, source_session, metadata,
                             created_at, updated_at)
                        VALUES
                            ($1, $2, $3, $4, $5,
                             NOW(), $6::vector, $7, $8::jsonb,
                             to_timestamp($9), to_timestamp($9))
                        ON CONFLICT (id) DO NOTHING
                        """,
                        mid, item.content, item.type, item.importance,
                        item.access_count, embedding_str, item.source_session,
                        json.dumps(item.metadata), item.timestamp,
                    )
                    ids.append(mid)
        return ids

    async def aget(self, memory_id: str) -> MemoryItem | None:
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT id, content, memory_type, importance,
                       access_count, last_access_at,
                       embedding::text, source_session, metadata,
                       EXTRACT(EPOCH FROM created_at) as created_ts
                FROM {self._table}
                WHERE id = $1
                """,
                memory_id,
            )
        if row is None:
            return None
        return self._row_to_item(row)

    async def adelete(self, memory_id: str) -> None:
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {self._table} WHERE id = $1", memory_id
            )

    async def aupdate(self, memory_id: str, **updates) -> None:
        allowed = {"content", "importance", "access_count", "memory_type"}
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            return

        set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(fields))
        values = list(fields.values()) + [memory_id]

        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {self._table} SET {set_clause} WHERE id = ${len(fields)+1}",
                *values,
            )

    async def acount(self) -> int:
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchval(f"SELECT COUNT(*) FROM {self._table}")
        return row or 0

    async def aget_all(self) -> list[MemoryItem]:
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance,
                       access_count, last_access_at,
                       embedding::text, source_session, metadata,
                       EXTRACT(EPOCH FROM created_at) as created_ts
                FROM {self._table}
                ORDER BY created_at DESC
                """
            )
        return [self._row_to_item(r) for r in rows]

    # ── 向量检索 ──────────────────────────────────────────────────────

    async def asearch(
        self, query_embedding: list[float], k: int = 5
    ) -> list[MemoryItem]:
        """使用 pgvector 的 <=> 余弦距离进行向量相似度搜索。"""
        pool = await self._ensure_conn()
        embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance,
                       access_count, last_access_at,
                       embedding::text, source_session, metadata,
                       EXTRACT(EPOCH FROM created_at) as created_ts,
                       (embedding <=> $1::vector) as distance
                FROM {self._table}
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                embedding_str, k,
            )
        return [self._row_to_item(r) for r in rows]

    async def asearch_by_type(
        self, query_embedding: list[float], memory_type: str, k: int = 5
    ) -> list[MemoryItem]:
        """按记忆类型过滤的向量检索。"""
        pool = await self._ensure_conn()
        embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance,
                       access_count, last_access_at,
                       embedding::text, source_session, metadata,
                       EXTRACT(EPOCH FROM created_at) as created_ts
                FROM {self._table}
                WHERE embedding IS NOT NULL AND memory_type = $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                embedding_str, memory_type, k,
            )
        return [self._row_to_item(r) for r in rows]

    # ── 同步兼容 ──────────────────────────────────────────────────────

    def save(self, item: MemoryItem) -> str:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.asave(item)"
        )

    def get(self, memory_id: str) -> MemoryItem | None:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.aget(memory_id)"
        )

    def search(self, query_embedding: list[float], k: int = 5) -> list[MemoryItem]:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.asearch(...)"
        )

    def delete(self, memory_id: str) -> None:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.adelete(...)"
        )

    def update(self, memory_id: str, **updates) -> None:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.aupdate(...)"
        )

    def count(self) -> int:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.acount()"
        )

    def get_all(self) -> list[MemoryItem]:
        raise RuntimeError(
            "PGVectorMemoryStore is async-only. Use await store.aget_all()"
        )

    # ── 辅助方法：会话 / 消息 / 摘要 / Tool 调用 ─────────────────────

    async def save_session(
        self,
        session_id: str,
        user_id: str | None = None,
        title: str | None = None,
        status: str = "active",
        agent_id: str | None = None,
        session_data: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions
                    (id, user_id, title, status, agent_id,
                     session_data, metadata)
                VALUES
                    ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    session_data = EXCLUDED.session_data,
                    ended_at = CASE WHEN EXCLUDED.status = 'completed'
                                    THEN NOW() ELSE sessions.ended_at END
                """,
                session_id, user_id, title, status, agent_id,
                json.dumps(session_data or {}),
                json.dumps(metadata or {}),
            )

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: dict | None = None,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
        reasoning: str | None = None,
        token_count: int = 0,
        metadata: dict | None = None,
        trace_id: str | None = None,
    ) -> str:
        msg_id = str(uuid.uuid4())
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages
                    (id, session_id, role, content, tool_calls,
                     tool_call_id, tool_name, reasoning,
                     token_count, metadata, trace_id)
                VALUES
                    ($1, $2, $3, $4, $5::jsonb,
                     $6, $7, $8,
                     $9, $10::jsonb, $11)
                """,
                msg_id, session_id, role, content,
                json.dumps(tool_calls) if tool_calls else None,
                tool_call_id, tool_name, reasoning,
                token_count, json.dumps(metadata or {}), trace_id,
            )
            await conn.execute(
                "UPDATE sessions SET message_count = message_count + 1 WHERE id = $1",
                session_id,
            )
        return msg_id

    async def save_summary(
        self,
        session_id: str,
        summary_text: str,
        summary_type: str = "auto",
        importance: float = 0.5,
        embedding: list[float] | None = None,
        metadata: dict | None = None,
    ) -> str:
        sid = str(uuid.uuid4())
        embedding_str = (
            f"[{','.join(str(v) for v in embedding)}]" if embedding else None
        )
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_summary
                    (id, session_id, summary_text, summary_type,
                     importance, embedding, metadata)
                VALUES
                    ($1, $2, $3, $4, $5, $6::vector, $7::jsonb)
                """,
                sid, session_id, summary_text, summary_type,
                importance, embedding_str, json.dumps(metadata or {}),
            )
        return sid

    async def save_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_args: dict,
        status: str = "pending",
        tool_result: str | None = None,
        duration_ms: int | None = None,
        error_message: str | None = None,
        trace_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        tid = str(uuid.uuid4())
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tool_calls
                    (id, session_id, tool_name, tool_args, status,
                     tool_result, duration_ms, error_message, trace_id, metadata)
                VALUES
                    ($1, $2, $3, $4::jsonb, $5,
                     $6, $7, $8, $9, $10::jsonb)
                """,
                tid, session_id, tool_name, json.dumps(tool_args), status,
                tool_result, duration_ms, error_message, trace_id,
                json.dumps(metadata or {}),
            )
        return tid

    # ── 行转换 ────────────────────────────────────────────────────────

    def _row_to_item(self, row: asyncpg.Record) -> MemoryItem:
        embedding = None
        raw_emb = row.get("embedding")
        if raw_emb:
            try:
                cleaned = raw_emb.strip("[]")
                embedding = [float(v) for v in cleaned.split(",")] if cleaned else None
            except (ValueError, AttributeError):
                embedding = None

        metadata_raw = row.get("metadata")
        metadata: dict[str, Any] = {}
        if metadata_raw:
            if isinstance(metadata_raw, str):
                try:
                    metadata = json.loads(metadata_raw)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            elif isinstance(metadata_raw, dict):
                metadata = dict(metadata_raw)

        return MemoryItem(
            id=row["id"],
            content=row["content"],
            type=row["memory_type"],
            importance=self._to_float(row.get("importance"), 0.5),
            timestamp=self._to_float(row.get("created_ts"), 0.0),
            access_count=self._to_int(row.get("access_count"), 0),
            last_access=self._to_float(row.get("last_access_at"), 0.0),
            embedding=embedding,
            source_session=row.get("source_session"),
            metadata=metadata,
        )
