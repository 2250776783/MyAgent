"use client";

import type { Agent } from "@/types/agent";
import { Bot, Cpu, Play, Pause, ExternalLink } from "lucide-react";

interface Props {
  agent: Agent;
  onToggle?: (id: string, status: Agent["status"]) => void;
}

const statusLabel: Record<string, { label: string; className: string }> = {
  active: { label: "活跃", className: "bg-green-500/10 text-green-500" },
  inactive: { label: "停用", className: "bg-muted text-muted-foreground" },
  error: { label: "错误", className: "bg-red-500/10 text-red-500" },
  deploying: { label: "部署中", className: "bg-blue-500/10 text-blue-500 animate-pulse" },
};

const providerColors: Record<string, string> = {
  openai: "bg-green-500/10 text-green-600",
  deepseek: "bg-blue-500/10 text-blue-600",
  claude: "bg-purple-500/10 text-purple-600",
  custom: "bg-orange-500/10 text-orange-600",
};

export function AgentCard({ agent, onToggle }: Props) {
  const status = statusLabel[agent.status] || statusLabel.inactive;

  return (
    <div className="group rounded-xl border bg-card p-4 transition-colors hover:border-accent-foreground/20">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{agent.name}</h3>
            <p className="text-xs text-muted-foreground line-clamp-1">{agent.description}</p>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${status.className}`}>
          {agent.status === "active" ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          {status.label}
        </span>
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${providerColors[agent.provider] || ""}`}>
          <Cpu className="h-3 w-3" />
          {agent.provider}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
          {agent.model}
        </span>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex -space-x-1">
          {agent.tools.slice(0, 3).map((tool) => (
            <span key={tool} className="inline-flex h-5 items-center rounded-full border bg-background px-1.5 text-[9px] text-muted-foreground">
              {tool.split(".").pop() || tool}
            </span>
          ))}
          {agent.tools.length > 3 && (
            <span className="inline-flex h-5 items-center rounded-full border bg-background px-1.5 text-[9px] text-muted-foreground">
              +{agent.tools.length - 3}
            </span>
          )}
        </div>
        <a
          href={`/agents/${agent.id}`}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          详情 <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}
