"""向量化嵌入模块。

基于 OpenAI API 兼容的嵌入服务，将文本转换为向量表示，
支持单条和批量嵌入两种模式。
"""

from .embedder import EmbeddingClient, EmbeddingError

__all__ = ["EmbeddingClient", "EmbeddingError"]
