"""Prompt Assembly - Prompt 组装器。

将 ContextAssembly 渲染为 LLM prompt 字符串。
支持阶段排序、格式化、token 明细统计。
"""

from __future__ import annotations

from src.llm import TokenCounter

from .types import ContextAssembly, ContextType, InjectionPhase


class PromptAssembler:
    """Prompt 组装器。

    按注入阶段排序各 ContextSegment，渲染为结构化 prompt。::

        <system_prompt>

        === 当前目标 ===
        ...

        === 任务进度 ===
        ...

        === 相关记忆 ===
        ...

        === 对话历史 ===
        ...
    """

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self.token_counter = token_counter or TokenCounter()

    def assemble(self, assembly: ContextAssembly) -> str:
        """组装最终 prompt。"""
        return assembly.to_prompt()

    def get_token_breakdown(self, assembly: ContextAssembly) -> str:
        """生成 token 使用明细。"""
        lines = ["=== Prompt Token 明细 ==="]
        for seg in assembly.segments:
            pct = (seg.token_count / max(assembly.total_tokens, 1)) * 100
            lines.append(
                f"  [{seg.type.value:12s}] {seg.token_count:6d} tokens "
                f"({pct:4.1f}%) pri={seg.priority:.2f}"
            )
        lines.append(f"  {'总计':12s} {assembly.total_tokens:6d} tokens")
        lines.append(f"  压缩: {assembly.compressed_count} | 丢弃: {assembly.dropped_count}")
        return "\n".join(lines)
