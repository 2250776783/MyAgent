"""文档加载核心实现。

将磁盘文件解析为结构化 Document 对象，支持单文件和目录批量加载。

文本格式（.txt, .md, .py, .json, .csv, .yaml, .html, .xml 等）直接读取，
复杂格式（.pdf, .docx, .pptx, .xlsx）尝试 unstructured 解析。
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 可以直接读取的纯文本扩展名
TEXT_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".yaml", ".yml",
                   ".html", ".htm", ".xml", ".js", ".ts", ".css", ".toml",
                   ".ini", ".cfg", ".conf", ".env", ".rst", ".tex",
                   ".log", ".svg"}


class LoaderError(Exception):
    pass


class Document:
    """系统中文档的标准表示。

    Args:
        content: 文档文本内容
        metadata: 文档元数据（文件名、文件路径等）
    """

    def __init__(self, content: str, metadata: dict | None = None) -> None:
        self.content = content
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"Document(content={self.content[:50]}..., metadata={self.metadata})"


class FileLoader:
    """单个文件的加载器。

    根据文件扩展名自动选择加载方式：纯文本直接读取，复杂格式走 unstructured。

    Args:
        file_path: 文件路径
        strategy: unstructured 分析策略（仅在复杂格式时生效）
    """

    def __init__(self, file_path: str | Path, strategy: str = "auto") -> None:
        self.file_path = Path(file_path)
        self.strategy = strategy

    def load(self) -> list[Document]:
        if not self.file_path.exists():
            raise FileNotFoundError(f"file not found: {self.file_path}")

        ext = self.file_path.suffix.lower()
        if ext in TEXT_EXTENSIONS:
            return self._load_text()
        return self._load_unstructured()

    def _load_text(self) -> list[Document]:
        try:
            content = self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = self.file_path.read_text(encoding="gbk")

        documents = []
        for block in content.strip().split("\n\n"):
            text = block.strip()
            if text:
                documents.append(Document(
                    content=text,
                    metadata={
                        "filename": self.file_path.name,
                        "file_path": str(self.file_path),
                        "file_type": "text",
                    },
                ))
        return documents if documents else [
            Document(content="", metadata={
                "filename": self.file_path.name,
                "file_path": str(self.file_path),
                "file_type": "text",
            })
        ]

    def _load_unstructured(self) -> list[Document]:
        try:
            from unstructured.partition.auto import partition
        except ImportError:
            raise LoaderError(
                "unstructured is required for this file type. "
                "Install it with: uv add unstructured"
            ) from None

        try:
            elements = partition(str(self.file_path), strategy=self.strategy)
        except Exception as e:
            raise LoaderError(
                f"failed to partition {self.file_path}: {e}"
            ) from e

        documents = []
        for element in elements:
            text = str(getattr(element, "text", "")).strip()
            if not text:
                continue
            metadata = dict(element.metadata.to_dict()) if element.metadata else {}
            metadata.setdefault("filename", self.file_path.name)
            metadata.setdefault("file_path", str(self.file_path))
            documents.append(Document(content=text, metadata=metadata))

        return documents


class DirectoryLoader:
    """目录下多文件的批量加载器。

    Args:
        directory: 目录路径
        glob_pattern: 文件匹配模式，默认为所有文件
    """

    def __init__(
        self, directory: str | Path, glob_pattern: str = "**/*"
    ) -> None:
        self.directory = Path(directory)
        self.glob_pattern = glob_pattern

    def load(self) -> list[Document]:
        if not self.directory.exists():
            raise FileNotFoundError(f"directory not found: {self.directory}")
        if not self.directory.is_dir():
            raise NotADirectoryError(f"not a directory: {self.directory}")

        all_documents: list[Document] = []
        for file_path in sorted(self.directory.glob(self.glob_pattern)):
            if not file_path.is_file():
                continue
            try:
                loader = FileLoader(file_path)
                docs = loader.load()
                all_documents.extend(docs)
                logger.info("loaded %d docs from %s", len(docs), file_path)
            except Exception as e:
                logger.warning("skipping %s: %s", file_path, e)

        return all_documents
