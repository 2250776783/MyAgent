"""工具系统基类。

提供 BaseTool 抽象基类和 ToolRegistry 注册管理器。
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """工具基类。

    子类需定义 name、description 并实现 run 方法。
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, **kwargs: Any) -> str:  # noqa: ANN401
        """执行工具逻辑。"""

    def to_openai_tool(self) -> dict[str, Any]:
        """转换为 OpenAI tool calling 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }


class ToolRegistry:
    """工具注册管理器。

    管理工具的注册、查找和批量导出。
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具。"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """按名称查找工具。"""
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"tool not found: {name}")
        return tool

    def list_tools(self) -> list[BaseTool]:
        """返回所有注册的工具。"""
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """将所有工具转为 OpenAI tool calling 格式。"""
        return [t.to_openai_tool() for t in self._tools.values()]
