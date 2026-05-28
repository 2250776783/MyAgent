"use client";

import { useState } from "react";
import { useWorkflowStore } from "@/stores/workflow-store";

const nodeTypeMeta = [
  { type: "input", label: "输入", color: "bg-emerald-500" },
  { type: "llm", label: "LLM", color: "bg-blue-500" },
  { type: "tool", label: "工具", color: "bg-orange-500" },
  { type: "knowledge", label: "知识库", color: "bg-green-500" },
  { type: "code", label: "代码", color: "bg-purple-500" },
  { type: "condition", label: "条件", color: "bg-yellow-500" },
  { type: "output", label: "输出", color: "bg-cyan-500" },
] as const;

export function NodePalette() {
  const addNode = useWorkflowStore((s) => s.addNode);
  const [collapsed, setCollapsed] = useState(false);

  const handleDragStart = (e: React.DragEvent, type: string) => {
    e.dataTransfer.setData("application/reactflow", type);
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <div className="rounded-xl border bg-card p-3">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mb-2 flex w-full items-center justify-between text-xs font-semibold text-muted-foreground"
      >
        <span>节点</span>
        <span className="text-xs">{collapsed ? "+" : "-"}</span>
      </button>
      {!collapsed && (
        <div className="space-y-1">
          {nodeTypeMeta.map((meta) => (
            <button
              key={meta.type}
              draggable
              onDragStart={(e) => handleDragStart(e, meta.type)}
              onClick={() => addNode(meta.type, { x: 100 + Math.random() * 300, y: 100 + Math.random() * 200 })}
              className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs hover:bg-muted/50 transition-colors"
            >
              <span className={`h-2 w-2 rounded-full ${meta.color}`} />
              {meta.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
