"""FastAPI 日志中间件。

自动在每个 HTTP 请求上初始化 TraceContext，
记录请求/响应信息到日志系统。
"""

import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.logging.adapter import LoggerAdapter
from src.logging.constants import EventType
from src.logging.context import TraceContext


class LoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI 日志中间件。

    在每个 HTTP 请求上注入 trace_id，记录请求和响应信息。

    用法::

        app.add_middleware(LoggingMiddleware, adapter=adapter)
    """

    def __init__(self, app: Any, adapter: LoggerAdapter | None = None) -> None:
        super().__init__(app)
        self._adapter = adapter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理每个 HTTP 请求。"""
        TraceContext.init(
            agent_name="fastapi",
            user_id=request.client.host if request.client else "",
        )
        trace_id = TraceContext.get_trace_id()

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录 HTTP 请求详情的中间件（与 LoggingMiddleware 分开，可选使用）。"""

    def __init__(self, app: Any, adapter: LoggerAdapter | None = None) -> None:
        super().__init__(app)
        self._adapter = adapter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration = (time.monotonic() - start) * 1000

        if self._adapter:
            self._adapter.info(
                EventType.HTTP_REQUEST,
                f"{request.method} {request.url.path} → {response.status_code}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration, 1),
            )

        return response
