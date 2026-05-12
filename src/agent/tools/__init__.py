"""Agent 工具系统。

提供 BaseTool 抽象基类、ToolRegistry 注册管理器、按能力域组织的工具集，
以及运行时执行器和安全策略。

使用方式::

    from src.agent.tools import CalculatorTool, CurrentTimeTool
    from src.agent.tools.base import BaseTool, ToolRegistry
"""

from .capabilities import CurrentTimeTool, CalculatorTool, WebSearchTool

__all__ = [
    "CalculatorTool",
    "CurrentTimeTool",
    "WebSearchTool",
]
