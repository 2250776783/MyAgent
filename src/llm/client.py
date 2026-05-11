"""LLM API 调用封装。

提供 LLMClient 类，统一封装 OpenAI API 兼容的聊天完成调用，
支持同步、流式两种模式，内置指数退避重试机制，以及 tool calling。
"""

import logging
import time
from collections.abc import Generator
from typing import Any

from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from src.config import settings
from src.llm.types import Message

logger = logging.getLogger(__name__)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key or settings.llm_api_key
        raw_base_url = base_url or settings.llm_base_url
        self.base_url = (
            raw_base_url.rstrip("/")
            if raw_base_url.rstrip("/").endswith("/v1")
            else raw_base_url.rstrip("/") + "/v1"
        )
        self.model = model or settings.llm_model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        """调用 LLM 聊天完成 API，可选传入工具定义。"""
        if not messages:
            raise ValueError("messages must not be empty")

        dict_messages = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": dict_messages,  # type: ignore[arg-type]
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self._client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                msg = choice.message
                result = Message(role=msg.role or "assistant", content=msg.content or "")
                if msg.tool_calls:
                    result.tool_calls = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                return result
            except (APIError, APITimeoutError, RateLimitError) as e:
                last_error = e
                logger.warning(
                    "LLM API error (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))

        raise LLMError(
            f"LLM call failed after {self.max_retries} retries"
        ) from last_error

    def chat_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
    ) -> Generator[Message, None, None]:
        if not messages:
            raise ValueError("messages must not be empty")

        dict_messages = [m.to_dict() for m in messages]
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                stream = self._client.chat.completions.create(
                    model=self.model,
                    messages=dict_messages,  # type: ignore[arg-type]
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None  # type: ignore[union-attr]
                    if delta and delta.content:
                        yield Message(role="assistant", content=delta.content)
                return
            except (APIError, APITimeoutError, RateLimitError) as e:
                last_error = e
                logger.warning(
                    "LLM stream error (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))

        raise LLMError(
            f"LLM stream failed after {self.max_retries} retries"
        ) from last_error
