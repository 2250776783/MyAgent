"""重新生成种子用户数据：清空旧中文数据，插入纯 ASCII 新数据。"""
import asyncio
import json
from pathlib import Path

import bcrypt
import asyncpg

# ── 100 个纯英文用户名 ──────────────────────────────────────────
# 格式: (username, email, role, active)
USERS = [
    ("zhangsan",   "zhangsan001@qq.com",      "ADMIN", True),
    ("lisi",       "lisi002@163.com",         "ADMIN", True),
    ("wangfang",   "wangfang003@gmail.com",   "ADMIN", True),
    ("zhaoqiang",  "zhaoqiang004@outlook.com","ADMIN", True),
    ("liuyang",    "liuyang005@foxmail.com",  "ADMIN", True),
    ("chenjing",   "chenjing006@icloud.com",  "USER",  True),
    ("yanglei",    "yanglei007@sina.com",     "USER",  True),
    ("huangli",    "huangli008@sohu.com",     "USER",  True),
    ("zhoujie",    "zhoujie009@126.com",      "USER",  True),
    ("wumin",      "wumin010@yeah.net",       "USER",  True),
    ("xuhao",      "xuhao011@qq.com",         "USER",  True),
    ("sunyue",     "sunyue012@163.com",       "USER",  True),
    ("machao",     "machao013@gmail.com",     "USER",  True),
    ("zhuting",    "zhuting014@outlook.com",  "USER",  True),
    ("hubo",       "hubo015@foxmail.com",     "USER",  True),
    ("guochen",    "guochen016@icloud.com",   "USER",  True),
    ("linxue",     "linxue017@sina.com",      "USER",  True),
    ("hefeng",     "hefeng018@sohu.com",      "USER",  True),
    ("gaona",      "gaona019@126.com",        "USER",  True),
    ("luogang",    "luogang020@yeah.net",     "USER",  True),
    ("liangqian",  "liangqian021@qq.com",     "USER",  True),
    ("songtao",    "songtao022@163.com",      "USER",  True),
    ("tangxiao",   "tangxiao023@gmail.com",   "USER",  True),
    ("hanbing",    "hanbing024@outlook.com",  "USER",  True),
    ("caorui",     "caorui025@foxmail.com",   "USER",  True),
    ("dengping",   "dengping026@icloud.com",  "USER",  True),
    ("xukai",      "xukai027@sina.com",       "USER",  True),
    ("pengjuan",   "pengjuan028@sohu.com",    "USER",  True),
    ("suming",     "suming029@126.com",       "USER",  True),
    ("panhui",     "panhui030@yeah.net",      "USER",  True),
    ("tianyu",     "tianyu031@qq.com",        "USER",  True),
    ("dongjie",    "dongjie032@163.com",      "USER",  True),
    ("fanxin",     "fanxin033@gmail.com",     "USER",  True),
    ("caiwen",     "caiwen034@outlook.com",   "USER",  True),
    ("yuyong",     "yuyong035@foxmail.com",   "USER",  True),
    ("dulin",      "dulin036@icloud.com",     "USER",  True),
    ("yexuan",     "yexuan037@sina.com",      "USER",  True),
    ("chenghui",   "chenghui038@sohu.com",    "USER",  True),
    ("weixia",     "weixia039@126.com",       "USER",  True),
    ("shenhao",    "shenhao040@yeah.net",     "USER",  True),
    ("renjie",     "renjie041@qq.com",        "USER",  True),
    ("yaoli",      "yaoli042@163.com",        "USER",  True),
    ("luqiang",    "luqiang043@gmail.com",    "USER",  True),
    ("fumin",      "fumin044@outlook.com",    "USER",  True),
    ("zhonglei",   "zhonglei045@foxmail.com", "USER",  True),
    ("cuiyan",     "cuiyan046@icloud.com",    "USER",  True),
    ("tanpeng",    "tanpeng047@sina.com",     "USER",  True),
    ("liaohong",   "liaohong048@sohu.com",    "USER",  True),
    ("wangjun",    "wangjun049@126.com",      "USER",  True),
    ("baijing",    "baijing050@yeah.net",      "USER",  True),
    ("zoufeng",    "zoufeng051@qq.com",       "USER",  True),
    ("shilei",     "shilei052@163.com",       "USER",  True),
    ("mengna",     "mengna053@gmail.com",     "USER",  True),
    ("qinliang",   "qinliang054@outlook.com", "USER",  True),
    ("guting",     "guting055@foxmail.com",   "USER",  True),
    ("houwei",     "houwei056@icloud.com",    "USER",  True),
    ("shaojie",    "shaojie057@sina.com",     "USER",  True),
    ("wanchao",    "wanchao058@sohu.com",     "USER",  True),
    ("duanmin",    "duanmin059@126.com",      "USER",  True),
    ("leibo",      "leibo060@yeah.net",       "USER",  True),
    ("qianfang",   "qianfang061@qq.com",      "USER",  True),
    ("tangjie",    "tangjie062@163.com",      "USER",  True),
    ("yunjing",    "yunjing063@gmail.com",    "USER",  True),
    ("yihui",      "yihui064@outlook.com",    "USER",  True),
    ("changjuan",  "changjuan065@foxmail.com","USER",  True),
    ("wuqiang",    "wuqiang066@icloud.com",   "USER",  True),
    ("qiaoyan",    "qiaoyan067@sina.com",     "USER",  True),
    ("hexin",      "hexin068@sohu.com",       "USER",  True),
    ("laiyong",    "laiyong069@126.com",      "USER",  True),
    ("gongli",     "gongli070@yeah.net",      "USER",  True),
    ("wenhao",     "wenhao071@qq.com",        "USER",  True),
    ("weilan",     "weilan072@163.com",       "USER",  True),
    ("anqi",       "anqi073@gmail.com",       "USER",  True),
    ("raochao",    "raochao074@outlook.com",  "USER",  True),
    ("ronghua",    "ronghua075@foxmail.com",  "USER",  True),
    ("xingmin",    "xingmin076@icloud.com",   "USER",  True),
    ("weijie",     "weijie077@sina.com",      "USER",  True),
    ("jiating",    "jiating078@sohu.com",     "USER",  True),
    ("jiangbo",    "jiangbo079@126.com",      "USER",  True),
    ("fangjing",   "fangjing080@yeah.net",    "USER",  True),
    ("yanhao",     "yanhao081@qq.com",        "USER",  True),
    ("kanghui",    "kanghui082@163.com",      "USER",  True),
    ("hongxia",    "hongxia083@gmail.com",    "USER",  True),
    ("shiqiang",   "shiqiang084@outlook.com", "USER",  True),
    ("taomin",     "taomin085@foxmail.com",   "USER",  True),
    ("qiulei",     "qiulei086@icloud.com",    "USER",  True),
    ("fanli",      "fanli087@sina.com",       "USER",  True),
    ("shujun",     "shujun088@sohu.com",      "USER",  True),
    ("niejing",    "niejing089@126.com",      "USER",  True),
    ("xingtao",    "xingtao090@yeah.net",     "USER",  True),
    ("yujie",      "yujie091@qq.com",         "USER",  True),
    ("ouyangxue",  "ouyangxue092@163.com",    "USER",  True),
    ("murongfeng", "murongfeng093@gmail.com", "USER",  True),
    ("linghuchong","linghuchong094@outlook.com","USER", True),
    ("limubai",    "limubai095@foxmail.com",  "USER",  True),
    ("linshiyin",  "linshiyin096@icloud.com", "USER",  False),
    ("huawuque",   "huawuque097@sina.com",    "USER",  False),
    ("chuliuxiang","chuliuxiang098@sohu.com",  "USER",  False),
    ("luxiaofeng", "luxiaofeng099@126.com",   "USER",  False),
    ("yegucheng",  "yegucheng100@yeah.net",   "USER",  False),
]

PASSWORD = "password123"
DSN = "postgresql://myagent:myagent_secret@localhost:5432/agent_memory"

SEED_FILE = Path(__file__).resolve().parent.parent / "docker" / "postgres" / "init" / "02-seed-users.sql"
LOGIN_PAGE = Path(__file__).resolve().parent.parent / "web" / "src" / "app" / "(auth)" / "login" / "page.tsx"


def generate_sql() -> str:
    """生成纯 ASCII 种子数据 SQL 文件。"""
    password_hash = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode()
    envs = ["dark", "light", "system"]
    langs = ["zh-CN", "en"]
    lines = [
        "-- ============================================================================",
        "-- Seed: 100 名测试用户（纯 ASCII）",
        "-- ============================================================================",
        "-- 所有用户密码: password123",
        "-- 重新生成：uv run python scripts/reseed_users.py",
        f"-- 生成时间: 2026-05-28",
        "-- 执行：docker compose exec -T postgres psql -U myagent -d agent_memory < docker/postgres/init/02-seed-users.sql",
        "-- ============================================================================",
        "",
        "INSERT INTO users (id, external_id, name, email, password_hash, role, is_active, preferences, metadata)",
        "VALUES",
    ]

    for i, (name, email, role, active) in enumerate(USERS):
        theme = envs[i % 3]
        lang = langs[i % 2]
        prefs = json.dumps({"theme": theme, "language": lang, "notifications": i % 3 != 0}, ensure_ascii=False)
        meta = json.dumps({"source": "seed", "batch": "20260528", "index": i}, ensure_ascii=False)
        ext_id = f"user_{name}_{i+1:03d}"
        comma = "," if i < len(USERS) - 1 else ";"
        lines.append(
            f"    (uuid_generate_v4(), '{ext_id}', '{name}', '{email}', "
            f"'{password_hash}', '{role}', {'true' if active else 'false'}, "
            f"'{prefs}'::jsonb, '{meta}'::jsonb){comma}"
        )

    lines.extend(["", "-- 验证", "SELECT COUNT(*) AS total_users FROM users;", ""])
    return "\n".join(lines)


def generate_login_default() -> str:
    """第一个用户作为登录页面默认值。"""
    return USERS[0][0], USERS[0][1]  # zhangsan, zhangsan001@qq.com


async def reseed():
    """清空旧数据并插入新数据。"""
    conn = await asyncpg.connect(DSN)
    try:
        # 清空依赖表
        print("清空旧数据...")
        await conn.execute("DELETE FROM sessions")
        await conn.execute("DELETE FROM long_term_memory")
        await conn.execute("DELETE FROM tasks")
        await conn.execute("DELETE FROM agent_states")
        await conn.execute("DELETE FROM users")

        # 生成密码哈希
        password_hash = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode()

        # 批量插入
        print(f"插入 {len(USERS)} 个用户...")
        for i, (name, email, role, active) in enumerate(USERS):
            ext_id = f"user_{name}_{i+1:03d}"
            theme = ["dark", "light", "system"][i % 3]
            lang = ["zh-CN", "en"][i % 2]
            prefs = json.dumps({"theme": theme, "language": lang, "notifications": i % 3 != 0})
            meta = json.dumps({"source": "seed", "batch": "20260528", "index": i})

            await conn.execute(
                """INSERT INTO users (id, external_id, name, email, password_hash, role, is_active, preferences, metadata)
                   VALUES (uuid_generate_v4(), $1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb)""",
                ext_id, name, email, password_hash, role, active, prefs, meta
            )

        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"用户总数: {count}")
    finally:
        await conn.close()


async def main():
    # 1. 写入数据库
    await reseed()

    # 2. 更新 SQL 种子文件
    sql = generate_sql()
    SEED_FILE.write_text(sql, encoding="utf-8")
    print(f"SQL 种子文件已更新: {SEED_FILE}")

    # 3. 更新登录页面默认值
    uname, uemail = generate_login_default()
    print(f"\n登录页面应更新为: {uname} / password123")
    print(f"   email: {uemail}")

    # 验证新用户能登录
    import urllib.request
    body = json.dumps({"email": "zhangsan001@qq.com", "password": "password123"}).encode()
    req = urllib.request.Request("http://localhost:8000/api/auth/login", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data.get("access_token"):
            print("\n✅ 登录验证通过！zhangsan001@qq.com 可以成功登录")
    except Exception as e:
        print(f"\n⚠️ 登录验证: {e}")


if __name__ == "__main__":
    asyncio.run(main())
