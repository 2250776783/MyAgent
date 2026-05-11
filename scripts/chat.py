"""交互式对话脚本。

启动 Agent 的交互式对话循环，支持工具调用和流式输出。

Usage:
    uv run python scripts/chat.py
    uv run python scripts/chat.py --no-tools
"""

import argparse
import logging
import sys

from src.agent import Agent
from src.agent.tools import CalculatorTool, CurrentTimeTool
from src.llm import LLMClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个智能助手，可以使用工具来获取信息或执行操作。"
    "如果工具返回了结果，根据结果回答用户的问题。"
    "如果不需要使用工具，直接回答即可。"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 交互式对话")
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="禁用工具（仅纯对话）",
    )
    parser.add_argument(
        "--system-prompt",
        default=SYSTEM_PROMPT,
        help="自定义系统提示词",
    )
    args = parser.parse_args()

    llm = LLMClient()

    tools = None
    if not args.no_tools:
        tools = [CurrentTimeTool(), CalculatorTool()]

    agent = Agent(
        llm=llm,
        tools=tools,
        system_prompt=args.system_prompt,
    )

    print("Agent 对话已启动 (输入 /quit 退出, /reset 重置历史)")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n>>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input.strip():
            continue

        if user_input.strip() == "/quit":
            print("再见！")
            break

        if user_input.strip() == "/reset":
            agent.reset()
            print("对话历史已重置。")
            continue

        try:
            print()
            full = ""
            for chunk in agent.chat_stream(user_input):
                print(chunk, end="", flush=True)
                full += chunk
            print()
        except Exception as e:
            logger.error("对话出错: %s", e)
            print(f"\n[错误] {e}")


if __name__ == "__main__":
    main()
