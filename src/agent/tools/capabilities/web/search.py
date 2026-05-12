"""网页搜索工具。

基于 SerpApi 的 Google 网页搜索，返回结构化搜索结果。
"""

from typing import Any

from serpapi import SerpApiClient

from src.agent.tools.base import (
    BaseTool,
    BaseToolArgs,
    Field,
    ToolMetadata,
    ToolOutput,
)
from src.config.settings import settings


class WebSearchArgs(BaseToolArgs):
    """网页搜索参数：搜索关键词。"""

    query: str = Field(description="搜索关键词，如「今天天气怎么样」")


class WebSearchTool(BaseTool):
    """网页搜索工具。

    适用场景：
    - 实时信息查询（新闻、天气、股价等）
    - 知识库未覆盖的事实性问答
    - 最新事件的检索

    不适用场景：
    - 数学计算（请使用 calculator）
    - 内部知识库问答（请使用 retriever）
    """

    name: str = "web_search"
    description: str = "执行 Google 网页搜索，返回搜索结果摘要。传入 query 参数。"
    args_schema: type[WebSearchArgs] = WebSearchArgs
    metadata: ToolMetadata = ToolMetadata(
        readonly=True,
        destructive=False,
        category="web",
    )

    def _run(self, query: str, **kwargs: Any) -> ToolOutput:
        if not query or not query.strip():
            return ToolOutput(success=False, error="搜索关键词不能为空")

        api_key = settings.serpapi_api_key
        if not api_key:
            return ToolOutput(success=False, error="SERPAPI_API_KEY 未配置")

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "gl": "cn",
                "hl": "zh-CN",
            }

            client = SerpApiClient(params)
            results = client.get_dict()

            if "answer_box_list" in results:
                return ToolOutput(success=True, output="\n".join(results["answer_box_list"]))
            if "answer_box" in results and "answer" in results["answer_box"]:
                return ToolOutput(success=True, output=results["answer_box"]["answer"])
            if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
                return ToolOutput(success=True, output=results["knowledge_graph"]["description"])
            if "organic_results" in results and results["organic_results"]:
                snippets = [
                    f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                    for i, res in enumerate(results["organic_results"][:3])
                ]
                return ToolOutput(success=True, output="\n\n".join(snippets))

            return ToolOutput(success=True, output=f"未找到关于「{query}」的相关信息。")

        except Exception as e:
            return ToolOutput(success=False, error=f"搜索失败: {e}")
