"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Copy } from "lucide-react";
import type { LogEntry as LogEntryType } from "@/types/log";

const levelConfig: Record<string, { label: string; className: string; dot: string }> = {
  ERROR: { label: "ERROR", className: "bg-red-500/10 text-red-500 border-red-500/20", dot: "bg-red-500" },
  WARN: { label: "WARN", className: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20", dot: "bg-yellow-500" },
  INFO: { label: "INFO", className: "bg-blue-500/10 text-blue-500 border-blue-500/20", dot: "bg-blue-500" },
  DEBUG: { label: "DEBUG", className: "bg-muted text-muted-foreground border-transparent", dot: "bg-muted-foreground" },
};

interface Props {
  entry: LogEntryType;
}

export function LogEntry({ entry }: Props) {
  const [expanded, setExpanded] = useState(false);
  const config = levelConfig[entry.level] || levelConfig.DEBUG;

  const copyDetails = () => {
    const text = JSON.stringify(entry.details, null, 2);
    navigator.clipboard.writeText(text).catch(() => {});
  };

  return (
    <div className="group border-b border-border/50 transition-colors hover:bg-muted/20">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-2 text-left"
      >
        <span className="shrink-0">
          {expanded ? <ChevronDown className="h-3 w-3 text-muted-foreground" /> : <ChevronRight className="h-3 w-3 text-muted-foreground" />}
        </span>
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${config.dot}`} />
        <span className={`shrink-0 rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${config.className}`}>
          {config.label}
        </span>
        <span className="text-[10px] text-muted-foreground shrink-0 w-16 font-mono">
          {entry.timestamp.split("T")[1]?.split(".")[0] || entry.timestamp}
        </span>
        <span className="text-xs text-muted-foreground shrink-0 w-20 truncate">{entry.source}</span>
        <span className="text-xs flex-1 truncate">{entry.message}</span>
        {entry.trace_id && (
          <span className="text-[10px] text-muted-foreground font-mono shrink-0">
            {entry.trace_id.slice(0, 8)}
          </span>
        )}
      </button>
      {expanded && entry.details && Object.keys(entry.details).length > 0 && (
        <div className="border-t border-border/30 px-4 py-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-muted-foreground">详细信息</span>
            <button onClick={copyDetails} className="rounded p-1 text-muted-foreground hover:text-foreground">
              <Copy className="h-3 w-3" />
            </button>
          </div>
          <pre className="rounded-lg bg-muted p-3 text-[11px] font-mono leading-relaxed overflow-x-auto">
            {JSON.stringify(entry.details, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
