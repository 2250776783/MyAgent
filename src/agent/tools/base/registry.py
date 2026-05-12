"""Tool Registry 注册表。

提供工具的动态注册、查找、过滤和批量导出功能。
支持按 category 过滤和 capability 路由。
"""

from typing import Any

from .tool import BaseTool
from .errors import ToolNotFoundError


class ToolRegistry:
    """工具注册管理器。

    管理工具的注册、查找和批量导出。
    支持按能力域（category）过滤。

    Args:
        tools: 初始工具列表
    """

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """注册一个工具。

        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """注销一个工具。"""
        self._tools.pop(name, None)

    def get(self, name: str) -> BaseTool:
        """按名称获取工具。

        Args:
            name: 工具名称

        Returns:
            工具实例

        Raises:
            ToolNotFoundError: 未找到指定工具
        """
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"tool not found: {name}")
        return tool

    def list_tools(self) -> list[BaseTool]:
        """返回所有注册的工具。"""
        return list(self._tools.values())

    def filter_by_category(self, category: str) -> list[BaseTool]:
        """按能力域过滤工具。"""
        return [t for t in self._tools.values() if t.metadata.category == category]

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """将所有工具转为 OpenAI tool calling 格式。"""
        return [t.to_openai_tool() for t in self._tools.values()]

    def get_tool_descriptions(self) -> str:
        """获取纯文本工具描述（用于 ReActAgent 等场景）。"""
        lines = []
        for tool in self._tools.values():
            params = list(tool.args_schema.model_fields.keys())
            params_str = ", ".join(params) if params else "无参数"
            lines.append(f"{tool.name}({params_str}): {tool.description}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
