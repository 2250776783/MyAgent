"""Auth 路由 - 注册、登录、Token 管理。"""
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.auth import db as auth_db
from src.api.auth import jwt as auth_jwt
from src.api.auth import password as auth_pwd
from src.api.deps import get_current_user
from src.api.models.auth import (
    AuthResponse,
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    TokenRefreshRequest,
    UserResponse,
)

router = APIRouter(tags=["auth"])


def _user_to_response(row: dict) -> UserResponse:
    """数据库行记录 → UserResponse。"""
    return UserResponse(
        id=str(row["id"]),
        username=row["name"],
        email=row["email"],
        role=row["role"],
        is_active=row.get("is_active", True),
        created_at=str(row.get("created_at", "")),
    )


def _make_auth_response(user_row: dict) -> AuthResponse:
    """生成含 token 的认证响应。"""
    user_id = str(user_row["id"])
    role = user_row["role"]
    return AuthResponse(
        access_token=auth_jwt.create_access_token(user_id, role),
        refresh_token=auth_jwt.create_refresh_token(user_id),
        user=_user_to_response(user_row),
    )


# ── 注册 ───────────────────────────────────────────────────────


@router.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """注册新用户。注册成功后自动登录，返回 access_token 和 refresh_token。"""
    existing = await auth_db.get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )
    hashed = auth_pwd.hash_password(body.password)
    try:
        user_row = await auth_db.create_user(
            name=body.username,
            email=body.email,
            password_hash=hashed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {e}",
        )
    return _make_auth_response(user_row)


# ── 登录 ───────────────────────────────────────────────────────


@router.post("/api/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """用户登录。"""
    user_row = await auth_db.get_user_by_email(body.email)
    if not user_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if not user_row.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    if not auth_pwd.verify_password(body.password, user_row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    return _make_auth_response(user_row)


# ── 登出 ───────────────────────────────────────────────────────


@router.post("/api/auth/logout")
async def logout():
    """登出。客户端清除 token 即可，服务端不做额外操作。"""
    return {"success": True, "message": "已登出"}


# ── Token 刷新 ────────────────────────────────────────────────


@router.post("/api/auth/refresh")
async def refresh_token(body: TokenRefreshRequest):
    """使用 refresh_token 获取新的 token 对。"""
    payload = auth_jwt.decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh_token 无效或已过期")
    user = await auth_db.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return {
        "access_token": auth_jwt.create_access_token(str(user["id"]), user["role"]),
        "refresh_token": auth_jwt.create_refresh_token(str(user["id"])),
    }


# ── 获取个人信息 ───────────────────────────────────────────────


@router.get("/api/auth/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
):
    """获取当前登录用户信息。"""
    return _user_to_response(current_user)


# ── 修改密码 ───────────────────────────────────────────────────


@router.put("/api/auth/password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
):
    """修改密码。"""
    if not auth_pwd.verify_password(body.old_password, current_user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码至少 6 个字符")
    new_hash = auth_pwd.hash_password(body.new_password)
    pool = await auth_db.get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2::uuid",
            new_hash,
            str(current_user["id"]),
        )
    return {"success": True, "message": "密码修改成功"}
