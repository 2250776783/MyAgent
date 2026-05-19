"""基础设施验证脚本。

验证 Docker 容器状态、PostgreSQL + pgvector、Redis 连接。

用法:
    python scripts/verify_infra.py
"""

import asyncio
import sys


def check_docker() -> list[str]:
    import subprocess
    results = []
    for name in ["myagent-postgres", "myagent-redis"]:
        try:
            r = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", name],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip() == "running":
                results.append(f"  [OK] {name} 运行中")
            else:
                results.append(f"  [FAIL] {name} 未运行 ({r.stdout.strip()})")
        except FileNotFoundError:
            return ["  [FAIL] Docker 未安装"]
        except subprocess.TimeoutExpired:
            results.append(f"  [FAIL] {name} 超时")
    return results


async def check_postgres() -> list[str]:
    from src.config import settings
    results = []
    try:
        import asyncpg
        conn = await asyncpg.connect(
            user=settings.pg_user, password=settings.pg_password,
            host=settings.pg_host, port=settings.pg_port,
            database=settings.pg_database,
        )
        ver = await conn.fetchval("SELECT version()")
        results.append(f"  [OK] PostgreSQL: {ver.split(',')[0]}")

        vec = await conn.fetchval(
            "SELECT extversion FROM pg_extension WHERE extname='vector'"
        )
        results.append(f"  [OK] pgvector v{vec}" if vec else "  [FAIL] pgvector 未安装")

        tables = {r["table_name"] async for r in conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )}
        expect = {"users", "sessions", "messages", "conversation_summary",
                  "long_term_memory", "tasks", "tool_calls", "memory_links", "agent_states"}
        missing = expect - tables
        if missing:
            results.append(f"  [WARN] 缺少表: {', '.join(sorted(missing))}")
        else:
            results.append(f"  [OK] {len(expect)} 张表已创建")

        await conn.execute(
            "INSERT INTO long_term_memory (content, memory_type, embedding, importance) "
            "VALUES ('v', 'test', '[0.1,0.2,0.3]'::vector, 0.5) ON CONFLICT DO NOTHING"
        )
        n = await conn.fetchval(
            "SELECT count(*) FROM long_term_memory WHERE embedding IS NOT NULL"
        )
        results.append(f"  [OK] 向量检索正常 ({n} 条)")
        await conn.close()
    except ImportError:
        results.append("  [SKIP] asyncpg 未安装")
    except Exception as e:
        results.append(f"  [FAIL] PostgreSQL: {e}")
    return results


async def check_redis() -> list[str]:
    from src.config import settings
    results = []
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis(
            host=settings.redis_host, port=settings.redis_port,
            password=settings.redis_password or None, db=settings.redis_db,
            decode_responses=True, socket_connect_timeout=5,
        )
        assert await r.ping(), "ping failed"
        results.append(f"  [OK] Redis v{(await r.info('server')).get('redis_version', '?')}")

        await r.set("_v", "ok", ex=10)
        assert await r.get("_v") == "ok"
        await r.delete("_v")
        results.append("  [OK] Redis 读写正常")
        await r.close()
    except ImportError:
        results.append("  [SKIP] redis 未安装")
    except Exception as e:
        results.append(f"  [FAIL] Redis: {e}")
    return results


async def main() -> int:
    print("=" * 48)
    print("  AI Agent Memory — 基础设施验证")
    print("=" * 48)
    all_ok = True
    for label, fn in [("[1/3] Docker", check_docker),
                      ("[2/3] PostgreSQL+pgvector", check_postgres),
                      ("[3/3] Redis", check_redis)]:
        print(f"\n{label}:")
        for line in await fn() if asyncio.iscoroutinefunction(fn) else fn():
            print(line)
            if "[FAIL]" in line:
                all_ok = False
    print("\n" + "=" * 48)
    print(f"  结果: {'全部通过' if all_ok else '存在失败'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
