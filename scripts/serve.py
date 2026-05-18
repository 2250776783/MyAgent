"""Web 服务器入口。

启动 FastAPI Web 服务器，提供 Agent 的 REST API 和 WebSocket 接口。

用法:
    uv run python scripts/serve.py
    uv run python scripts/serve.py --port 8080 --reload
"""

import argparse
import sys
from pathlib import Path

import uvicorn

# 确保项目根目录在 sys.path 中（src layout）
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.api.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="启动 Agent Web 服务器")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    parser.add_argument("--port", type=int, default=8000, help="端口")
    parser.add_argument("--reload", action="store_true", help="代码变更时自动重载")
    parser.add_argument("--log-level", default="info", help="日志级别")
    args = parser.parse_args()

    app = create_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
