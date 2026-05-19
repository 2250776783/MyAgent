"""异步 LLM API 调用封装。

提供 AsyncLLMClient 类，包装 AsyncOpenAI 实现异步聊天调用，
与同步 LLMClient 保持接口一致。提供 .sync 属性返回同步客户端，
供 ContextManager/MemoryManager 等同步子系统使用。
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from src.config import settings
from src.llm.client import LLMClient, LLMError, _clean_surrogates
from src.llm.types import Message
from src.logging import get_default_adapter
from src.logging.agent import LLMLogger


class AsyncLLMClient:
    """异步 LLM 客户端，包装 AsyncOpenAI。

    用法::

        client = AsyncLLMClient()
        response = await client.async_chat(messages)
        async for token in client.async_chat_stream(messages):
            ...

    同步子组件（ContextManager/MemoryManager）通过 .sync 获取同步客户端::

        sync_llm = client.sync  # LLMClient 实例
        context_mgr = ContextManager(llm=sync_llm)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        llm_logger: LLMLogger | None = None,
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

        self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self._sync_client: LLMClient | None = None
        self._llm_logger = llm_logger or LLMLogger(get_default_adapter())

    @property
    def sync(self) -> LLMClient:
        """返回同配置的同步 LLMClient，供 ContextManager/MemoryManager 使用。"""
        if self._sync_client is None:
            self._sync_client = LLMClient(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay,
            )
        return self._sync_client

    async def async_chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        """异步调用 LLM 聊天完成 API，可选传入工具定义。"""
        if not messages:
            raise ValueError("messages must not be empty")

        dict_messages = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": dict_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        dict_messages = [m.to_dict() for m in messages]
        start = time.monotonic()
        self._llm_logger.prompt(self.model, dict_messages, tools=tools)

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                msg = choice.message
                clean = _clean_surrogates(msg.content or "")
                result = Message(role=msg.role or "assistant", content=clean)
                extra = choice.message.model_extra or {}
                if "reasoning_content" in extra:
                    result.reasoning_content = _clean_surrogates(extra["reasoning_content"])
                if msg.tool_calls:
                    result.tool_calls = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": _clean_surrogates(tc.function.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]

                usage = getattr(response, "usage", None)
                prompt_tokens = usage.prompt_tokens if usage else None
                completion_tokens = usage.completion_tokens if usage else None
                latency = (time.monotonic() - start) * 1000
                self._llm_logger.response(
                    self.model,
                    clean[:200],
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=round(latency, 1),
                    tool_calls=result.tool_calls,
                )
                return result
            except (APIError, APITimeoutError, RateLimitError) as e:
                last_error = e
                latency = (time.monotonic() - start) * 1000
                self._llm_logger.error(
                    self.model,
                    str(e),
                    latency_ms=round(latency, 1),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))

        raise LLMError(
            f"Async LLM call failed after {self.max_retries} retries"
        ) from last_error

    async def async_chat_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
    ) -> AsyncGenerator[Message, None]:
        """异步逐 token 流式调用 LLM。"""
        if not messages:
            raise ValueError("messages must not be empty")

        dict_messages = [m.to_dict() for m in messages]
        start = time.monotonic()
        self._llm_logger.prompt(self.model, dict_messages)
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                stream = await self._client.chat.completions.create(
                    model=self.model,
                    messages=dict_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    stream=True,
                )
                full_content: list[str] = []
                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        clean = _clean_surrogates(delta.content)
                        full_content.append(clean)
                        yield Message(role="assistant", content=clean)
                latency = (time.monotonic() - start) * 1000
                self._llm_logger.response(
                    self.model,
                    "".join(full_content)[:200],
                    latency_ms=round(latency, 1),
                )
                return
            except (APIError, APITimeoutError, RateLimitError) as e:
                last_error = e
                latency = (time.monotonic() - start) * 1000
                self._llm_logger.error(
                    self.model,
                    str(e),
                    latency_ms=round(latency, 1),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))

        raise LLMError(
            f"Async LLM stream failed after {self.max_retries} retries"
        ) from last_error
