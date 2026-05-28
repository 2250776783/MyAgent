"use client";

import { useEffect, useRef } from "react";
import { LogEntry } from "./log-entry";
import type { LogEntry as LogEntryType } from "@/types/log";
import { ScrollText } from "lucide-react";

interface Props {
  entries: LogEntryType[];
  loading: boolean;
  autoScroll: boolean;
}

export function LogViewer({ entries, loading, autoScroll }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [entries, autoScroll]);

  if (loading) {
    return (
      <div className="rounded-xl border">
        <div className="space-y-0">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-10 animate-pulse border-b border-border/50 px-4 py-2">
              <div className="h-4 w-3/4 rounded bg-muted" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
          <ScrollText className="h-6 w-6 text-muted-foreground" />
        </div>
        <h3 className="mt-4 text-sm font-medium">暂无日志</h3>
        <p className="mt-1 text-xs text-muted-foreground">没有匹配的日志记录</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-card">
      <div className="flex items-center justify-between border-b bg-muted/20 px-4 py-2">
        <span className="text-xs text-muted-foreground">
          共 {entries.length} 条日志
        </span>
      </div>
      <div className="divide-y divide-border/50">
        {entries.map((entry) => (
          <LogEntry key={entry.id} entry={entry} />
        ))}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}
