"""Auth 模块 - 异步数据库操作。"""
from typing import Any

import asyncpg

from src.config import settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """获取或创建 asyncpg 连接池。"""
    global _pool
    if _pool is None:
        clean_dsn = f"postgresql://{settings.pg_user}:{settings.pg_password}@{settings.pg_host}:{settings.pg_port}/{settings.pg_database}"
        _pool = await asyncpg.create_pool(
            dsn=clean_dsn,
            min_size=settings.pg_min_size,
            max_size=settings.pg_max_size,
            command_timeout=10,
        )
    return _pool


async def close_pool() -> None:
    """关闭连接池。"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_user_by_email(email: str) -> dict[str, Any] | None:
    """按邮箱查找用户。"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, email, password_hash, role, is_active, "
            "preferences, metadata, created_at, updated_at "
            "FROM users WHERE email = $1",
            email,
        )
    return dict(row) if row else None


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """按 ID 查找用户。"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, email, password_hash, role, is_active, "
            "preferences, metadata, created_at, updated_at "
            "FROM users WHERE id = $1::uuid",
            user_id,
        )
    return dict(row) if row else None


async def create_user(
    name: str,
    email: str,
    password_hash: str,
) -> dict[str, Any]:
    """创建新用户并返回用户信息。"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO users (name, email, password_hash, role) "
            "VALUES ($1, $2, $3, 'USER') "
            "RETURNING id, name, email, role, is_active, created_at, updated_at",
            name,
            email,
            password_hash,
        )
    return dict(row)
