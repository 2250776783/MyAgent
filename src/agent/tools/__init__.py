"""Agent 工具系统。

提供 BaseTool 抽象基类、ToolRegistry 注册管理器，以及内置工具集。
"""

from .base import BaseTool, ToolRegistry
from .builtin import CalculatorTool, CurrentTimeTool

__all__ = ["BaseTool", "ToolRegistry", "CalculatorTool", "CurrentTimeTool"]
