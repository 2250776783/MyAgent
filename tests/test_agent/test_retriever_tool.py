"""测试 RetrieverTool。"""

from unittest.mock import MagicMock

import pytest

from src.agent.tools.capabilities import RetrieverTool
from src.agent.tools.base import ToolOutput


class TestRetrieverTool:
    def test_name_and_description(self) -> None:
        tool = RetrieverTool()
        assert tool.name == "retriever"
        assert tool.description

    def test_empty_query(self) -> None:
        tool = RetrieverTool()
        result = tool.run(query="")
        assert not result.success
        assert "不能为空" in result.error

    def test_no_engine(self) -> None:
        tool = RetrieverTool()
        result = tool.run(query="test")
        assert not result.success
        assert "未初始化" in result.error

    def test_engine_query_success(self) -> None:
        mock_engine = MagicMock()
        mock_engine.query.return_value = "这是答案"
        tool = RetrieverTool(rag_engine=mock_engine)
        result = tool.run(query="测试问题")
        assert result.success
        assert result.output == "这是答案"
        mock_engine.query.assert_called_once_with(
            question="测试问题", k=5, rerank_top_k=3
        )

    def test_engine_query_custom_k(self) -> None:
        mock_engine = MagicMock()
        mock_engine.query.return_value = "答案"
        tool = RetrieverTool(rag_engine=mock_engine)
        result = tool.run(query="问题", k=10, rerank_top_k=5)
        assert result.success
        mock_engine.query.assert_called_once_with(
            question="问题", k=10, rerank_top_k=5
        )

    def test_engine_query_failure(self) -> None:
        mock_engine = MagicMock()
        mock_engine.query.side_effect = RuntimeError("LLM 调用失败")
        tool = RetrieverTool(rag_engine=mock_engine)
        result = tool.run(query="问题")
        assert not result.success
        assert "LLM 调用失败" in result.error

    def test_to_openai_tool_includes_parameters(self) -> None:
        tool = RetrieverTool(rag_engine=MagicMock())
        schema = tool.to_openai_tool()
        params = schema["function"]["parameters"]
        assert "query" in params["properties"]
        assert params["required"] == ["query"]

    def test_args_schema(self) -> None:
        assert RetrieverTool.args_schema is not None
        schema = RetrieverTool.args_schema.model_json_schema()
        props = schema["properties"]
        assert "query" in props
        assert props["query"]["type"] == "string"
        assert "k" in props
        assert props["k"]["default"] == 5
        assert "rerank_top_k" in props
        assert props["rerank_top_k"]["default"] == 3
