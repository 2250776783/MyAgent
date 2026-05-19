# AI Agent Memory System — 数据库与缓存基础设施

## 架构

```
AI Agent (pgvector_store.py)
  ├── asyncpg → PostgreSQL 16 + pgvector (myagent-postgres)
  └── redis   → Redis 7 + AOF (myagent-redis)
```

## 快速启动

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
```

## 目录结构

```
docker/
├── docker-compose.yml        # 编排文件
├── .env.example              # 环境变量示例
├── postgres/init/01-init.sql # 建表 + pgvector
└── redis/redis.conf          # AOF + LRU 配置
```

## 健康检查

```bash
docker compose -f docker/docker-compose.yml exec postgres pg_isready -U myagent -d agent_memory
docker compose -f docker/docker-compose.yml exec redis redis-cli ping
```

## PostgreSQL 验证

```bash
# 查看所有表
docker compose -f docker/docker-compose.yml exec postgres psql -U myagent -d agent_memory -c "\dt"

# 验证 pgvector 扩展
docker compose -f docker/docker-compose.yml exec postgres psql -U myagent -d agent_memory \
  -c "SELECT extname, extversion FROM pg_extension;"

# 向量检索测试
docker compose -f docker/docker-compose.yml exec postgres psql -U myagent -d agent_memory -c "
  INSERT INTO long_term_memory (content, memory_type, embedding, importance)
  VALUES ('苹果是水果', 'entity', '[0.1,0.2,0.3]'::vector, 0.9);
  SELECT content, (embedding <=> '[0.12,0.22,0.32]'::vector) AS distance
  FROM long_term_memory WHERE embedding IS NOT NULL ORDER BY distance LIMIT 5;"
```

## Redis 验证

```bash
docker compose -f docker/docker-compose.yml exec redis redis-cli set "test:k" "v"
docker compose -f docker/docker-compose.yml exec redis redis-cli get "test:k"
docker compose -f docker/docker-compose.yml exec redis redis-cli del "test:k"
docker compose -f docker/docker-compose.yml exec redis redis-cli dbsize
```

## Python 连接

```python
import asyncpg, redis.asyncio as aioredis
from src.config import settings

async def check_pg():
    conn = await asyncpg.connect(user=settings.pg_user, password=settings.pg_password,
                                 host=settings.pg_host, port=settings.pg_port,
                                 database=settings.pg_database)
    print(await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname='vector'"))
    await conn.close()

async def check_redis():
    r = aioredis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    print(await r.ping())
    await r.close()
```

## 使用 PGVectorMemoryStore

```python
import asyncio
from src.agent.memory.stores import PGVectorMemoryStore
from src.agent.memory.types import MemoryItem

async def demo():
    store = PGVectorMemoryStore()
    await store.connect()
    await store.asave(MemoryItem(content="用户偏好函数式编程", type="preference",
                                 importance=0.9, embedding=[0.1, 0.2, 0.3]))
    for m in await store.asearch([0.1, 0.2, 0.3], k=5):
        print(f"  [{m.importance}] {m.content}")
    await store.save_message(session_id="s1", role="user", content="你好")
    await store.aclose()

asyncio.run(demo())
```

## 表结构

| 表 | 用途 | 关键字段 |
|----|------|----------|
| `users` | 用户 | id(UUID), name, email, preferences(JSONB) |
| `sessions` | 会话 | id, user_id, status, agent_id, session_data(JSONB) |
| `messages` | 消息 | id, session_id, role, content, tool_calls(JSONB) |
| `conversation_summary` | 摘要 | id, session_id, summary_text, embedding(VECTOR) |
| `long_term_memory` | 记忆+向量 | id, content, memory_type, embedding(VECTOR), importance |
| `tasks` | 任务 | id, session_id, title, status, progress |
| `tool_calls` | 工具日志 | id, session_id, tool_name, tool_args(JSONB), duration_ms |
| `memory_links` | 关联图谱 | source_id, target_id, relation_type, strength |
| `agent_states` | 状态恢复 | agent_id, session_id, state_type, state_data(JSONB) |

## 配置（`.env`）

```env
PG_HOST=localhost        PG_PORT=5432    PG_USER=myagent    PG_PASSWORD=myagent_secret    PG_DATABASE=agent_memory
REDIS_HOST=localhost     REDIS_PORT=6379 REDIS_PASSWORD=    REDIS_DB=0
PG_MIN_SIZE=2            PG_MAX_SIZE=10
```

## 生产建议

1. Redis 设置 `requirepass` 密码
2. 添加 `deploy.resources.limits` 到 docker-compose.yml
3. 定期 `pg_dump` 备份
4. 大数据量时添加 HNSW 索引：`CREATE INDEX ON long_term_memory USING hnsw (embedding vector_cosine_ops);`
5. 扩展监控：`docker-compose.yml` 可增加 pgAdmin / Prometheus
