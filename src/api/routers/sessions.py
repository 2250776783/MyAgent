"""Session 管理 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_session_store
from src.api.sessions.store import SessionStore

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(store: SessionStore = Depends(get_session_store)):
    sessions = await store.list_active()
    return {
        "sessions": [
            {"id": s.id, "created_at": s.created_at}
            for s in sessions
        ]
    }


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    session = await store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = []
    if session.agent:
        for msg in session.agent.messages:
            if msg.role in ("user", "assistant"):
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
    return {"messages": messages}


@router.get("/{session_id}")
async def get_session_info(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    session = await store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": session.id, "created_at": session.created_at}


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    deleted = await store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
