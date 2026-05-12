"""Tool 参数 schema 定义。

所有工具的 args_schema 必须继承 BaseToolArgs，
使用 Pydantic Field 声明类型、描述和校验规则。

Example::

    class CalculatorArgs(BaseToolArgs):
        expression: str = Field(description="数学表达式，如 1+2")
"""

from pydantic import BaseModel, Field


class BaseToolArgs(BaseModel):
    """所有工具参数 schema 的基类。

    子类通过定义 Pydantic 字段来自动生成 JSON Schema，
    供 LLM function calling 使用。
    """
    pass


__all__ = ["BaseToolArgs", "Field"]
