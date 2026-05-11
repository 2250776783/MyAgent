"""测试工具系统：BaseTool, ToolRegistry, 内置工具。"""

import pytest

from src.agent.tools import CalculatorTool, CurrentTimeTool
from src.agent.tools.base import BaseTool, ToolRegistry


class SimpleTool(BaseTool):
    name: str = "test_tool"
    description: str = "一个测试工具"

    def run(self, **kwargs: str) -> str:
        return f"executed with {kwargs}"


class TestBaseTool:
    def test_to_openai_tool_format(self) -> None:
        tool = SimpleTool()
        result = tool.to_openai_tool()
        assert result["type"] == "function"
        assert result["function"]["name"] == "test_tool"
        assert result["function"]["description"] == "一个测试工具"
        assert "parameters" in result["function"]


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)
        assert registry.get("test_tool") is tool

    def test_get_nonexistent_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        t1 = SimpleTool()
        t2 = CurrentTimeTool()
        registry.register(t1)
        registry.register(t2)
        tools = registry.list_tools()
        assert len(tools) == 2

    def test_to_openai_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(SimpleTool())
        result = registry.to_openai_tools()
        assert len(result) == 1
        assert result[0]["function"]["name"] == "test_tool"

    def test_register_empty(self) -> None:
        registry = ToolRegistry()
        assert registry.list_tools() == []
        assert registry.to_openai_tools() == []


class TestCurrentTimeTool:
    def test_run_returns_time_string(self) -> None:
        tool = CurrentTimeTool()
        result = tool.run()
        assert len(result) == 19  # "YYYY-MM-DD HH:MM:SS"

    def test_name_and_description(self) -> None:
        tool = CurrentTimeTool()
        assert tool.name == "current_time"
        assert tool.description


class TestCalculatorTool:
    def test_simple_addition(self) -> None:
        tool = CalculatorTool()
        assert tool.run(expression="1+2") == "3"

    def test_complex_expression(self) -> None:
        tool = CalculatorTool()
        assert tool.run(expression="(3+5)*2") == "16"

    def test_illegal_chars(self) -> None:
        tool = CalculatorTool()
        result = tool.run(expression="1+__import__('os')")
        assert "错误" in result

    def test_division(self) -> None:
        tool = CalculatorTool()
        assert float(tool.run(expression="10/3")) == pytest.approx(3.333, rel=1e-2)

    def test_divide_by_zero(self) -> None:
        tool = CalculatorTool()
        result = tool.run(expression="1/0")
        assert "错误" in result

    def test_empty_expression(self) -> None:
        tool = CalculatorTool()
        result = tool.run(expression="  ")
        assert "错误" in result

    def test_name_and_description(self) -> None:
        tool = CalculatorTool()
        assert tool.name == "calculator"
        assert tool.description
