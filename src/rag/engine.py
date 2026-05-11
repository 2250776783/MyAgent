"""RAG 引擎。

编排完整的 RAG 流程：检索 → 增强（构建含上下文的 prompt）→ 生成。
"""

import logging

from src.llm import LLMClient, Message
from src.rag.loader import Document
from src.rag.retriever import Retriever

logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = (
    "你是一个问答助手。请使用以下上下文信息回答用户的问题。\n"
    "如果上下文信息不足以回答问题，请如实说明。\n"
    "引用来源时请注明对应的文档来源。\n\n"
    "上下文:\n"
    "---\n"
    "{context}\n"
    "---\n\n"
    "问题: {question}\n"
    "回答:"
)


class RAGEngine:
    """RAG 查询引擎。

    编排检索 → 增强 → 生成流程。

    Args:
        retriever: 检索器实例
        llm: LLM 客户端实例
        prompt_template: RAG prompt 模板
    """

    def __init__(
        self,
        retriever: Retriever,
        llm: LLMClient,
        prompt_template: str = RAG_PROMPT_TEMPLATE,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.prompt_template = prompt_template

    def query(
        self,
        question: str,
        k: int = 5,
        rerank_top_k: int = 3,
    ) -> str:
        """回答用户问题。

        Args:
            question: 用户问题
            k: 向量检索候选数
            rerank_top_k: 重排序保留数

        Returns:
            答案文本
        """
        docs = self.retriever.retrieve(question, k=k, rerank_top_k=rerank_top_k)
        answer, _ = self._generate(question, docs)
        return answer

    def query_with_sources(
        self,
        question: str,
        k: int = 5,
        rerank_top_k: int = 3,
    ) -> tuple[str, list[Document]]:
        """回答用户问题并返回来源文档。

        Args:
            question: 用户问题
            k: 向量检索候选数
            rerank_top_k: 重排序保留数

        Returns:
            (答案文本, 来源文档列表)
        """
        docs = self.retriever.retrieve(question, k=k, rerank_top_k=rerank_top_k)
        answer, sources = self._generate(question, docs)
        return answer, sources

    def _generate(
        self, question: str, docs: list[Document]
    ) -> tuple[str, list[Document]]:
        """根据问题和检索到的文档生成答案。"""
        if not docs:
            return (
                "我无法回答这个问题，因为知识库中没有找到相关信息。",
                [],
            )

        context = "\n---\n".join(d.content for d in docs)
        prompt = self.prompt_template.format(context=context, question=question)

        response = self.llm.chat([Message(role="user", content=prompt)])
        return response.content, docs
