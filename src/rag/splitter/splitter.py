"""文档切分核心实现。

将 Document 对象按递归字符策略切分为较小的重叠块，
保留父文档元数据并添加 chunk_index / chunk_total 追踪信息。
"""

import logging
from typing import Any

from src.rag.loader import Document

logger = logging.getLogger(__name__)


class SplitterError(Exception):
    pass


class RecursiveCharacterSplitter:
    """递归字符文本切分器。

    基于 langchain-text-splitters 的 RecursiveCharacterTextSplitter，
    按优先级从高到低的分隔符列表递归切分，保持段落和句子的完整性。

    Args:
        chunk_size: 每个块的目标字符数（默认 500）
        chunk_overlap: 块之间的重叠字符数（默认 50）
        separators: 分隔符优先级列表（默认按段落、行、句、词递进）
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ".", "?", "!", " ", ""]

    def split(self, documents: list[Document]) -> list[Document]:
        """将文档列表切分为更小的块。

        Args:
            documents: 待切分的文档列表

        Returns:
            切分后的文档块列表，每块继承父文档的元数据，
            并添加 chunk_index 和 chunk_total 字段
        """
        if not documents:
            return []

        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter as LcSplitter
        except ImportError:
            raise SplitterError(
                "langchain-text-splitters is required. "
                "Install it with: uv add langchain-text-splitters"
            ) from None

        lc_splitter = LcSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

        result: list[Document] = []
        for doc in documents:
            if not doc.content.strip():
                continue

            texts = lc_splitter.split_text(doc.content)
            chunk_total = len(texts)

            for i, text in enumerate(texts):
                if not text.strip():
                    continue
                metadata: dict[str, Any] = dict(doc.metadata)
                metadata["chunk_index"] = i
                metadata["chunk_total"] = chunk_total
                result.append(Document(content=text, metadata=metadata))

        return result
