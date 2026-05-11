"""Token 计数器。

基于 tiktoken 计算文本和消息序列的 token 数量，
未安装 tiktoken 时自动降级为字符估算。
"""

import logging

logger = logging.getLogger(__name__)

try:
    import tiktoken

    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not installed, falling back to character-based approximation")


class TokenCounter:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._encoding = self._init_encoding()

    def _init_encoding(self) -> object:
        if not _TIKTOKEN_AVAILABLE:
            return None
        try:
            return tiktoken.encoding_for_model(self.model)
        except KeyError:
            try:
                return tiktoken.get_encoding("cl100k_base")
            except Exception:
                return None

    def count(self, text: str) -> int:
        encoding = self._encoding
        if encoding is not None:
            return len(encoding.encode(text))  # type: ignore[attr-defined]
        return len(text) // 4 + 1

    def count_messages(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += self.count(msg.get("content", ""))
            total += self.count(msg.get("role", ""))
        return total
