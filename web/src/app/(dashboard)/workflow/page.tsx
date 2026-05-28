"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, WorkflowIcon, Play, Pencil } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { workflowApi } from "@/api/workflow";
import { formatRelativeTime } from "@/lib/utils";
import type { Workflow } from "@/types/workflow";

export default function WorkflowListPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    workflowApi.list().then((res) => {
      setWorkflows(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = workflows.filter(
    (w) => !search || w.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">工作流</h1>
          <p className="mt-1 text-sm text-muted-foreground">可视化的 AI 工作流编排</p>
        </div>
        <button
          onClick={() => router.push("/workflow/new")}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> 创建工作流
        </button>
      </div>

      <div className="mb-4">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索工作流..."
            className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
            <WorkflowIcon className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-sm font-medium">暂无工作流</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {search ? "未找到匹配的工作流" : "创建一个工作流来编排 AI 任务"}
          </p>
          {!search && (
            <button
              onClick={() => router.push("/workflow/new")}
              className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              创建工作流
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((wf) => (
            <div
              key={wf.id}
              className="group rounded-xl border bg-card p-4 transition-all hover:shadow-md hover:border-accent-foreground/20"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <WorkflowIcon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold">{wf.name}</h3>
                    <p className="text-xs text-muted-foreground">{wf.nodes.length} 个节点</p>
                  </div>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    wf.is_active
                      ? "bg-green-500/10 text-green-500"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {wf.is_active ? "运行中" : "已停止"}
                </span>
              </div>
              {wf.description && (
                <p className="mt-3 text-xs text-muted-foreground line-clamp-2">{wf.description}</p>
              )}
              <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                <span>{formatRelativeTime(wf.updated_at)}</span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => router.push(`/workflow/${wf.id}`)}
                    className="rounded p-1 hover:bg-muted"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button className="rounded p-1 hover:bg-muted">
                    <Play className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </PageContainer>
  );
}
