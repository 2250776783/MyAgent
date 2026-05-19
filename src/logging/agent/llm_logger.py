"""LLM 交互日志器 — 请求/响应/流式/错误。

记录与 LLM 的所有交互，包括提示词、响应、token 用量和延迟。
"""

import time
from typing import Any

from src.logging.adapter import LoggerAdapter
from src.logging.constants import EventType


class LLMLogger:
    """LLM 交互日志器。

    用法::

        llm_logger = LLMLogger(adapter)
        llm_logger.prompt("deepseek-chat", messages, tools=[...])
        # ... LLM 调用 ...
        llm_logger.response("deepseek-chat", "北京天气...", prompt_tokens=50, completion_tokens=100, latency_ms=1200)
    """

    def __init__(self, adapter: LoggerAdapter) -> None:
        self._adapter = adapter

    def prompt(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        **extra: Any,
    ) -> None:
        """记录 LLM 请求。"""
        self._adapter.info(
            EventType.LLM_PROMPT,
            f"LLM 请求 → {model}",
            model=model,
            messages=messages,
            tools=tools,
            **extra,
        )

    def response(
        self,
        model: str,
        content_preview: str,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        latency_ms: float | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        **extra: Any,
    ) -> None:
        """记录 LLM 响应。"""
        self._adapter.info(
            EventType.LLM_RESPONSE,
            f"LLM 响应 ← {model}",
            model=model,
            content_preview=content_preview[:500],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            **extra,
        )

    def stream_token(self, model: str, token: str, **extra: Any) -> None:
        """记录流式 token（可按需启用）。"""
        self._adapter.debug(
            EventType.LLM_STREAM,
            token,
            model=model,
            **extra,
        )

    def error(
        self,
        model: str,
        error_msg: str,
        *,
        prompt_tokens: int | None = None,
        latency_ms: float | None = None,
        **extra: Any,
    ) -> None:
        """记录 LLM 错误。"""
        self._adapter.error(
            EventType.LLM_ERROR,
            f"LLM 错误: {error_msg}",
            exception=error_msg,
            model=model,
            prompt_tokens=prompt_tokens,
            latency_ms=latency_ms,
            **extra,
        )

    @classmethod
    def duration_ms(cls, start: float) -> float:
        """计算耗时。"""
        return (time.monotonic() - start) * 1000
