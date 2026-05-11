"""文档加载器测试。"""

from pathlib import Path

import pytest

from src.rag.loader import Document, FileLoader, DirectoryLoader, LoaderError


class TestDocument:
    def test_basic(self):
        doc = Document("hello", {"file": "test.txt"})
        assert doc.content == "hello"
        assert doc.metadata == {"file": "test.txt"}

    def test_default_metadata(self):
        doc = Document("hello")
        assert doc.metadata == {}

    def test_repr(self):
        doc = Document("hello world", {"filename": "test.txt"})
        assert "test.txt" in repr(doc)


class TestFileLoader:
    def test_load_txt(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("line1\n\nline2", encoding="utf-8")
        docs = FileLoader(f).load()
        assert len(docs) >= 1
        assert any("line1" in d.content for d in docs)

    def test_load_md(self, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("# Title\n\ncontent", encoding="utf-8")
        docs = FileLoader(f).load()
        assert len(docs) >= 1

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileLoader("nonexistent.txt").load()


class TestDirectoryLoader:
    def test_load_directory(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("file a", encoding="utf-8")
        (tmp_path / "b.txt").write_text("file b", encoding="utf-8")
        docs = DirectoryLoader(tmp_path, "*.txt").load()
        assert len(docs) >= 2

    def test_glob_filter(self, tmp_path: Path):
        (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")
        (tmp_path / "skip.md").write_text("skip", encoding="utf-8")
        docs = DirectoryLoader(tmp_path, "*.txt").load()
        assert len(docs) >= 1
        assert all(d.metadata.get("filename") == "keep.txt" for d in docs)

    def test_directory_not_found(self):
        with pytest.raises(FileNotFoundError):
            DirectoryLoader("nonexistent").load()
