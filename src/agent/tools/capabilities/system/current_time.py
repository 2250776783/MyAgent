"""当前时间工具。

返回服务器本地日期和时间，无需参数。
适用于 LLM 需要知道当前时间或日期的场景。
"""

import datetime
from typing import Any

from src.agent.tools.base import (
    BaseTool,
    ToolOutput,
    ToolMetadata,
    BaseToolArgs,
)


class CurrentTimeTool(BaseTool):
    """获取当前日期和时间。

    适用场景：
    - LLM 需要知道当前日期
    - 计算时间差
    - 判断是否在某个时间范围内

    不适用场景：
    - 获取其他时区的时间（默认返回本地时间）
    - 获取精确到毫秒的高精度时间
    """

    name: str = "current_time"
    description: str = "获取当前本地日期和时间"
    args_schema: type[BaseToolArgs] = BaseToolArgs
    metadata: ToolMetadata = ToolMetadata(
        readonly=True,
        destructive=False,
        category="system",
    )

    def _run(self, **kwargs: Any) -> ToolOutput:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ToolOutput(success=True, output=now)
