"""Tool 核心抽象层。

提供 BaseTool 抽象基类、注册表、输出类型、参数 schema 和错误体系。
"""

from .tool import BaseTool
from .registry import ToolRegistry
from .output import ToolOutput, ToolMetadata
from .schema import BaseToolArgs, Field
from .errors import (
    ToolError,
    ToolTimeoutError,
    ToolPermissionError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
)

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "ToolOutput",
    "ToolMetadata",
    "BaseToolArgs",
    "Field",
    "ToolError",
    "ToolTimeoutError",
    "ToolPermissionError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolValidationError",
]
