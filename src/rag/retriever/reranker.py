"""LLM 重排序器。

利用 LLM 对检索结果进行精排，提升相关文档的排序质量。
"""

import logging
import re

from src.llm import LLMClient, Message
from src.rag.loader import Document

logger = logging.getLogger(__name__)

RE_RANK_PROMPT = (
    "给定以下问题和候选段落，请根据相关性对段落进行排序。\n"
    "只返回最相关的前 {top_k} 个段落索引（从 0 开始），用逗号分隔，不要解释。\n\n"
    "问题: {query}\n\n"
    "段落:\n{passages}\n\n"
    "最相关的 {top_k} 个索引（逗号分隔）:"
)


class ReRanker:
    """基于 LLM 的检索结果重排序器。

    对向量检索返回的文档进行 LLM 相关性评估并重新排序。

    Args:
        llm_client: LLM 客户端实例
        top_k: 重排序后保留的结果数（默认 3）
    """

    def __init__(self, llm_client: LLMClient, top_k: int = 3) -> None:
        self.llm = llm_client
        self.top_k = top_k

    def rerank(self, query: str, documents: list[tuple[Document, float]]) -> list[Document]:
        """对检索结果进行重排序。

        Args:
            query: 原始查询
            documents: (Document, score) 列表

        Returns:
            重排序后的 Document 列表
        """
        if not documents:
            return []
        if len(documents) <= 1:
            return [d for d, _ in documents]

        passages_text = "\n".join(
            f"[{i}] {doc.content[:200]}"
            for i, (doc, _) in enumerate(documents)
        )

        prompt = RE_RANK_PROMPT.format(
            query=query,
            passages=passages_text,
            top_k=min(self.top_k, len(documents)),
        )

        try:
            response = self.llm.chat([Message(role="user", content=prompt)])
            indices = self._parse_indices(response.content, max_index=len(documents) - 1)
        except Exception as e:
            logger.warning("ReRank LLM call failed, falling back to vector scores: %s", e)
            indices = list(range(len(documents)))

        if not indices:
            indices = list(range(len(documents)))

        return [documents[i][0] for i in indices if i < len(documents)]

    def _parse_indices(self, content: str, max_index: int) -> list[int]:
        """解析 LLM 返回的索引列表。"""
        numbers = [int(n) for n in re.findall(r"\d+", content)]
        return [n for n in numbers if 0 <= n <= max_index][:self.top_k]
