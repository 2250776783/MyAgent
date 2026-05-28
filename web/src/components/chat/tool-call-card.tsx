"use client";

import type { ToolCallInfo } from "@/types/chat";
import { Wrench, Loader2, CheckCircle, XCircle, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

interface Props {
  toolCall: ToolCallInfo;
}

const statusConfig = {
  pending: { icon: Wrench, className: "text-muted-foreground" },
  running: { icon: Loader2, className: "text-blue-500 animate-spin" },
  completed: { icon: CheckCircle, className: "text-green-500" },
  error: { icon: XCircle, className: "text-red-500" },
};

export function ToolCallCard({ toolCall }: Props) {
  const [expanded, setExpanded] = useState(false);
  const config = statusConfig[toolCall.status || "pending"];
  const Icon = config.icon;

  return (
    <div className="rounded-lg border border-muted bg-muted/30">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 p-2 text-left text-xs hover:bg-muted/50"
      >
        {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <Icon className={`h-3.5 w-3.5 ${config.className}`} />
        <span className="font-mono text-muted-foreground">{toolCall.name}</span>
        {toolCall.status === "running" && (
          <span className="text-blue-500">运行中...</span>
        )}
        {toolCall.status === "completed" && (
          <span className="text-green-500">完成</span>
        )}
        {toolCall.status === "error" && (
          <span className="text-red-500">失败</span>
        )}
      </button>
      {expanded && (
        <div className="border-t border-muted p-2 space-y-2">
          {toolCall.args && (
            <div>
              <div className="mb-1 text-xs text-muted-foreground">参数:</div>
              <pre className="overflow-x-auto rounded bg-muted p-2 text-xs">{toolCall.args}</pre>
            </div>
          )}
          {toolCall.output && (
            <div>
              <div className="mb-1 text-xs text-muted-foreground">结果:</div>
              <pre className="overflow-x-auto rounded bg-muted p-2 text-xs">{toolCall.output}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
