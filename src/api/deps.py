"""FastAPI 依赖注入。

提供 session、agent 工厂等可复用依赖。
"""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, Request

from src.api.sessions.store import Session, SessionStore
from src.agent.async_agent import AsyncAgent
from src.llm import AsyncLLMClient


def create_async_agent(**kwargs: Any) -> AsyncAgent:
    """工厂函数：创建新的 AsyncAgent 实例。"""
    llm = AsyncLLMClient()
    return AsyncAgent(llm=llm, **kwargs)


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.session_store


async def get_session(
    session_id: str | None = None,
    store: SessionStore = Depends(get_session_store),
) -> AsyncGenerator[Session, None]:
    """按 session_id 获取或创建 session。"""
    session = await store.get_or_create(
        session_id=session_id,
        agent_factory=create_async_agent,
    )
    yield session
