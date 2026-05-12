"""安全计算器工具。

在受限环境中执行数学表达式求值，仅支持 +-*/ 和括号。
防止注入攻击，禁止访问系统函数和变量。
"""

from typing import Any

from pydantic import Field

from src.agent.tools.base import (
    BaseTool,
    ToolOutput,
    ToolMetadata,
    BaseToolArgs,
)

ALLOWED_CHARS = set("0123456789+-*/.() ")


class CalculatorArgs(BaseToolArgs):
    """计算器参数：数学表达式。"""

    expression: str = Field(
        description="数学表达式，如 1+2 或 (3+5)*2。支持 + - * / 和括号。"
    )


class CalculatorTool(BaseTool):
    """安全数学计算器。

    适用场景：
    - 数学公式求值
    - 数值运算

    不适用场景：
    - 字符串拼接或格式化
    - 逻辑运算
    - 访问系统变量或调用函数
    """

    name: str = "calculator"
    description: str = "执行数学计算，支持 + - * / 和括号。传入数学表达式，返回计算结果。"
    args_schema: type[CalculatorArgs] = CalculatorArgs
    metadata: ToolMetadata = ToolMetadata(
        readonly=True,
        destructive=False,
        category="code",
    )

    def _run(self, expression: str, **kwargs: Any) -> ToolOutput:
        if not expression or not expression.strip():
            return ToolOutput(success=False, error="表达式不能为空")

        if not all(c in ALLOWED_CHARS for c in expression):
            return ToolOutput(
                success=False,
                error="表达式包含非法字符，只支持数字和 + - * / . ( ) 运算符",
            )

        try:
            result = eval(expression, {"__builtins__": {}}, {})  # nosec
            return ToolOutput(success=True, output=str(result))
        except ZeroDivisionError:
            return ToolOutput(success=False, error="除数不能为零")
        except Exception as e:
            return ToolOutput(success=False, error=f"计算错误: {e}")
