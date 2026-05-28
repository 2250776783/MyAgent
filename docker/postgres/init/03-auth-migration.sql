-- ============================================================================
-- Auth 模块迁移 — 为 users 表添加认证相关字段
-- ============================================================================
-- 使用说明: docker compose exec postgres psql -U myagent -d agent_memory -f /docker-entrypoint-initdb.d/03-auth-migration.sql
-- 或者在容器内执行: psql -U myagent -d agent_memory < /sql/03-auth-migration.sql
-- ============================================================================

-- 添加密码哈希字段（bcrypt 哈希值，约 60 字符）
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NOT NULL DEFAULT '';

-- 添加角色字段（USER / ADMIN）
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'USER';

-- 为角色添加索引
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
