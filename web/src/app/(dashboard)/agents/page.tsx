"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, LayoutGrid, List, Bot } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { AgentCard } from "@/components/agents/agent-card";
import { agentsApi } from "@/api/agents";
import type { Agent } from "@/types/agent";

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");

  useEffect(() => {
    agentsApi.list().then((res) => {
      setAgents(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = agents.filter(
    (a) => !search || a.name.toLowerCase().includes(search.toLowerCase()) || a.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agent 管理</h1>
          <p className="mt-1 text-sm text-muted-foreground">管理和配置你的 AI Agent</p>
        </div>
        <button
          onClick={() => router.push("/agents/new")}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> 创建 Agent
        </button>
      </div>

      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索 Agent..."
            className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
          />
        </div>
        <div className="flex rounded-lg border">
          <button
            onClick={() => setView("grid")}
            className={`rounded-l-lg p-2 ${view === "grid" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
          <button
            onClick={() => setView("list")}
            className={`rounded-r-lg p-2 ${view === "list" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:text-foreground"}`}
          >
            <List className="h-4 w-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
            <Bot className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-sm font-medium">暂无 Agent</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {search ? "未找到匹配的 Agent" : "创建第一个 Agent 开始使用"}
          </p>
          {!search && (
            <button
              onClick={() => router.push("/agents/new")}
              className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              创建 Agent
            </button>
          )}
        </div>
      ) : (
        <div className={view === "grid"
          ? "grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          : "space-y-2"
        }>
          {filtered.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </PageContainer>
  );
}
