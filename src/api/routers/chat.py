"""聊天 API 路由。

提供非流式 POST /api/chat 和 SSE 流式 POST /api/chat/stream 端点。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from src.api.deps import get_session
from src.api.models.chat import ChatRequest, ChatResponse
from src.api.sessions.store import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    session: Session = Depends(get_session),
) -> ChatResponse:
    """非流式聊天：发送消息，返回完整回复。"""
    if not session.agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        content = await session.agent.chat(request.message)
        return ChatResponse(session_id=session.id, content=content)
    except Exception as e:
        logger.exception("Chat error for session %s", session.id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    session: Session = Depends(get_session),
):
    """SSE 流式聊天：通过 Server-Sent Events 推送回复。"""
    if not session.agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    async def event_generator():
        try:
            async for chunk in session.agent.chat_stream(request.message):
                yield {"event": "token", "data": chunk}
            yield {"event": "done", "data": session.id}
        except Exception as e:
            logger.exception("Stream error for session %s", session.id)
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())
