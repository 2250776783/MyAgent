"""内置工具集。

提供计算器、时间等常用工具，可在 Agent 中直接注册使用。
"""

import datetime
from typing import Any

from src.agent.tools.base import BaseTool


class CurrentTimeTool(BaseTool):
    """获取当前日期和时间。"""

    name: str = "current_time"
    description: str = "获取当前日期和时间"

    def run(self, **kwargs: Any) -> str:  # noqa: ANN401
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class CalculatorTool(BaseTool):
    """安全数学计算器，支持加减乘除和括号。"""

    name: str = "calculator"
    description: str = "执行数学计算，支持 + - * / 和括号。传入参数 expression"

    def run(self, **kwargs: Any) -> str:  # noqa: ANN401
        expr = kwargs.get("expression", "")
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expr):
            return "错误: 表达式包含非法字符"
        try:
            result = eval(expr, {"__builtins__": {}}, {})  # nosec
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"
