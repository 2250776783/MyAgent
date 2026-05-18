"""WebSocket 聊天路由。

提供实时双向通信端点 /api/ws/chat。
同一个 WebSocket 连接内可发送多条消息，session 在首条消息时建立。

协议:
  客户端 → 服务端: {"message": "你好", "session_id": "可选"}
  服务端 → 客户端: {"type": "token", "data": {"text": "..."}}
                   {"type": "tool_call", "data": {"id": "...", "name": "...", "args": "..."}}
                   {"type": "tool_result", "data": {"name": "...", "output": "..."}}
                   {"type": "done", "data": {"session_id": "..."}}
                   {"type": "error", "data": {"message": "..."}}
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    session = None
    store = None

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            message = msg.get("message", "")

            if not message:
                await websocket.send_json(
                    {"type": "error", "data": {"message": "消息不能为空"}}
                )
                continue

            # 首条消息时创建 session，后续复用
            if session is None:
                from src.api.deps import create_async_agent
                from src.api.sessions.store import SessionStore

                store = websocket.app.state.session_store
                session = await store.get_or_create(
                    session_id=msg.get("session_id"),
                    agent_factory=create_async_agent,
                )

            if not session or not session.agent:
                await websocket.send_json(
                    {"type": "error", "data": {"message": "Agent 未初始化"}}
                )
                continue

            async for event in session.agent.chat_stream_events(message):
                if event.type == "done":
                    event.data["session_id"] = session.id
                await websocket.send_json(
                    {"type": event.type, "data": event.data}
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except json.JSONDecodeError:
        try:
            await websocket.send_json(
                {"type": "error", "data": {"message": "无效的 JSON 消息"}}
            )
        except Exception:
            pass
    except Exception as e:
        logger.exception("WebSocket error")
        try:
            await websocket.send_json(
                {"type": "error", "data": {"message": str(e)}}
            )
        except Exception:
            pass
