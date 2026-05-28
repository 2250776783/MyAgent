"use client";

import { useState, useEffect } from "react";
import { Wrench } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { ToolList } from "@/components/tools/tool-list";
import { ApiKeyManager } from "@/components/tools/api-key-manager";
import { toolsApi } from "@/api/tools";
import type { Tool, ApiKeyInfo } from "@/types/tool";

// Placeholder - API keys would come from a dedicated endpoint
const mockApiKeys: ApiKeyInfo[] = [
  { id: "key_1", name: "OpenAI", key_preview: "sk-...abc123", created_at: "2025-01-01T00:00:00Z", last_used: "2025-05-28T00:00:00Z" },
  { id: "key_2", name: "SerpApi", key_preview: "serp-...xyz789", created_at: "2025-02-15T00:00:00Z" },
];

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>(mockApiKeys);
  const [showKeys, setShowKeys] = useState(false);

  useEffect(() => {
    toolsApi.list().then((res) => {
      setTools(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleToggle = async (id: string, enabled: boolean) => {
    setTools((prev) => prev.map((t) => (t.id === id ? { ...t, enabled } : t)));
    try {
      await toolsApi.update(id, { enabled });
    } catch {
      setTools((prev) => prev.map((t) => (t.id === id ? { ...t, enabled: !enabled } : t)));
    }
  };

  const handleAddKey = (name: string, key: string) => {
    const newKey: ApiKeyInfo = {
      id: `key_${Date.now()}`,
      name,
      key_preview: key.slice(0, 8) + "...",
      created_at: new Date().toISOString(),
    };
    setApiKeys((prev) => [...prev, newKey]);
  };

  const handleDeleteKey = (id: string) => {
    setApiKeys((prev) => prev.filter((k) => k.id !== id));
  };

  return (
    <PageContainer className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">工具管理</h1>
        <p className="mt-1 text-sm text-muted-foreground">管理 Agent 可使用的工具和 API 密钥</p>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <button
          onClick={() => setShowKeys(false)}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
            !showKeys ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          工具列表
        </button>
        <button
          onClick={() => setShowKeys(true)}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
            showKeys ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          API 密钥
        </button>
      </div>

      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : showKeys ? (
        <div className="rounded-xl border bg-card p-4">
          <ApiKeyManager keys={apiKeys} onAdd={handleAddKey} onDelete={handleDeleteKey} />
        </div>
      ) : (
        <ToolList
          tools={tools}
          onToggle={handleToggle}
          onSelect={setSelectedTool}
          search={search}
          onSearchChange={setSearch}
        />
      )}
    </PageContainer>
  );
}
