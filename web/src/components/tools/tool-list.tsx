"use client";

import { Wrench, Search, SlidersHorizontal } from "lucide-react";
import type { Tool } from "@/types/tool";

interface Props {
  tools: Tool[];
  onToggle: (id: string, enabled: boolean) => void;
  onSelect: (tool: Tool) => void;
  search: string;
  onSearchChange: (v: string) => void;
}

const categoryLabels: Record<string, string> = {
  search: "搜索",
  code: "代码",
  system: "系统",
  web: "网络",
  data: "数据处理",
  communication: "通讯",
  other: "其他",
};

export function ToolList({ tools, onToggle, onSelect, search, onSearchChange }: Props) {
  const filtered = tools.filter(
    (t) => !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase())
  );

  const grouped = filtered.reduce<Record<string, Tool[]>>((acc, t) => {
    const cat = t.category || "other";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(t);
    return acc;
  }, {});

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="搜索工具..."
            className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
          />
        </div>
      </div>

      {Object.keys(grouped).length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
            <Wrench className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-sm font-medium">暂无工具</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {search ? "未找到匹配的工具" : "没有可用的工具"}
          </p>
        </div>
      ) : (
        Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="mb-6">
            <h3 className="mb-3 text-xs font-medium text-muted-foreground">
              {categoryLabels[category] || category}
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((tool) => (
                <div
                  key={tool.id}
                  className="group rounded-xl border bg-card p-4 transition-all hover:shadow-md"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3" onClick={() => onSelect(tool)}>
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                        <Wrench className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium">{tool.name}</h4>
                        <p className="text-xs text-muted-foreground line-clamp-1">{tool.description}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => onToggle(tool.id, !tool.enabled)}
                      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${
                        tool.enabled ? "bg-primary" : "bg-input"
                      }`}
                    >
                      <span
                        className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${
                          tool.enabled ? "translate-x-4" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
