"use client";

import { memo } from "react";
import { Handle, Position } from "reactflow";
import { Cpu, Wrench, BookOpen, Code2, ArrowRightLeft, CornerDownLeft, GitBranch } from "lucide-react";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  llm: Cpu,
  tool: Wrench,
  knowledge: BookOpen,
  code: Code2,
  input: ArrowRightLeft,
  output: CornerDownLeft,
  condition: GitBranch,
};

const colorMap: Record<string, string> = {
  llm: "border-blue-500/30 bg-blue-500/5",
  tool: "border-orange-500/30 bg-orange-500/5",
  knowledge: "border-green-500/30 bg-green-500/5",
  code: "border-purple-500/30 bg-purple-500/5",
  input: "border-emerald-500/30 bg-emerald-500/5",
  output: "border-cyan-500/30 bg-cyan-500/5",
  condition: "border-yellow-500/30 bg-yellow-500/5",
};

const dotColor: Record<string, string> = {
  llm: "bg-blue-500",
  tool: "bg-orange-500",
  knowledge: "bg-green-500",
  code: "bg-purple-500",
  input: "bg-emerald-500",
  output: "bg-cyan-500",
  condition: "bg-yellow-500",
};

interface BaseNodeProps {
  data: { label: string; type: string; config?: Record<string, unknown> };
  selected: boolean;
}

function BaseNode({ data, selected }: BaseNodeProps) {
  const Icon = iconMap[data.type] || Cpu;
  const borderColor = colorMap[data.type] || "border-gray-500/30 bg-gray-500/5";
  const dot = dotColor[data.type] || "bg-gray-500";

  return (
    <div
      className={`rounded-xl border-2 px-4 py-3 min-w-[160px] shadow-sm transition-shadow ${
        borderColor
      } ${
        selected ? "ring-2 ring-primary shadow-md" : ""
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-border !w-3 !h-3 !border-2 !border-background" />
      <div className="flex items-center gap-2">
        <div className={`flex h-7 w-7 items-center justify-center rounded-lg ${dot} bg-opacity-20`}>
          {Icon && <Icon className={`h-4 w-4 ${dot.replace("bg-", "text-")}`} />}
        </div>
        <span className="text-sm font-medium">{data.label}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-border !w-3 !h-3 !border-2 !border-background" />
    </div>
  );
}

export const LLMNode = memo(function LLMNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
export const ToolNode = memo(function ToolNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
export const KnowledgeNode = memo(function KnowledgeNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
export const CodeNode = memo(function CodeNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
export const InputNode = memo(function InputNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
export const OutputNode = memo(function OutputNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
export const ConditionNode = memo(function ConditionNode(props: BaseNodeProps) {
  return <BaseNode {...props} />;
});
