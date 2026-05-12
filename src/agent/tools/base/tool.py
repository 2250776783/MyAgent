"""BaseTool 抽象基类。

所有工具的基类，定义统一接口：
- name / description: 工具身份标识
- args_schema: Pydantic 参数 schema（自动生成 OpenAI tool calling 格式）
- metadata: 安全元数据（runtime 使用）
- run(): 执行入口，返回结构化 ToolOutput
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from .output import ToolOutput, ToolMetadata
from .schema import BaseToolArgs
from .errors import ToolExecutionError


class BaseTool(ABC):
    """工具抽象基类。

    所有具体工具必须继承此类，定义以下属性：
    - name: 工具名称（唯一标识）
    - description: 工具描述（LLM Planner 理解用）
    - args_schema: Pydantic 参数模型

    子类示例::

        class CalculatorArgs(BaseToolArgs):
            expression: str = Field(description="数学表达式")

        class CalculatorTool(BaseTool):
            name = "calculator"
            description = "执行数学计算，支持 +-*/ 和括号"
            args_schema = CalculatorArgs

            def run(self, expression: str, **kwargs: Any) -> ToolOutput:
                try:
                    result = eval(expression)
                    return ToolOutput(success=True, output=str(result))
                except Exception as e:
                    return ToolOutput(success=False, error=str(e))
    """

    name: str = ""
    description: str = ""
    args_schema: type[BaseModel] = BaseToolArgs
    metadata: ToolMetadata = ToolMetadata()

    def run(self, **kwargs: Any) -> ToolOutput:
        """执行工具逻辑。

        子类必须实现此方法，返回结构化 ToolOutput。
        抛出异常会被 runtime 层捕获并包装为 ToolOutput(success=False)。
        """
        try:
            return self._run(**kwargs)
        except ToolExecutionError:
            raise
        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    @abstractmethod
    def _run(self, **kwargs: Any) -> ToolOutput:
        """子类实现的具体工具逻辑。"""

    def to_openai_tool(self) -> dict[str, Any]:
        """转换为 OpenAI tool calling 格式。

        自动从 args_schema 的 Pydantic 模型生成 JSON Schema。
        """
        schema = self.args_schema.model_json_schema()
        schema.pop("title", None)
        schema.pop("$defs", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }
