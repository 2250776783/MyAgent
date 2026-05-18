"""Context Compression - 上下文压缩器。

多策略压缩：TRUNCATE / SUMMARIZE / STRUCTURED / DROP / MERGE。
当上下文窗口接近溢出时自动选择合适策略。
"""

from __future__ import annotations

import logging

from src.llm import LLMClient, Message, TokenCounter

from .types import (
    ContextSegment,
    ContextType,
    CompressionStrategy,
    InjectionPhase,
)

logger = logging.getLogger(__name__)


class ContextCompressor:
    """上下文压缩器。

    Args:
        llm: LLM 客户端（用于摘要压缩）
        token_counter: Token 计数器
    """

    def __init__(
        self,
        llm: LLMClient | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.llm = llm
        self.token_counter = token_counter or TokenCounter()

    def compress(
        self,
        segment: ContextSegment,
        strategy: CompressionStrategy,
        target_tokens: int | None = None,
    ) -> ContextSegment:
        if strategy == CompressionStrategy.TRUNCATE:
            return self._truncate(segment, target_tokens)
        elif strategy == CompressionStrategy.SUMMARIZE:
            return self._summarize(segment, target_tokens)
        elif strategy == CompressionStrategy.DROP:
            return self._drop(segment)
        return segment

    def compress_batch(
        self,
        segments: list[ContextSegment],
        total_budget: int,
    ) -> list[ContextSegment]:
        current_tokens = sum(self.token_counter.count(s.content) for s in segments)
        if current_tokens <= total_budget:
            return segments

        high = [s for s in segments if s.priority >= 0.8]
        mid = [s for s in segments if 0.4 <= s.priority < 0.8]
        low = [s for s in segments if s.priority < 0.4]

        result = list(high)

        for s in low:
            if self._count_total(result) < total_budget:
                result.append(s)

        for s in mid:
            if self._count_total(result) < total_budget:
                remaining = total_budget - self._count_total(result)
                result.append(self._truncate(s, remaining))
            else:
                break

        return result

    def _truncate(
        self, segment: ContextSegment, target_tokens: int | None
    ) -> ContextSegment:
        if target_tokens is None:
            target_tokens = self.token_counter.count(segment.content) // 2
        content = segment.content
        while self.token_counter.count(content) > target_tokens and len(content) > 100:
            content = content[:int(len(content) * 0.8)]
        return ContextSegment(
            id=segment.id + "_cmp",
            type=ContextType.COMPRESSED,
            content=content + "\n...(已压缩)",
            priority=segment.priority * 0.8,
            token_count=self.token_counter.count(content),
            source=segment.source,
            metadata={**segment.metadata, "compression": "truncate"},
            phase=InjectionPhase.MEMORY,
        )

    def _summarize(
        self, segment: ContextSegment, target_tokens: int | None = None
    ) -> ContextSegment:
        if not self.llm:
            return self._truncate(segment, target_tokens)
        content = segment.content
        if self.token_counter.count(content) < 200:
            return segment

        prompt = (
            f"请将以下内容压缩为简洁的摘要，保留所有关键信息。\n\n{content}"
        )
        try:
            response = self.llm.chat([Message(role="user", content=prompt)])
            compressed_text = response.content.strip()
            if not compressed_text:
                return self._truncate(segment, target_tokens)
            return ContextSegment(
                id=segment.id + "_sum",
                type=ContextType.COMPRESSED,
                content=compressed_text + "\n(摘要)",
                priority=segment.priority * 0.85,
                token_count=self.token_counter.count(compressed_text),
                source=segment.source,
                metadata={**segment.metadata, "compression": "summarize"},
                phase=InjectionPhase.MEMORY,
            )
        except Exception as e:
            logger.warning("Summarization failed: %s", e)
            return self._truncate(segment, target_tokens)

    def _drop(self, segment: ContextSegment) -> ContextSegment:
        return ContextSegment(
            id=segment.id + "_drop",
            type=ContextType.COMPRESSED,
            content="(已丢弃)",
            priority=0.0,
            token_count=0,
            source=segment.source,
            metadata={**segment.metadata, "compression": "drop"},
            phase=InjectionPhase.MEMORY,
        )

    def _count_total(self, segments: list[ContextSegment]) -> int:
        return sum(self.token_counter.count(s.content) for s in segments)
