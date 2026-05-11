"""文档切分器测试。"""

import pytest

from src.rag.loader import Document
from src.rag.splitter import RecursiveCharacterSplitter, SplitterError


class TestRecursiveCharacterSplitter:
    def test_short_document(self):
        doc = Document("short text", {"source": "test"})
        splitter = RecursiveCharacterSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split([doc])
        assert len(chunks) == 1
        assert chunks[0].content == "short text"
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[0].metadata["chunk_total"] == 1
        assert chunks[0].metadata["source"] == "test"

    def test_long_document_split(self):
        content = "word " * 200
        doc = Document(content, {"source": "test"})
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        chunks = splitter.split([doc])
        assert len(chunks) > 1

    def test_chunk_overlap(self):
        content = "A long paragraph that goes on and on with enough text.\n\n" * 10
        doc = Document(content)
        splitter = RecursiveCharacterSplitter(chunk_size=50, chunk_overlap=20)
        chunks = splitter.split([doc])
        assert len(chunks) > 1

    def test_metadata_preserved(self):
        doc = Document("long content " * 50, {"filename": "test.txt", "page": 1})
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        chunks = splitter.split([doc])
        for c in chunks:
            assert c.metadata["filename"] == "test.txt"
            assert c.metadata["page"] == 1

    def test_empty_documents(self):
        splitter = RecursiveCharacterSplitter()
        assert splitter.split([]) == []

    def test_empty_content(self):
        doc = Document("  ", {"source": "empty"})
        splitter = RecursiveCharacterSplitter()
        chunks = splitter.split([doc])
        assert chunks == []

    def test_invalid_chunk_size(self):
        with pytest.raises(ValueError, match="chunk_size"):
            RecursiveCharacterSplitter(chunk_size=0)

    def test_invalid_overlap(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            RecursiveCharacterSplitter(chunk_overlap=10, chunk_size=5)

    def test_multiple_documents(self):
        docs = [Document("A " * 30), Document("B " * 30)]
        splitter = RecursiveCharacterSplitter(chunk_size=20, chunk_overlap=5)
        chunks = splitter.split(docs)
        assert len(chunks) > 2
