"""FastAPI 依赖注入。

提供 session、agent 工厂等可复用依赖。
"""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status

from src.api.auth import db as auth_db
from src.api.auth import jwt as auth_jwt
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


async def get_current_user(
    authorization: str | None = Header(None),
) -> dict:
    """从 Authorization header 解析当前登录用户。"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证令牌")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证令牌格式错误")
    payload = auth_jwt.decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证令牌无效或已过期")
    user = await auth_db.get_user_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    return user
