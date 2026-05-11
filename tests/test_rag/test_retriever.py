"""Retriever 模块测试。

覆盖 VectorStore、ReRanker 和 Retriever 三个核心类。
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.rag.loader import Document
from src.rag.retriever import VectorStore, ReRanker, Retriever


class TestVectorStore:
    """VectorStore 单元测试。"""

    def test_init_creates_collection(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        assert store.count() == 0

    def test_add_documents(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        docs = [Document(content="hello"), Document(content="world")]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        store.add(docs, embeddings)
        assert store.count() == 2

    def test_add_empty(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        store.add([], [])
        assert store.count() == 0

    def test_add_mismatched_lengths_raises(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        docs = [Document(content="hello")]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        with pytest.raises(ValueError, match="same length"):
            store.add(docs, embeddings)

    def test_similarity_search(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        docs = [Document(content="hello world"), Document(content="goodbye world")]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        store.add(docs, embeddings)

        results = store.similarity_search([0.1, 0.2, 0.3], k=2)
        assert len(results) == 2
        assert isinstance(results[0], tuple)
        assert isinstance(results[0][0], Document)
        assert isinstance(results[0][1], float)

    def test_similarity_search_no_results(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        results = store.similarity_search([0.1, 0.2], k=5)
        assert results == []

    def test_count(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        assert store.count() == 0
        store.add([Document(content="hello")], [[0.1, 0.2]])
        assert store.count() == 1

    def test_delete_collection(self, tmp_path: Path) -> None:
        store = VectorStore(collection_name="test", persist_path=tmp_path)
        store.add([Document(content="hello")], [[0.1, 0.2]])
        assert store.count() == 1
        store.delete_collection()
        assert store.count() == 0


class TestReRanker:
    """ReRanker 单元测试。"""

    def test_empty_documents(self) -> None:
        reranker = ReRanker(llm_client=MagicMock())
        assert reranker.rerank("query", []) == []

    def test_single_document(self) -> None:
        reranker = ReRanker(llm_client=MagicMock())
        doc = Document(content="test")
        result = reranker.rerank("query", [(doc, 0.9)])
        assert result == [doc]

    def test_rerank_with_valid_response(self) -> None:
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "3, 1, 0"
        mock_llm.chat.return_value = mock_response

        reranker = ReRanker(llm_client=mock_llm, top_k=2)
        docs = [
            (Document(content="doc A"), 0.5),
            (Document(content="doc B"), 0.7),
            (Document(content="doc C"), 0.9),
            (Document(content="doc D"), 0.3),
        ]
        result = reranker.rerank("test query", docs)
        assert len(result) == 2
        assert result[0].content == "doc D"  # index 3
        assert result[1].content == "doc B"  # index 1

    def test_rerank_llm_failure_fallback(self) -> None:
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = Exception("API error")

        reranker = ReRanker(llm_client=mock_llm, top_k=2)
        docs = [
            (Document(content="doc A"), 0.5),
            (Document(content="doc B"), 0.7),
        ]
        result = reranker.rerank("test", docs)
        assert len(result) == 2
        assert result[0].content == "doc A"
        assert result[1].content == "doc B"

    def test_parse_indices(self) -> None:
        reranker = ReRanker(llm_client=MagicMock())
        assert reranker._parse_indices("3, 1, 0", max_index=5) == [3, 1, 0]
        assert reranker._parse_indices("0 2 5", max_index=5) == [0, 2, 5]
        assert reranker._parse_indices("invalid", max_index=5) == []
        assert reranker._parse_indices("", max_index=5) == []

    def test_parse_indices_out_of_range(self) -> None:
        reranker = ReRanker(llm_client=MagicMock())
        result = reranker._parse_indices("10, 1, 2", max_index=5)
        assert 10 not in result
        assert result == [1, 2]


class TestRetriever:
    """Retriever 单元测试。"""

    @pytest.fixture
    def mock_store(self) -> MagicMock:
        store = MagicMock()
        store.similarity_search.return_value = [
            (Document(content="doc A"), 0.9),
            (Document(content="doc B"), 0.7),
        ]
        return store

    @pytest.fixture
    def mock_embed(self) -> MagicMock:
        embed = MagicMock()
        embed.embed.return_value = [0.1, 0.2, 0.3]
        return embed

    def test_retrieve_with_results(
        self, mock_store: MagicMock, mock_embed: MagicMock
    ) -> None:
        retriever = Retriever(vector_store=mock_store, embed_client=mock_embed)
        docs = retriever.retrieve("test query", k=2)
        assert len(docs) == 2
        assert docs[0].content == "doc A"
        mock_embed.embed.assert_called_once_with("test query")
        mock_store.similarity_search.assert_called_once_with([0.1, 0.2, 0.3], k=2)

    def test_retrieve_no_embedding(self, mock_store: MagicMock) -> None:
        mock_embed = MagicMock()
        mock_embed.embed.return_value = []
        retriever = Retriever(vector_store=mock_store, embed_client=mock_embed)
        docs = retriever.retrieve("test query")
        assert docs == []

    def test_retrieve_with_reranker(
        self, mock_store: MagicMock, mock_embed: MagicMock
    ) -> None:
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [
            Document(content="reranked A"),
            Document(content="reranked B"),
        ]
        retriever = Retriever(
            vector_store=mock_store,
            embed_client=mock_embed,
            reranker=mock_reranker,
        )
        docs = retriever.retrieve("test query", k=2, rerank_top_k=2)
        assert len(docs) == 2
        assert docs[0].content == "reranked A"
        mock_reranker.rerank.assert_called_once()

    def test_retrieve_without_reranker(
        self, mock_store: MagicMock, mock_embed: MagicMock
    ) -> None:
        retriever = Retriever(vector_store=mock_store, embed_client=mock_embed)
        docs = retriever.retrieve("test query", k=2)
        assert len(docs) == 2
        assert docs[0].content == "doc A"
