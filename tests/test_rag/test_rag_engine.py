"""RAGEngine 集成测试。

覆盖 RAGEngine 的 query、query_with_sources 和 _generate 方法。
"""

from unittest.mock import MagicMock

import pytest

from src.rag.loader import Document
from src.rag.engine import RAGEngine


class TestRAGEngine:
    """RAGEngine 单元测试。"""

    @pytest.fixture
    def mock_retriever(self) -> MagicMock:
        retriever = MagicMock()
        retriever.retrieve.return_value = [
            Document(content="RAG 是一种基于检索增强生成的技术。"),
            Document(content="它通过检索外部知识来增强 LLM 的回答。"),
        ]
        return retriever

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "RAG 是一种检索增强生成技术。"
        llm.chat.return_value = mock_response
        return llm

    def test_query_returns_answer(
        self, mock_retriever: MagicMock, mock_llm: MagicMock
    ) -> None:
        engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)
        answer = engine.query("什么是 RAG？")
        assert isinstance(answer, str)
        assert answer == "RAG 是一种检索增强生成技术。"

    def test_query_with_sources(
        self, mock_retriever: MagicMock, mock_llm: MagicMock
    ) -> None:
        engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)
        answer, sources = engine.query_with_sources("什么是 RAG？")
        assert answer == "RAG 是一种检索增强生成技术。"
        assert len(sources) == 2
        assert all(isinstance(s, Document) for s in sources)

    def test_no_documents_found(self, mock_llm: MagicMock) -> None:
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)
        answer, sources = engine._generate("test", [])
        assert "无法回答" in answer
        assert sources == []
        mock_llm.chat.assert_not_called()

    def test_empty_question(
        self, mock_retriever: MagicMock, mock_llm: MagicMock
    ) -> None:
        engine = RAGEngine(retriever=mock_retriever, llm=mock_llm)
        answer = engine.query("")
        assert isinstance(answer, str)

    def test_custom_prompt_template(self, mock_llm: MagicMock) -> None:
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            Document(content="some context"),
        ]
        template = "CONTEXT: {context}\nQ: {question}\nA:"
        engine = RAGEngine(
            retriever=mock_retriever, llm=mock_llm, prompt_template=template
        )
        engine.query("test")
        call_args = mock_llm.chat.call_args[0][0]
        assert call_args[0].content.startswith("CONTEXT:")
