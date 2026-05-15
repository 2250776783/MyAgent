"""SQLite 结构化存储后端。

存储实体知识、会话记录、反思结果等结构化记忆。
支持按类型和重要性过滤检索。
"""

import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from ..types import MemoryItem
from .base import MemoryStore

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    type TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    timestamp REAL NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_access REAL DEFAULT 0,
    source_session TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    summary TEXT,
    message_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    importance REAL DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS reflections (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    reflection_type TEXT NOT NULL,
    source_ids TEXT DEFAULT '[]',
    importance REAL DEFAULT 0.5,
    timestamp REAL NOT NULL
);
"""


class SQLMemoryStore(MemoryStore):
    """基于 SQLite 的结构化记忆存储。

    存储实体、偏好、会话摘要等结构化的记忆数据，
    与 ChromaMemoryStore 配合使用（SQLite 存结构化数据，ChromaDB 存向量）。

    Args:
        db_path: SQLite 数据库文件路径
    """

    def __init__(self, db_path: str | Path = "memory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript(_SCHEMA)
        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def save(self, item: MemoryItem) -> str:
        memory_id = item.id or str(uuid.uuid4())
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, content, type, importance, timestamp, access_count, last_access, source_session, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory_id,
                item.content,
                item.type,
                item.importance,
                item.timestamp,
                item.access_count,
                item.last_access,
                item.source_session,
                json.dumps(item.metadata),
            ),
        )
        conn.commit()
        return memory_id

    def save_batch(self, items: list[MemoryItem]) -> list[str]:
        conn = self._get_conn()
        ids = []
        for item in items:
            mid = item.id or str(uuid.uuid4())
            ids.append(mid)
            conn.execute(
                """INSERT OR REPLACE INTO memories
                   (id, content, type, importance, timestamp, access_count, last_access, source_session, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mid,
                    item.content,
                    item.type,
                    item.importance,
                    item.timestamp,
                    item.access_count,
                    item.last_access,
                    item.source_session,
                    json.dumps(item.metadata),
                ),
            )
        conn.commit()
        return ids

    def get(self, memory_id: str) -> MemoryItem | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return self._row_to_item(row) if row else None

    def search(self, query_embedding: list[float], k: int = 5) -> list[MemoryItem]:
        """SQLite 不支持向量检索，返回最近 k 条记忆作为 fallback。"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?", (k,)
        ).fetchall()
        return [self._row_to_item(r) for r in rows if r]

    def delete(self, memory_id: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()

    def update(self, memory_id: str, **updates) -> None:
        allowed = {"content", "importance", "access_count", "last_access", "type", "metadata"}
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            return

        if "metadata" in fields:
            fields["metadata"] = json.dumps(fields["metadata"])

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [memory_id]

        conn = self._get_conn()
        conn.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", values)
        conn.commit()

    def count(self) -> int:
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
        return row["cnt"] if row else 0

    def get_all(self) -> list[MemoryItem]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM memories ORDER BY timestamp DESC").fetchall()
        return [self._row_to_item(r) for r in rows if r]

    def filter_by_type(self, memory_type: str, limit: int = 50) -> list[MemoryItem]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM memories WHERE type = ? ORDER BY importance DESC LIMIT ?",
            (memory_type, limit),
        ).fetchall()
        return [self._row_to_item(r) for r in rows if r]

    def get_unreflected_memories(self, since_timestamp: float, limit: int = 50) -> list[MemoryItem]:
        """获取指定时间戳之后的新记忆（尚未被反思的）。"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM memories WHERE timestamp > ? ORDER BY importance DESC LIMIT ?",
            (since_timestamp, limit),
        ).fetchall()
        return [self._row_to_item(r) for r in rows if r]

    # 会话管理 ---------------------------------------------------------------

    def save_session(self, session_id: str, summary: str, message_count: int,
                     token_count: int, start_time: float, end_time: float,
                     importance: float = 0.5) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (id, summary, message_count, token_count, start_time, end_time, importance)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, summary, message_count, token_count, start_time, end_time, importance),
        )
        conn.commit()

    def get_recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY end_time DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # 反思管理 ---------------------------------------------------------------

    def save_reflection(self, content: str, reflection_type: str,
                        source_ids: list[str], importance: float = 0.5) -> str:
        rid = str(uuid.uuid4())
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO reflections
               (id, content, reflection_type, source_ids, importance, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (rid, content, reflection_type, json.dumps(source_ids), importance, time.time()),
        )
        conn.commit()
        return rid

    def get_recent_reflections(self, limit: int = 10) -> list[dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM reflections ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            content=row["content"],
            type=row["type"],
            importance=row["importance"],
            timestamp=row["timestamp"],
            access_count=row["access_count"],
            last_access=row["last_access"],
            source_session=row["source_session"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
