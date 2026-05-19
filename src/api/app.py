"""FastAPI 应用工厂。

创建和配置 FastAPI 应用实例，注册路由和中间件。
"""

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import chat, health, sessions, ws
from src.api.sessions.store import SessionStore
from src.logging import get_default_adapter, setup_logging
from src.logging.middleware.fastapi import LoggingMiddleware, RequestLoggingMiddleware

# 在模块加载时初始化日志系统
_adapter = setup_logging()


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    adapter = get_default_adapter()

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
    app.add_middleware(LoggingMiddleware, adapter=adapter)
    app.add_middleware(RequestLoggingMiddleware, adapter=adapter)

    app.state.session_store = SessionStore(ttl_seconds=3600)
    app.state.log_adapter = adapter

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(ws.router)

    @app.on_event("startup")
    async def start_cleanup_task() -> None:
        asyncio.create_task(_cleanup_loop(app))

    @app.on_event("shutdown")
    async def shutdown_logging() -> None:
        from src.logging import shutdown_logging as _shutdown
        _shutdown()

    return app


async def _cleanup_loop(app: FastAPI) -> None:
    """后台 TTL 清理任务。"""
    adapter = get_default_adapter()
    while True:
        await asyncio.sleep(300)
        try:
            store: SessionStore = app.state.session_store
            count = await store.cleanup_expired()
            if count:
                adapter.info(
                    "system.event",
                    f"会话清理: 过期 {count} 个",
                    count=count,
                )
        except Exception:
            adapter.error("system.error", "会话清理异常", exception="清理失败")
