"""存储后端实现。

支持三种后端：
- ChromaMemoryStore           — ChromaDB 向量存储（同步）
- SQLMemoryStore              — SQLite 结构化存储（同步）
- PGVectorMemoryStore         — PostgreSQL + pgvector（异步，推荐）

迁移路径：ChromaDB/SQLite → 推荐使用 PGVectorMemoryStore
"""

from .base import MemoryStore
from .chroma_store import ChromaMemoryStore
from .sql_store import SQLMemoryStore

try:
    from .pgvector_store import PGVectorMemoryStore
except ImportError:
    PGVectorMemoryStore = None  # type: ignore[assignment,misc]

__all__ = [
    "MemoryStore",
    "ChromaMemoryStore",
    "SQLMemoryStore",
    "PGVectorMemoryStore",
]
