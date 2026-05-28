"use client";

import { useState, useEffect } from "react";
import { Search, Brain, Tag, Star, Clock, Filter } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { memoryApi } from "@/api/memory";
import { formatRelativeTime } from "@/lib/utils";
import type { Memory, MemoryType } from "@/types/memory";

const typeConfig: Record<MemoryType, { label: string; className: string }> = {
  episodic: { label: "情景记忆", className: "bg-blue-500/10 text-blue-500" },
  semantic: { label: "语义记忆", className: "bg-green-500/10 text-green-500" },
  procedural: { label: "程序记忆", className: "bg-purple-500/10 text-purple-500" },
};

function groupByDate(memories: Memory[]): Record<string, Memory[]> {
  const groups: Record<string, Memory[]> = {};
  for (const m of memories) {
    const date = m.created_at.split("T")[0];
    if (!groups[date]) groups[date] = [];
    groups[date].push(m);
  }
  return groups;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<MemoryType | "all">("all");
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    memoryApi.list().then((res) => {
      setMemories(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSearch = async () => {
    if (!search.trim()) return;
    setSearching(true);
    try {
      const res = await memoryApi.search({ query: search, limit: 20 });
      setMemories(res.data);
    } catch {} finally {
      setSearching(false);
    }
  };

  const filtered = typeFilter === "all"
    ? memories
    : memories.filter((m) => m.type === typeFilter);

  const grouped = groupByDate(filtered);

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">记忆</h1>
          <p className="mt-1 text-sm text-muted-foreground">浏览和管理 AI Agent 的长期记忆</p>
        </div>
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="搜索记忆..."
            className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
          />
        </div>
        <div className="flex gap-1 rounded-lg border bg-muted/30 p-1">
          {(["all", "episodic", "semantic", "procedural"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`rounded-md px-3 py-1 text-xs font-medium ${
                typeFilter === t ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {t === "all" ? "全部" : typeConfig[t].label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Brain className="h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-sm font-medium">暂无记忆</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {search ? "未找到匹配的记忆" : "Agent 运行后将自动生成记忆"}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([date, items]) => (
            <div key={date}>
              <h3 className="mb-3 text-xs font-medium text-muted-foreground">{date}</h3>
              <div className="space-y-2">
                {items.map((memory) => {
                  const config = typeConfig[memory.type];
                  return (
                    <div key={memory.id} className="rounded-lg border bg-card p-4 transition-colors hover:border-accent-foreground/20">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="mb-2 flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${config.className}`}>
                              <Brain className="h-3 w-3" />
                              {config.label}
                            </span>
                            {memory.importance_score > 0.7 && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-500">
                                <Star className="h-3 w-3" /> 重要
                              </span>
                            )}
                          </div>
                          <p className="text-sm leading-relaxed">{memory.content}</p>
                          {memory.tags && memory.tags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {memory.tags.map((tag) => (
                                <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                                  <Tag className="h-2.5 w-2.5" /> {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="shrink-0 text-right">
                          <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {formatRelativeTime(memory.created_at)}
                          </div>
                          <div className="mt-1 text-[10px] text-muted-foreground">
                            置信度: {(memory.confidence_score * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
