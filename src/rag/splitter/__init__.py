"""文档切分器。

基于 langchain-text-splitters 将长文档切分为重叠的文本块，
保留原始元数据并添加切分来源信息。
"""

from .splitter import RecursiveCharacterSplitter, SplitterError

__all__ = ["RecursiveCharacterSplitter", "SplitterError"]
