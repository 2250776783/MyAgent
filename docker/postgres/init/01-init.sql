-- ============================================================================
-- AI Agent Memory System — PostgreSQL 初始化脚本
-- ============================================================================
-- 自动执行顺序：
--   1. 启用 pgvector / uuid-ossp 扩展
--   2. 创建所有基础表结构
--   3. 创建索引与自动更新触发器
-- ============================================================================

-- ─── 扩展 ──────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================================
-- 用户表
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id     VARCHAR(255) UNIQUE,
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) UNIQUE,
    preferences     JSONB DEFAULT '{}',
    metadata        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_external_id ON users(external_id);
CREATE INDEX IF NOT EXISTS idx_users_preferences ON users USING gin(preferences jsonb_path_ops);


-- ============================================================================
-- 会话表
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(500),
    status          VARCHAR(50) NOT NULL DEFAULT 'active',
    agent_id        VARCHAR(255),
    session_data    JSONB DEFAULT '{}',
    metadata        JSONB DEFAULT '{}',
    message_count   INTEGER DEFAULT 0,
    token_count     INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(user_id, status) WHERE status = 'active';


-- ============================================================================
-- 消息表（完整对话历史 + 工具调用追踪 + Agent trace）
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_index   INTEGER NOT NULL DEFAULT 0,
    role            VARCHAR(50) NOT NULL,
    content         TEXT NOT NULL,
    tool_calls      JSONB DEFAULT NULL,
    tool_call_id    VARCHAR(255),
    tool_name       VARCHAR(255),
    reasoning       TEXT,
    token_count     INTEGER DEFAULT 0,
    metadata        JSONB DEFAULT '{}',
    trace_id        VARCHAR(255),
    parent_msg_id   UUID REFERENCES messages(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_index ON messages(session_id, message_index);
CREATE INDEX IF NOT EXISTS idx_messages_trace_id ON messages(trace_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(session_id, role);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);


-- ============================================================================
-- 对话摘要表（支持 Context Compression 和 Session 恢复）
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversation_summary (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    summary_text    TEXT NOT NULL,
    summary_type    VARCHAR(50) NOT NULL DEFAULT 'auto',
    token_count     INTEGER DEFAULT 0,
    message_start   INTEGER,
    message_end     INTEGER,
    importance      REAL DEFAULT 0.5,
    embedding       VECTOR(1536),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_summary_session ON conversation_summary(session_id);
CREATE INDEX IF NOT EXISTS idx_summary_importance ON conversation_summary(importance DESC);
CREATE INDEX IF NOT EXISTS idx_summary_type ON conversation_summary(summary_type);
CREATE INDEX IF NOT EXISTS idx_summary_session_range ON conversation_summary(session_id, message_start, message_end);


-- ============================================================================
-- 长期记忆表（核心：Agent 的"大脑皮层"——知识/偏好/经验/洞察）
-- ============================================================================
CREATE TABLE IF NOT EXISTS long_term_memory (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    content             TEXT NOT NULL,
    memory_type         VARCHAR(100) NOT NULL,
    importance_score    REAL DEFAULT 0.5,
    confidence_score    REAL DEFAULT 0.7,
    emotional_score     REAL,
    access_count        INTEGER DEFAULT 0,
    last_accessed_at    TIMESTAMPTZ,
    decay_factor        REAL DEFAULT 1.0,
    reinforcement_count INTEGER DEFAULT 0,
    source_session      UUID REFERENCES sessions(id) ON DELETE SET NULL,
    embedding           VECTOR(1536),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_user ON long_term_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON long_term_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON long_term_memory(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_access ON long_term_memory(last_accessed_at NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_memory_user_type ON long_term_memory(user_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_user_importance ON long_term_memory(user_id, importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_memory_metadata ON long_term_memory USING gin(metadata jsonb_path_ops);


-- ============================================================================
-- RAG 检索缓存表（避免重复嵌入和 LLM 调用）
-- ============================================================================
CREATE TABLE IF NOT EXISTS knowledge_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash      VARCHAR(64) NOT NULL,
    query_text      TEXT NOT NULL,
    query_embedding VECTOR(1536),
    result_text     TEXT NOT NULL,
    source_docs     JSONB DEFAULT '[]',
    token_count     INTEGER DEFAULT 0,
    hit_count       INTEGER DEFAULT 1,
    metadata        JSONB DEFAULT '{}',
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_query_hash ON knowledge_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON knowledge_cache(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cache_hits ON knowledge_cache(hit_count DESC);


-- ============================================================================
-- 任务表（Agent 长期任务分解与执行追踪）
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES sessions(id) ON DELETE SET NULL,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    parent_task_id  UUID REFERENCES tasks(id) ON DELETE SET NULL,
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority        INTEGER DEFAULT 0,
    task_type       VARCHAR(100),
    input_data      JSONB DEFAULT '{}',
    output_data     JSONB DEFAULT '{}',
    error_info      JSONB DEFAULT NULL,
    progress        REAL DEFAULT 0.0,
    agent_id        VARCHAR(255),
    metadata        JSONB DEFAULT '{}',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC, status);


-- ============================================================================
-- Tool 调用记录表（ReAct 轨迹 / Tool Learning / Agent Replay）
-- ============================================================================
CREATE TABLE IF NOT EXISTS tool_calls (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES sessions(id) ON DELETE CASCADE,
    message_id      UUID REFERENCES messages(id) ON DELETE SET NULL,
    task_id         UUID REFERENCES tasks(id) ON DELETE SET NULL,
    tool_name       VARCHAR(255) NOT NULL,
    tool_args       JSONB NOT NULL,
    tool_result     TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    duration_ms     INTEGER,
    retry_count     INTEGER DEFAULT 0,
    error_message   TEXT,
    token_cost      INTEGER,
    metadata        JSONB DEFAULT '{}',
    trace_id        VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_tool ON tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_status ON tool_calls(status);
CREATE INDEX IF NOT EXISTS idx_tool_calls_trace ON tool_calls(trace_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session_tool ON tool_calls(session_id, tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_errors ON tool_calls(tool_name, status) WHERE status IN ('error', 'timeout');
CREATE INDEX IF NOT EXISTS idx_tool_args ON tool_calls USING gin(tool_args jsonb_path_ops);


-- ============================================================================
-- 记忆关联表（支持多跳记忆图谱 / Graph RAG）
-- ============================================================================
CREATE TABLE IF NOT EXISTS memory_links (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL,
    target_id       UUID NOT NULL,
    relation_type   VARCHAR(100) NOT NULL,
    strength        REAL DEFAULT 1.0,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_links_source ON memory_links(source_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON memory_links(target_id);
CREATE INDEX IF NOT EXISTS idx_links_relation ON memory_links(relation_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_links_unique ON memory_links(source_id, target_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_links_bidirectional ON memory_links(source_id, target_id);


-- ============================================================================
-- Agent 状态表（断点恢复 / 状态持久化）
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_states (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id        VARCHAR(255) NOT NULL,
    session_id      UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    state_type      VARCHAR(100) NOT NULL,
    state_data      JSONB NOT NULL,
    token_count     INTEGER DEFAULT 0,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_agent_states_agent ON agent_states(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_states_session ON agent_states(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_states_type ON agent_states(agent_id, state_type);


-- ============================================================================
-- pgvector IVFFLAT 索引（向量检索加速）
-- ============================================================================
-- 使用说明：
--   检索前设置 probes: SET ivfflat.probes = 10;
--   probes 越大召回率越高，建议值：
--     < 1K 记忆: probes = 1
--     1K-10K:    probes = 10
--     10K-100K:  probes = 20
--     100K+:     probes = 50

CREATE INDEX IF NOT EXISTS idx_memory_embedding ON long_term_memory
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_summary_embedding ON conversation_summary
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE INDEX IF NOT EXISTS idx_cache_embedding ON knowledge_cache
    USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 50);


-- ============================================================================
-- 自动更新 updated_at 触发器
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'updated_at' AND table_schema = 'public'
    LOOP
        EXECUTE format(
            'CREATE TRIGGER IF NOT EXISTS set_%I_updated_at BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            tbl, tbl
        );
    END LOOP;
END;
$$;
