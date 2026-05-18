"""FastAPI 应用工厂。

创建和配置 FastAPI 应用实例，注册路由和中间件。
"""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import chat, health, sessions, ws
from src.api.sessions.store import SessionStore

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    app = FastAPI(
        title="MyAgent API",
        version="0.1.0",
        description="Web-based Agent API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.session_store = SessionStore(ttl_seconds=3600)

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(ws.router)

    @app.on_event("startup")
    async def start_cleanup_task() -> None:
        asyncio.create_task(_cleanup_loop(app))

    return app


async def _cleanup_loop(app: FastAPI) -> None:
    """后台 TTL 清理任务。"""
    while True:
        await asyncio.sleep(300)
        try:
            store: SessionStore = app.state.session_store
            count = await store.cleanup_expired()
            if count:
                logger.info("Cleaned up %d expired sessions", count)
        except Exception:
            logger.exception("Session cleanup error")
