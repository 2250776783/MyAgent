"""检索编排器。

整合向量搜索和可选的重排序，对外提供统一的检索接口。
"""

import logging

from src.rag.embed import EmbeddingClient
from src.rag.loader import Document
from src.rag.retriever.reranker import ReRanker
from src.rag.retriever.store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """检索编排器。

    编排搜索流程：嵌入查询 → 向量检索 → 可选重排序 → 返回结果。

    Args:
        vector_store: 向量存储实例
        embed_client: 嵌入客户端实例
        reranker: 可选的重排序器
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embed_client: EmbeddingClient,
        reranker: ReRanker | None = None,
    ) -> None:
        self.store = vector_store
        self.embed = embed_client
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
        k: int = 5,
        rerank_top_k: int = 3,
    ) -> list[Document]:
        """检索与查询相关的文档。

        Args:
            query: 查询文本
            k: 向量检索返回的候选数
            rerank_top_k: 重排序后保留的结果数

        Returns:
            相关文档列表
        """
        query_embedding = self.embed.embed(query)
        if not query_embedding:
            return []

        results = self.store.similarity_search(query_embedding, k=k)

        if self.reranker and len(results) > 1:
            self.reranker.top_k = rerank_top_k
            return self.reranker.rerank(query, results)

        return [doc for doc, _ in results]
