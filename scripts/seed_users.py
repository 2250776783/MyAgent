"""生成 100 名测试用户 SQL 种子文件。

用法:
    uv run python scripts/seed_users.py
    docker compose exec -T postgres psql -U myagent -d agent_memory < docker/postgres/init/02-seed-users.sql
"""

import os

import bcrypt as _bcrypt

SQL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docker",
    "postgres",
    "init",
    "02-seed-users.sql",
)

# ── 100 个中文姓名 ──────────────────────────────────────────────
NAMES = [
    "张三", "李四", "王芳", "赵强", "刘洋",
    "陈静", "杨磊", "黄丽", "周杰", "吴敏",
    "徐浩", "孙悦", "马超", "朱婷", "胡波",
    "郭晨", "林雪", "何峰", "高娜", "罗刚",
    "梁倩", "宋涛", "唐晓", "韩冰", "曹瑞",
    "邓萍", "许凯", "彭娟", "苏明", "潘慧",
    "田宇", "董洁", "范鑫", "蔡文", "余勇",
    "杜琳", "叶璇", "程辉", "魏霞", "沈浩",
    "任杰", "姚莉", "卢强", "傅敏", "钟磊",
    "崔燕", "谭鹏", "廖红", "汪俊", "白晶",
    "邹峰", "石磊", "孟娜", "秦亮", "顾婷",
    "侯伟", "邵洁", "万超", "段敏", "雷波",
    "钱芳", "汤杰", "尹静", "易辉", "常娟",
    "武强", "乔艳", "贺鑫", "赖勇", "龚丽",
    "文豪", "卫兰", "安琪", "饶超", "荣华",
    "幸敏", "韦杰", "贾婷", "江波", "方静",
    "严浩", "康辉", "洪霞", "史强", "陶敏",
    "邱磊", "樊丽", "舒俊", "聂晶", "邢涛",
    "俞洁", "欧阳雪", "慕容峰", "令狐冲", "李慕白",
    "林诗音", "花无缺", "楚留香", "陆小凤", "叶孤城",
]

DOMAINS = [
    "qq.com", "163.com", "gmail.com", "outlook.com", "foxmail.com",
    "icloud.com", "sina.com", "sohu.com", "126.com", "yeah.net",
]


def generate_sql() -> str:
    """生成 INSERT SQL 语句。"""
    lines = [
        "-- ============================================================================",
        "-- Seed: 100 名测试用户",
        "-- ============================================================================",
        "-- 所有用户默认密码: password123",
        "-- 如需重新生成：uv run python scripts/seed_users.py",
        "-- 执行：docker compose exec -T postgres psql -U myagent -d agent_memory < docker/postgres/init/02-seed-users.sql",
        "-- ============================================================================",
        "",
        "INSERT INTO users (id, external_id, name, email, password_hash, role, is_active, preferences, metadata)",
        "VALUES",
    ]

    rows = []
    for i, name in enumerate(NAMES):
        # 生成拼音风格的 external_id
        pinyin = name.lower().replace(" ", ".")
        ext_id = f"user_{pinyin}_{i+1:03d}"

        # 生成邮箱
        email_prefix = pinyin.replace(".", "")
        domain = DOMAINS[i % len(DOMAINS)]
        email = f"{email_prefix}{i+1:03d}@{domain}"

        # 密码哈希: "password123"（使用 bcrypt）
        pwd_hash = _bcrypt.hashpw(b"password123", _bcrypt.gensalt()).decode()

        # 角色: 前 5 个为 ADMIN，其余为 USER
        role = "ADMIN" if i < 5 else "USER"

        # 是否活跃: 第 95-99 个用户为不活跃
        is_active = "false" if 95 <= i < 100 else "true"

        # 偏好和元数据
        theme = "dark" if i % 3 == 0 else ("light" if i % 3 == 1 else "system")
        lang = "zh-CN" if i % 2 == 0 else "en"
        preferences = f'{{"theme": "{theme}", "language": "{lang}", "notifications": {"true" if i % 5 != 0 else "false"}}}'
        metadata = f'{{"source": "seed", "batch": "20260528", "index": {i}}}'

        rows.append(
            f"    (uuid_generate_v4(), '{ext_id}', '{name}', '{email}', "
            f"'{pwd_hash}', '{role}', {is_active}, '{preferences}'::jsonb, '{metadata}'::jsonb)"
        )

    lines.append(",\n".join(rows))
    lines.append(";")

    # 更新序列
    lines.extend([
        "",
        "-- 更新 updated_at 时间戳（可选验证）",
        "SELECT COUNT(*) AS total_users FROM users;",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    sql = generate_sql()
    with open(SQL_PATH, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"[OK] 种子 SQL 已生成: {SQL_PATH}")
    print(f"      共 {len(NAMES)} 条用户记录")
    print(f"      默认密码: password123")
    print(f"      管理员: {', '.join(NAMES[:5])}")


if __name__ == "__main__":
    main()
