"""向量化模块测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.rag.embed import EmbeddingClient, EmbeddingError


class FakeEmbeddingData:
    def __init__(self, embedding: list[float]):
        self.embedding = embedding


class TestEmbeddingClient:
    def test_embed_returns_vector(self):
        client = EmbeddingClient(api_key="test", base_url="http://localhost:9999/v1")
        assert hasattr(client, "embed")
        assert hasattr(client, "embed_batch")

    def test_empty_text(self):
        client = EmbeddingClient(api_key="test", base_url="http://localhost:9999/v1")
        assert client.embed("") == []
        assert client.embed("   ") == []

    def test_empty_batch(self):
        client = EmbeddingClient(api_key="test", base_url="http://localhost:9999/v1")
        assert client.embed_batch([]) == []

    def test_embed_batch_single(self):
        client = EmbeddingClient(api_key="test", base_url="http://localhost:9999/v1")
        client._embed_api = MagicMock(return_value=[FakeEmbeddingData([0.1, 0.2, 0.3])])
        result = client.embed_batch(["text"])
        assert result == [[0.1, 0.2, 0.3]]

    def test_model_config(self):
        client = EmbeddingClient(
            api_key="test",
            base_url="http://localhost:11434/v1",
            model="bge-m3",
        )
        assert client.model == "bge-m3"
        assert "localhost" in client.base_url
