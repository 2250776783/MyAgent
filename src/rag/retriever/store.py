"""向量存储封装。

基于 ChromaDB PersistentClient 实现，将文档和嵌入向量持久化到本地磁盘。
"""

import logging
import uuid
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.rag.loader import Document

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB 向量存储封装。

    支持文档增删查和相似度搜索，数据持久化到磁盘。

    Args:
        collection_name: 集合名称（默认 "documents"）
        persist_path: 持久化路径，默认从 settings 读取
    """

    def __init__(
        self,
        collection_name: str = "documents",
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

    def add(self, documents: list[Document], embeddings: list[list[float]]) -> None:
        """添加文档及其嵌入向量到存储。

        Args:
            documents: 文档列表
            embeddings: 对应的嵌入向量列表
        """
        if not documents or not embeddings:
            return
        if len(documents) != len(embeddings):
            raise ValueError("documents and embeddings must have same length")

        ids = [str(uuid.uuid4()) for _ in documents]
        texts = [d.content for d in documents]
        metadatas: list[dict[str, Any] | None] = [
            dict(d.metadata) if d.metadata else None for d in documents
        ]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,  # type: ignore[arg-type]
            documents=texts,
            metadatas=metadatas,  # type: ignore[arg-type]
        )

    def similarity_search(
        self, query_embedding: list[float], k: int = 5
    ) -> list[tuple[Document, float]]:
        """按查询向量进行相似度搜索。

        Args:
            query_embedding: 查询向量
            k: 返回结果数量

        Returns:
            (Document, 相似度分数) 列表
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],  # type: ignore[arg-type]
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        documents: list[tuple[Document, float]] = []
        for i, text in enumerate(results["documents"][0]):
            metadata: dict = {}
            if results["metadatas"] and results["metadatas"][0]:
                raw = results["metadatas"][0][i] or {}
                if isinstance(raw, dict):
                    metadata = raw
            distance = results["distances"][0][i] if results["distances"] else 0.0
            score = 1.0 - distance  # ChromaDB returns L2 distance, convert to similarity
            documents.append(
                (Document(content=text, metadata=dict(metadata)), score)
            )

        return documents

    def count(self) -> int:
        """返回存储中的文档总数。"""
        return self._collection.count()

    def delete_collection(self) -> None:
        """删除当前集合。"""
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
        )
