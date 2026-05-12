"""RAG 知识库检索工具。

基于 RAGEngine 查询已摄入的知识库文档，返回检索增强生成的答案。
"""

from typing import Any

from src.agent.tools.base import (
    BaseTool,
    ToolOutput,
    ToolMetadata,
    BaseToolArgs,
    Field,
)
from src.rag.engine import RAGEngine


class RetrieverArgs(BaseToolArgs):
    """RAG 知识库查询参数。"""

    query: str = Field(description="查询问题，如「项目的核心功能是什么」")
    k: int = Field(default=5, description="向量检索候选文档数（默认 5）")
    rerank_top_k: int = Field(default=3, description="重排序后保留的文档数（默认 3）")


class RetrieverTool(BaseTool):
    """RAG 知识库检索工具。

    适用于已通过 ingest.py 导入数据到 ChromaDB 的知识库场景。
    基于向量检索 + 可选 LLM 重排序，从知识库中检索相关内容并生成答案。

    适用场景：
    - 查询已导入文档中的具体信息
    - 需要引用知识库来源的问答

    不适用场景：
    - 未导入文档时无法使用（返回空结果）
    - 实时信息查询（请使用 web_search）
    - 数学计算（请使用 calculator）

    Usage::

        from src.rag.engine import RAGEngine
        engine = RAGEngine(retriever=..., llm=...)
        tool = RetrieverTool(rag_engine=engine)
        result = tool.run(query="项目的核心功能是什么")
    """

    name: str = "retriever"
    description: str = (
        "查询知识库中的文档内容，返回检索增强生成的答案。"
        "传入 query 参数。需要先通过 ingest 导入文档。"
    )
    args_schema: type[RetrieverArgs] = RetrieverArgs
    metadata: ToolMetadata = ToolMetadata(
        readonly=True,
        destructive=False,
        category="rag",
    )

    def __init__(self, rag_engine: RAGEngine | None = None) -> None:
        super().__init__()
        self._engine = rag_engine

    def _run(self, query: str, k: int = 5, rerank_top_k: int = 3, **kwargs: Any) -> ToolOutput:
        if not query or not query.strip():
            return ToolOutput(success=False, error="查询内容不能为空")

        if not self._engine:
            return ToolOutput(
                success=False,
                error="RAG 引擎未初始化，请先通过 RetrieverTool(rag_engine=engine) 注入引擎实例",
            )

        try:
            answer = self._engine.query(question=query, k=k, rerank_top_k=rerank_top_k)
            return ToolOutput(success=True, output=answer)
        except Exception as e:
            return ToolOutput(success=False, error=f"知识库查询失败: {e}")
