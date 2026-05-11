"""向量化核心实现。

将文本转换为向量嵌入，支持单条和批量处理。
默认使用 OpenAI API 兼容的嵌入服务，可通过 settings 配置。
"""

import logging
from typing import Any

from openai import APIError, OpenAI
from openai.types import CreateEmbeddingResponse

from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    pass


class EmbeddingClient:
    """文本向量化客户端。

    封装 OpenAI API 兼容的嵌入服务调用。

    Args:
        api_key: API 密钥，默认从 settings 读取
        base_url: API 基础地址，默认从 settings 读取（自动补全 /v1）
        model: 嵌入模型名称，默认从 settings 读取
        batch_size: 批量嵌入时每批最大文本数（默认 20）
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        batch_size: int = 20,
    ) -> None:
        self.api_key = api_key or settings.embed_api_key or settings.llm_api_key
        raw_base_url = base_url or settings.embed_base_url or settings.llm_base_url
        self.base_url = (
            raw_base_url.rstrip("/")
            if raw_base_url.rstrip("/").endswith("/v1")
            else raw_base_url.rstrip("/") + "/v1"
        )
        self.model = model or settings.embed_model
        self.batch_size = batch_size

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def embed(self, text: str) -> list[float]:
        """将单条文本转换为向量。

        Args:
            text: 待嵌入的文本

        Returns:
            向量表示（float 列表）
        """
        if not text or not text.strip():
            return []

        data = self._embed_api([text])
        if not data:
            return []
        return data[0].embedding  # type: ignore[no-any-return]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量将文本转换为向量。

        自动按 batch_size 分片，每批调用一次 API。

        Args:
            texts: 待嵌入的文本列表

        Returns:
            向量列表，顺序与输入一致
        """
        if not texts:
            return []

        result: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            data = self._embed_api(batch)
            if data:
                result.extend(d.embedding for d in data)
        return result

    def _embed_api(self, texts: list[str]) -> list[Any]:
        """调用嵌入 API。

        Args:
            texts: 待嵌入的文本批次

        Returns:
            API 返回的嵌入数据对象列表
        """
        try:
            response: CreateEmbeddingResponse = self._client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return response.data
        except APIError as e:
            raise EmbeddingError(
                f"embedding API error: {e}"
            ) from e
