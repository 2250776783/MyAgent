"""Tool 系统核心数据类型。

提供结构化输出和安全元数据，替代自由文本返回。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolOutput:
    """结构化工具执行结果。

    所有工具的 run() 方法必须返回此类型，禁止返回自由文本。

    Attributes:
        success: 执行是否成功
        output: 成功时的输出文本
        error: 失败时的错误信息
        metadata: 执行元数据（耗时、来源等）
    """

    success: bool
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"错误: {self.error}"


@dataclass
class ToolMetadata:
    """工具安全元数据，用于 runtime 安全策略判断。

    Attributes:
        readonly: 工具是否只读（不会修改系统状态）
        destructive: 工具是否有破坏性（删除、写入等）
        requires_confirmation: 执行前是否需要用户确认
        requires_permission: 执行前是否需要权限检查
        timeout: 默认超时时间（秒）
        category: 工具能力域分类标识
    """

    readonly: bool = True
    destructive: bool = False
    requires_confirmation: bool = False
    requires_permission: bool = False
    timeout: int = 30
    category: str = "general"
