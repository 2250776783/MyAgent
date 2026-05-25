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
    同时提供会话、消息、摘要、工具调用、知识缓存、记忆链接、Agent 状态等辅助表的操作方法。

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

    def _embedding_to_str(self, embedding: list[float] | None) -> str | None:
        if embedding is None:
            return None
        return f"[{','.join(str(v) for v in embedding)}]"

    # ── 核心 CRUD：long_term_memory ───────────────────────────────────

    async def asave(self, item: MemoryItem) -> str:
        mid = item.id or str(uuid.uuid4())
        pool = await self._ensure_conn()
        embedding_str = self._embedding_to_str(item.embedding)

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self._table}
                    (id, content, memory_type, importance_score,
                     confidence_score, access_count, last_accessed_at,
                     decay_factor, reinforcement_count,
                     embedding, source_session, metadata,
                     created_at, updated_at)
                VALUES
                    ($1, $2, $3, $4, $5, $6, NOW(),
                     1.0, 0,
                     $7::vector, $8, $9::jsonb,
                     to_timestamp($10), to_timestamp($10))
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    importance_score = EXCLUDED.importance_score,
                    confidence_score = EXCLUDED.confidence_score,
                    access_count = EXCLUDED.access_count,
                    last_accessed_at = NOW(),
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """,
                mid,
                item.content,
                item.type,
                item.importance,
                0.7,
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
                    embedding_str = self._embedding_to_str(item.embedding)
                    await conn.execute(
                        f"""
                        INSERT INTO {self._table}
                            (id, content, memory_type, importance_score,
                             confidence_score, access_count, last_accessed_at,
                             decay_factor, reinforcement_count,
                             embedding, source_session, metadata,
                             created_at, updated_at)
                        VALUES
                            ($1, $2, $3, $4, $5, $6, NOW(),
                             1.0, 0,
                             $7::vector, $8, $9::jsonb,
                             to_timestamp($10), to_timestamp($10))
                        ON CONFLICT (id) DO NOTHING
                        """,
                        mid, item.content, item.type, item.importance,
                        0.7, item.access_count,
                        embedding_str, item.source_session,
                        json.dumps(item.metadata), item.timestamp,
                    )
                    ids.append(mid)
        return ids

    async def aget(self, memory_id: str) -> MemoryItem | None:
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT id, content, memory_type, importance_score,
                       confidence_score, access_count, last_accessed_at,
                       decay_factor, reinforcement_count,
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
        allowed = {"content", "importance_score", "confidence_score",
                   "access_count", "memory_type", "decay_factor",
                   "reinforcement_count"}
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
                SELECT id, content, memory_type, importance_score,
                       confidence_score, access_count, last_accessed_at,
                       decay_factor, reinforcement_count,
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
        embedding_str = self._embedding_to_str(query_embedding)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance_score,
                       confidence_score, access_count, last_accessed_at,
                       decay_factor, reinforcement_count,
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
        embedding_str = self._embedding_to_str(query_embedding)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance_score,
                       confidence_score, access_count, last_accessed_at,
                       decay_factor, reinforcement_count,
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

    async def asearch_by_importance(
        self, query_embedding: list[float], min_importance: float = 0.5, k: int = 5
    ) -> list[MemoryItem]:
        """按重要性阈值过滤的向量检索。"""
        pool = await self._ensure_conn()
        embedding_str = self._embedding_to_str(query_embedding)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance_score,
                       confidence_score, access_count, last_accessed_at,
                       decay_factor, reinforcement_count,
                       embedding::text, source_session, metadata,
                       EXTRACT(EPOCH FROM created_at) as created_ts
                FROM {self._table}
                WHERE embedding IS NOT NULL AND importance_score >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                embedding_str, min_importance, k,
            )
        return [self._row_to_item(r) for r in rows]

    async def asearch_hybrid(
        self, query_embedding: list[float], memory_type: str | None = None,
        min_importance: float = 0.0, k: int = 5,
    ) -> list[MemoryItem]:
        """混合检索：同时按类型和重要性过滤。"""
        pool = await self._ensure_conn()
        embedding_str = self._embedding_to_str(query_embedding)
        conditions = ["embedding IS NOT NULL"]
        params: list[Any] = [embedding_str]
        param_idx = 2

        if memory_type:
            conditions.append(f"memory_type = ${param_idx}")
            params.append(memory_type)
            param_idx += 1
        if min_importance > 0:
            conditions.append(f"importance_score >= ${param_idx}")
            params.append(min_importance)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        params.append(k)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, content, memory_type, importance_score,
                       confidence_score, access_count, last_accessed_at,
                       decay_factor, reinforcement_count,
                       embedding::text, source_session, metadata,
                       EXTRACT(EPOCH FROM created_at) as created_ts
                FROM {self._table}
                WHERE {where_clause}
                ORDER BY embedding <=> $1::vector
                LIMIT ${param_idx}
                """,
                *params,
            )
        return [self._row_to_item(r) for r in rows]

    # ── 记忆访问追踪 ──────────────────────────────────────────────────

    async def arecord_access(self, memory_id: str) -> None:
        """记录记忆访问（增加 access_count，更新 last_accessed_at）。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {self._table}
                SET access_count = access_count + 1,
                    last_accessed_at = NOW()
                WHERE id = $1
                """,
                memory_id,
            )

    async def areinforce_memory(self, memory_id: str) -> None:
        """强化记忆（增加 reinforcement_count，提升 confidence_score）。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {self._table}
                SET reinforcement_count = reinforcement_count + 1,
                    confidence_score = LEAST(confidence_score + 0.05, 1.0),
                    importance_score = LEAST(importance_score + 0.02, 1.0)
                WHERE id = $1
                """,
                memory_id,
            )

    async def adecay_memories(self, threshold: float = 0.3) -> int:
        """执行遗忘衰减，返回删除的记忆数。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {self._table}
                SET decay_factor = decay_factor * 0.9,
                    importance_score = importance_score * 0.95
                WHERE importance_score < 0.7
                """
            )
            result = await conn.execute(
                f"""
                DELETE FROM {self._table}
                WHERE decay_factor < $1
                   OR (importance_score < 0.1 AND access_count = 0)
                """,
                threshold,
            )
            parts = result.split()
            return int(parts[-1]) if parts else 0

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

    # ── 辅助方法：会话 ────────────────────────────────────────────────

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

    async def get_session(self, session_id: str) -> dict | None:
        """获取会话信息。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, title, status, agent_id,
                       session_data, metadata, message_count, token_count,
                       started_at, ended_at, created_at
                FROM sessions WHERE id = $1
                """,
                session_id,
            )
        if row is None:
            return None
        return dict(row)

    async def list_user_sessions(
        self, user_id: str, status: str | None = None, limit: int = 20
    ) -> list[dict]:
        """列出用户的会话。"""
        pool = await self._ensure_conn()
        if status:
            query = """
                SELECT id, title, status, message_count, token_count,
                       started_at, ended_at, created_at
                FROM sessions
                WHERE user_id = $1 AND status = $2
                ORDER BY created_at DESC LIMIT $3
            """
            params = [user_id, status, limit]
        else:
            query = """
                SELECT id, title, status, message_count, token_count,
                       started_at, ended_at, created_at
                FROM sessions
                WHERE user_id = $1
                ORDER BY created_at DESC LIMIT $2
            """
            params = [user_id, limit]

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]

    # ── 辅助方法：消息 ────────────────────────────────────────────────

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_index: int = 0,
        tool_calls: dict | None = None,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
        reasoning: str | None = None,
        token_count: int = 0,
        metadata: dict | None = None,
        trace_id: str | None = None,
        parent_msg_id: str | None = None,
    ) -> str:
        msg_id = str(uuid.uuid4())
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages
                    (id, session_id, message_index, role, content, tool_calls,
                     tool_call_id, tool_name, reasoning,
                     token_count, metadata, trace_id, parent_msg_id)
                VALUES
                    ($1, $2, $3, $4, $5, $6::jsonb,
                     $7, $8, $9,
                     $10, $11::jsonb, $12, $13)
                """,
                msg_id, session_id, message_index, role, content,
                json.dumps(tool_calls) if tool_calls else None,
                tool_call_id, tool_name, reasoning,
                token_count, json.dumps(metadata or {}), trace_id,
                parent_msg_id,
            )
            await conn.execute(
                "UPDATE sessions SET message_count = message_count + 1 WHERE id = $1",
                session_id,
            )
        return msg_id

    async def get_session_messages(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """按时间顺序获取会话消息。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, message_index, role, content, tool_calls,
                       tool_call_id, tool_name, reasoning,
                       token_count, trace_id, created_at
                FROM messages
                WHERE session_id = $1
                ORDER BY message_index ASC
                LIMIT $2 OFFSET $3
                """,
                session_id, limit, offset,
            )
        return [dict(r) for r in rows]

    # ── 辅助方法：摘要 ────────────────────────────────────────────────

    async def save_summary(
        self,
        session_id: str,
        summary_text: str,
        summary_type: str = "auto",
        importance: float = 0.5,
        message_start: int | None = None,
        message_end: int | None = None,
        embedding: list[float] | None = None,
        metadata: dict | None = None,
    ) -> str:
        sid = str(uuid.uuid4())
        embedding_str = self._embedding_to_str(embedding)
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_summary
                    (id, session_id, summary_text, summary_type,
                     importance, message_start, message_end,
                     embedding, metadata)
                VALUES
                    ($1, $2, $3, $4, $5, $6, $7, $8::vector, $9::jsonb)
                """,
                sid, session_id, summary_text, summary_type,
                importance, message_start, message_end,
                embedding_str, json.dumps(metadata or {}),
            )
        return sid

    async def get_session_summaries(self, session_id: str) -> list[dict]:
        """获取会话的所有摘要。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, summary_text, summary_type, importance,
                       message_start, message_end, token_count, created_at
                FROM conversation_summary
                WHERE session_id = $1
                ORDER BY created_at DESC
                """,
                session_id,
            )
        return [dict(r) for r in rows]

    # ── 辅助方法：工具调用 ────────────────────────────────────────────

    async def save_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_args: dict,
        status: str = "pending",
        tool_result: str | None = None,
        duration_ms: int | None = None,
        retry_count: int = 0,
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
                     tool_result, duration_ms, retry_count,
                     error_message, trace_id, metadata)
                VALUES
                    ($1, $2, $3, $4::jsonb, $5,
                     $6, $7, $8, $9, $10, $11::jsonb)
                """,
                tid, session_id, tool_name, json.dumps(tool_args), status,
                tool_result, duration_ms, retry_count,
                error_message, trace_id, json.dumps(metadata or {}),
            )
        return tid

    async def get_session_tool_calls(self, session_id: str) -> list[dict]:
        """获取会话的所有工具调用。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, tool_name, tool_args, tool_result, status,
                       duration_ms, retry_count, error_message,
                       trace_id, created_at
                FROM tool_calls
                WHERE session_id = $1
                ORDER BY created_at ASC
                """,
                session_id,
            )
        return [dict(r) for r in rows]

    async def get_tool_stats(self, tool_name: str | None = None) -> list[dict]:
        """获取工具调用统计。"""
        pool = await self._ensure_conn()
        if tool_name:
            query = """
                SELECT tool_name,
                       COUNT(*) AS total_calls,
                       COUNT(*) FILTER (WHERE status = 'success') AS success_count,
                       AVG(duration_ms)::INTEGER AS avg_duration_ms,
                       SUM(retry_count)::INTEGER AS total_retries
                FROM tool_calls
                WHERE tool_name = $1
                GROUP BY tool_name
            """
            params = [tool_name]
        else:
            query = """
                SELECT tool_name,
                       COUNT(*) AS total_calls,
                       COUNT(*) FILTER (WHERE status = 'success') AS success_count,
                       AVG(duration_ms)::INTEGER AS avg_duration_ms,
                       SUM(retry_count)::INTEGER AS total_retries
                FROM tool_calls
                GROUP BY tool_name
                ORDER BY total_calls DESC
            """
            params = []

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]

    # ── 辅助方法：知识缓存 ────────────────────────────────────────────

    async def save_knowledge_cache(
        self,
        query_text: str,
        result_text: str,
        query_embedding: list[float] | None = None,
        source_docs: list[dict] | None = None,
        token_count: int = 0,
        ttl_seconds: int | None = None,
        metadata: dict | None = None,
    ) -> str:
        """保存 RAG 检索缓存。"""
        import hashlib
        cid = str(uuid.uuid4())
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()
        embedding_str = self._embedding_to_str(query_embedding)
        expires_at = None
        if ttl_seconds:
            pool = await self._ensure_conn()
            async with pool.acquire() as conn:
                expires_at = await conn.fetchval(
                    "SELECT NOW() + $1::INTERVAL", f"{ttl_seconds} seconds"
                )

        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO knowledge_cache
                    (id, query_hash, query_text, query_embedding,
                     result_text, source_docs, token_count,
                     expires_at, metadata)
                VALUES
                    ($1, $2, $3, $4::vector,
                     $5, $6::jsonb, $7,
                     $8, $9::jsonb)
                ON CONFLICT (query_hash) DO UPDATE SET
                    hit_count = knowledge_cache.hit_count + 1,
                    result_text = EXCLUDED.result_text,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
                """,
                cid, query_hash, query_text, embedding_str,
                result_text, json.dumps(source_docs or []), token_count,
                expires_at, json.dumps(metadata or {}),
            )
        return cid

    async def get_knowledge_cache(self, query_text: str) -> dict | None:
        """通过 query_hash 精确匹配缓存。"""
        import hashlib
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, query_text, result_text, source_docs,
                       token_count, hit_count, created_at
                FROM knowledge_cache
                WHERE query_hash = $1
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                query_hash,
            )
        if row is None:
            return None
        return dict(row)

    async def search_knowledge_cache(
        self, query_embedding: list[float], threshold: float = 0.85, k: int = 3
    ) -> list[dict]:
        """语义近似匹配缓存。"""
        pool = await self._ensure_conn()
        embedding_str = self._embedding_to_str(query_embedding)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, query_text, result_text, source_docs,
                       token_count, hit_count,
                       1 - (query_embedding <=> $1::vector) AS similarity
                FROM knowledge_cache
                WHERE query_embedding IS NOT NULL
                  AND (expires_at IS NULL OR expires_at > NOW())
                  AND 1 - (query_embedding <=> $1::vector) >= $2
                ORDER BY query_embedding <=> $1::vector
                LIMIT $3
                """,
                embedding_str, threshold, k,
            )
        return [dict(r) for r in rows]

    # ── 辅助方法：记忆链接 ────────────────────────────────────────────

    async def save_memory_link(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        strength: float = 1.0,
        metadata: dict | None = None,
    ) -> str:
        """创建记忆关联。"""
        lid = str(uuid.uuid4())
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO memory_links
                    (id, source_id, target_id, relation_type, strength, metadata)
                VALUES
                    ($1, $2, $3, $4, $5, $6::jsonb)
                ON CONFLICT (source_id, target_id, relation_type)
                DO UPDATE SET strength = EXCLUDED.strength
                """,
                lid, source_id, target_id, relation_type, strength,
                json.dumps(metadata or {}),
            )
        return lid

    async def get_memory_links(
        self, memory_id: str, depth: int = 1
    ) -> list[dict]:
        """获取记忆的关联（BFS 遍历 depth 层）。"""
        pool = await self._ensure_conn()
        if depth <= 1:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, source_id, target_id, relation_type, strength
                    FROM memory_links
                    WHERE source_id = $1 OR target_id = $1
                    ORDER BY strength DESC
                    """,
                    memory_id,
                )
            return [dict(r) for r in rows]

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH RECURSIVE link_graph AS (
                    SELECT id, source_id, target_id, relation_type, strength, 1 AS hop
                    FROM memory_links
                    WHERE source_id = $1 OR target_id = $1
                    UNION
                    SELECT ml.id, ml.source_id, ml.target_id,
                           ml.relation_type, ml.strength, lg.hop + 1
                    FROM memory_links ml
                    INNER JOIN link_graph lg
                        ON (lg.target_id = ml.source_id OR lg.source_id = ml.target_id)
                        AND lg.hop < $2
                )
                SELECT DISTINCT id, source_id, target_id, relation_type,
                                strength, hop
                FROM link_graph
                ORDER BY hop, strength DESC
                LIMIT 50
                """,
                memory_id, depth,
            )
        return [dict(r) for r in rows]

    # ── 辅助方法：Agent 状态 ──────────────────────────────────────────

    async def save_agent_state(
        self,
        agent_id: str,
        session_id: str,
        state_type: str,
        state_data: dict,
        user_id: str | None = None,
        token_count: int = 0,
        metadata: dict | None = None,
        ttl_seconds: int | None = None,
    ) -> str:
        """持久化 Agent 状态。"""
        sid = str(uuid.uuid4())
        pool = await self._ensure_conn()
        expires_at = None
        if ttl_seconds:
            async with pool.acquire() as conn:
                expires_at = await conn.fetchval(
                    "SELECT NOW() + $1::INTERVAL", f"{ttl_seconds} seconds"
                )

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_states
                    (id, agent_id, session_id, user_id,
                     state_type, state_data, token_count,
                     metadata, expires_at)
                VALUES
                    ($1, $2, $3, $4, $5, $6::jsonb, $7,
                     $8::jsonb, $9)
                """,
                sid, agent_id, session_id, user_id,
                state_type, json.dumps(state_data), token_count,
                json.dumps(metadata or {}), expires_at,
            )
        return sid

    async def get_latest_agent_state(
        self, agent_id: str, session_id: str, state_type: str
    ) -> dict | None:
        """获取最新的 Agent 状态。"""
        pool = await self._ensure_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, state_data, token_count, metadata, created_at
                FROM agent_states
                WHERE agent_id = $1 AND session_id = $2 AND state_type = $3
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY created_at DESC
                LIMIT 1
                """,
                agent_id, session_id, state_type,
            )
        if row is None:
            return None
        return dict(row)

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

        importance = row.get("importance_score") or row.get("importance") or 0.5
        if isinstance(importance, str):
            try:
                importance = float(importance)
            except (ValueError, TypeError):
                importance = 0.5

        return MemoryItem(
            id=row["id"],
            content=row["content"],
            type=row["memory_type"],
            importance=self._to_float(importance, 0.5),
            timestamp=self._to_float(row.get("created_ts"), 0.0),
            access_count=self._to_int(row.get("access_count"), 0),
            last_access=self._to_float(row.get("last_accessed_at"), 0.0),
            embedding=embedding,
            source_session=row.get("source_session"),
            metadata=metadata,
        )

    @staticmethod
    def _to_float(val: Any, default: float) -> float:
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _to_int(val: Any, default: int) -> int:
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
