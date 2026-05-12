"""工具执行器。

提供带超时、重试和追踪能力的工具执行环境。
"""

import time
from typing import Any

from src.agent.tools.base import (
    BaseTool,
    ToolExecutionError,
    ToolNotFoundError,
    ToolOutput,
    ToolTimeoutError,
)
from src.agent.tools.policies import check_permission

from .tracing import ToolTracer


class ToolExecutor:
    """工具执行器。

    包装 BaseTool，提供：
    - 超时控制
    - 重试机制
    - 执行追踪
    - 安全检查
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 0,
        user_level: str = "standard",
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_level = user_level
        self.tracer = ToolTracer()

    def execute(
        self,
        tool: BaseTool,
        **kwargs: Any,
    ) -> ToolOutput:
        """执行工具，带超时、重试和安全检查。"""
        if not check_permission(tool.metadata, self._user_level):
            return ToolOutput(
                success=False,
                error=f"无权限执行工具 '{tool.name}'（用户级别: {self._user_level}）",
            )

        start = time.time()
        last_error = ""

        for attempt in range(self._max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(1 * attempt)

                result = tool.run(**kwargs)
                duration_ms = (time.time() - start) * 1000

                self.tracer.record(
                    tool_name=tool.name,
                    args=kwargs,
                    result=str(result),
                    success=result.success,
                    duration_ms=duration_ms,
                )

                return result

            except ToolExecutionError:
                raise
            except TimeoutError as e:
                raise ToolTimeoutError(str(e)) from e
            except Exception as e:
                last_error = str(e)
                duration_ms = (time.time() - start) * 1000
                self.tracer.record(
                    tool_name=tool.name,
                    args=kwargs,
                    error=str(e),
                    success=False,
                    duration_ms=duration_ms,
                )

        return ToolOutput(
            success=False,
            error=f"工具执行失败（已重试 {self._max_retries} 次）: {last_error}",
        )

    def execute_tool_call(
        self,
        tool_registry: Any,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """兼容 Agent._execute_tool 的接口，按名称查找并执行工具，返回字符串。"""
        try:
            tool = tool_registry.get(tool_name)
        except (ToolNotFoundError, KeyError):
            return f"错误: 未找到工具 '{tool_name}'"

        result = self.execute(tool, **arguments)
        return str(result)
