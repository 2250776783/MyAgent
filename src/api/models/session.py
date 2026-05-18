from pydantic import BaseModel


class SessionInfo(BaseModel):
    id: str
    created_at: float
    last_active: float
