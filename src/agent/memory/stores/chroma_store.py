"""ChromaDB 向量存储后端。

利用 ChromaDB 实现记忆的向量化存储和语义检索。
与 RAG 系统的 VectorStore 分离，使用独立的 collection。
"""

import logging
import uuid
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import settings

from ..types import MemoryItem
from .base import MemoryStore

logger = logging.getLogger(__name__)


class ChromaMemoryStore(MemoryStore):
    """基于 ChromaDB 的记忆存储。

    使用独立的 "memories" collection，与 RAG 文档存储分离。

    Args:
        collection_name: ChromaDB 集合名称
        persist_path: 持久化路径
    """

    def __init__(
        self,
        collection_name: str = "memories",
        persist_path: str | Path | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.persist_path = Path(persist_path or settings.chroma_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
        )

    def save(self, item: MemoryItem) -> str:
        memory_id = item.id or str(uuid.uuid4())
        embedding = item.embedding

        self._collection.add(
            ids=[memory_id],
            embeddings=[embedding] if embedding else None,  # type: ignore[arg-type]
            documents=[item.content],
            metadatas=[self._to_metadata(item)],
        )
        return memory_id

    def save_batch(self, items: list[MemoryItem]) -> list[str]:
        if not items:
            return []

        ids = [item.id or str(uuid.uuid4()) for item in items]
        embeddings = [item.embedding for item in items]
        has_all_embeddings = all(e is not None for e in embeddings)

        self._collection.add(
            ids=ids,
            embeddings=embeddings if has_all_embeddings else None,  # type: ignore[arg-type]
            documents=[item.content for item in items],
            metadatas=[self._to_metadata(item) for item in items],
        )
        return ids

    def get(self, memory_id: str) -> MemoryItem | None:
        results = self._collection.get(ids=[memory_id])
        if not results["ids"]:
            return None
        return self._from_result(results, 0)

    def search(self, query_embedding: list[float], k: int = 5) -> list[MemoryItem]:
        results = self._collection.query(
            query_embeddings=[query_embedding],  # type: ignore[arg-type]
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        if not results["ids"] or not results["ids"][0]:
            return []

        items: list[MemoryItem] = []
        for i in range(len(results["ids"][0])):
            item = self._from_result(results, i)
            if item:
                items.append(item)
        return items

    def delete(self, memory_id: str) -> None:
        self._collection.delete(ids=[memory_id])

    def update(self, memory_id: str, **updates) -> None:
        existing = self.get(memory_id)
        if not existing:
            return

        if "content" in updates:
            existing.content = updates["content"]
        if "importance" in updates:
            existing.importance = updates["importance"]
        if "access_count" in updates:
            existing.access_count = updates["access_count"]
        if "last_access" in updates:
            existing.last_access = updates["last_access"]

        self._collection.update(
            ids=[memory_id],
            documents=[existing.content],
            metadatas=[self._to_metadata(existing)],
        )

    def count(self) -> int:
        return self._collection.count()

    def get_all(self) -> list[MemoryItem]:
        results = self._collection.get(include=["documents", "metadatas"])
        if not results["ids"]:
            return []

        items: list[MemoryItem] = []
        for i in range(len(results["ids"])):
            item = self._from_result(results, i)
            if item:
                items.append(item)
        return items

    def _to_metadata(self, item: MemoryItem) -> dict[str, Any]:
        return {
            "memory_id": item.id,
            "type": item.type,
            "importance": str(item.importance),
            "timestamp": str(item.timestamp),
            "access_count": str(item.access_count),
            "last_access": str(item.last_access),
            "source_session": item.source_session or "",
        }

    def _from_result(self, results: Any, index: int) -> MemoryItem | None:
        try:
            meta = results["metadatas"][0][index] if results.get("metadatas") else {}
            return MemoryItem(
                id=results["ids"][0][index],
                content=results["documents"][0][index] if results.get("documents") else "",
                type=meta.get("type", "unknown"),
                importance=float(meta.get("importance", 0.5)),
                timestamp=float(meta.get("timestamp", 0)),
                access_count=int(meta.get("access_count", 0)),
                last_access=float(meta.get("last_access", 0)),
                source_session=meta.get("source_session") or None,
            )
        except (IndexError, TypeError, ValueError) as e:
            logger.warning("Failed to parse memory result: %s", e)
            return None
