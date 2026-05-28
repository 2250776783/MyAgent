"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Settings, Code2, Wrench, BookOpen, Bot } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { AgentForm } from "@/components/agents/agent-form";
import { agentsApi } from "@/api/agents";
import type { Agent } from "@/types/agent";

const tabs = [
  { id: "config", label: "配置", icon: Settings },
  { id: "prompt", label: "提示词", icon: Code2 },
  { id: "tools", label: "工具", icon: Wrench },
  { id: "knowledge", label: "知识库", icon: BookOpen },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>("config");

  useEffect(() => {
    agentsApi.get(id).then((res) => {
      setAgent(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <PageContainer>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="h-64 rounded-xl bg-muted" />
        </div>
      </PageContainer>
    );
  }

  if (!agent) {
    return (
      <PageContainer>
        <div className="flex flex-col items-center justify-center py-20">
          <Bot className="h-12 w-12 text-muted-foreground" />
          <h2 className="mt-4 text-lg font-semibold">Agent 不存在</h2>
          <p className="mt-1 text-sm text-muted-foreground">该 Agent 可能已被删除</p>
          <button
            onClick={() => router.push("/agents")}
            className="mt-4 flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <ArrowLeft className="h-4 w-4" /> 返回列表
          </button>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="max-w-5xl">
      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={() => router.push("/agents")}
          className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold">{agent.name}</h1>
          <p className="text-xs text-muted-foreground">{agent.description}</p>
        </div>
      </div>

      <div className="mb-6 flex gap-1 rounded-lg border bg-muted/30 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
              activeTab === tab.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="h-3.5 w-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "config" && <AgentForm initialData={agent} />}
      {activeTab === "prompt" && (
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold">系统提示词</h2>
          <pre className="rounded-lg bg-muted p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap">
            {agent.system_prompt}
          </pre>
        </div>
      )}
      {activeTab === "tools" && (
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold">已绑定的工具 ({agent.tools.length})</h2>
          {agent.tools.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂未绑定工具</p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2">
              {agent.tools.map((tool) => (
                <div key={tool} className="flex items-center gap-2 rounded-lg border bg-muted/30 p-3">
                  <Wrench className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{tool}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {activeTab === "knowledge" && (
        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-3 text-sm font-semibold">已绑定的知识库 ({agent.knowledge_base_ids.length})</h2>
          {agent.knowledge_base_ids.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂未绑定知识库</p>
          ) : (
            <div className="space-y-2">
              {agent.knowledge_base_ids.map((kid) => (
                <div key={kid} className="flex items-center gap-2 rounded-lg border bg-muted/30 p-3">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{kid}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </PageContainer>
  );
}
