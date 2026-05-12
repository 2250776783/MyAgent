"""安全策略工具。

提供工具执行前的安全检查、权限校验等能力。
"""

from src.agent.tools.base import ToolMetadata


def check_permission(metadata: ToolMetadata, user_level: str = "standard") -> bool:
    """检查当前用户是否有权限执行该工具。

    - admin: 可以执行所有工具
    - standard: 可以执行 readonly 工具和 destructive=False 的工具
    - restricted: 只能执行 readonly=True 的工具
    """
    if user_level == "admin":
        return True
    if user_level == "standard":
        return not (metadata.destructive and not metadata.readonly)
    if user_level == "restricted":
        return metadata.readonly
    return False


def should_confirm(metadata: ToolMetadata) -> bool:
    """判断工具执行前是否需要用户确认。"""
    return metadata.requires_confirmation or (metadata.destructive and not metadata.readonly)
