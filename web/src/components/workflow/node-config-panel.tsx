"use client";

import { useWorkflowStore } from "@/stores/workflow-store";
import { Cpu, Wrench, BookOpen, Code2, GitBranch, Trash2 } from "lucide-react";

const configForms: Record<string, { key: string; label: string; type: "text" | "select" | "number" }[]> = {
  llm: [
    { key: "model", label: "模型", type: "select" },
    { key: "temperature", label: "温度", type: "number" },
    { key: "system_prompt", label: "系统提示词", type: "text" },
  ],
  tool: [
    { key: "tool_name", label: "工具名称", type: "select" },
  ],
  knowledge: [
    { key: "knowledge_base", label: "知识库", type: "select" },
    { key: "top_k", label: "检索数量", type: "number" },
  ],
  code: [
    { key: "code", label: "代码", type: "text" },
  ],
  condition: [
    { key: "condition", label: "条件表达式", type: "text" },
  ],
};

const typeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  llm: Cpu,
  tool: Wrench,
  knowledge: BookOpen,
  code: Code2,
  condition: GitBranch,
};

export function NodeConfigPanel() {
  const selectedNode = useWorkflowStore((s) => s.selectedNode);
  const updateNodeConfig = useWorkflowStore((s) => s.updateNodeConfig);
  const updateNodeLabel = useWorkflowStore((s) => s.updateNodeLabel);
  const deleteSelected = useWorkflowStore((s) => s.deleteSelected);

  if (!selectedNode) {
    return (
      <div className="rounded-xl border bg-card p-4 text-center text-xs text-muted-foreground">
        选择一个节点以配置
      </div>
    );
  }

  const nodeType = selectedNode.type || "llm";
  const config = (selectedNode.data.config || {}) as Record<string, unknown>;
  const fields = configForms[nodeType] || [];
  const Icon = typeIcons[nodeType] || Cpu;

  return (
    <div className="rounded-xl border bg-card">
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
            <input
              value={(selectedNode.data.label as string) || ""}
              onChange={(e) => updateNodeLabel(selectedNode.id, e.target.value)}
              className="text-sm font-medium bg-transparent outline-none border-none"
            />
          </div>
          <button
            onClick={deleteSelected}
            className="rounded p-1 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
      <div className="space-y-3 p-4">
        {fields.length === 0 && (
          <p className="text-xs text-muted-foreground">该节点无额外配置</p>
        )}
        {fields.map((field) => (
          <div key={field.key}>
            <label className="mb-1 block text-xs text-muted-foreground">{field.label}</label>
            {field.type === "text" ? (
              <textarea
                value={(config[field.key] as string) || ""}
                onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                className="w-full rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
                rows={3}
              />
            ) : field.type === "number" ? (
              <input
                type="number"
                value={(config[field.key] as number) ?? ""}
                onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: parseFloat(e.target.value) || 0 })}
                className="w-full rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
              />
            ) : (
              <input
                value={(config[field.key] as string) || ""}
                onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                className="w-full rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
