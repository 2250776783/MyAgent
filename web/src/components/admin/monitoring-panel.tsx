"use client";

import { Activity, Cpu, Users, MessageSquare, Database, Zap } from "lucide-react";
import type { SystemMetrics } from "@/types/admin";

interface Props {
  metrics: SystemMetrics;
}

export function MonitoringPanel({ metrics }: Props) {
  const cards = [
    { label: "用户总数", value: metrics.total_users, icon: Users, color: "text-blue-500", bg: "bg-blue-500/10" },
    { label: "活跃会话", value: metrics.active_sessions, icon: Activity, color: "text-green-500", bg: "bg-green-500/10" },
    { label: "Agent 数", value: metrics.total_agents, icon: Cpu, color: "text-purple-500", bg: "bg-purple-500/10" },
    { label: "消息总数", value: metrics.total_messages, icon: MessageSquare, color: "text-orange-500", bg: "bg-orange-500/10" },
    { label: "今日 API 调用", value: metrics.api_calls_today, icon: Zap, color: "text-yellow-500", bg: "bg-yellow-500/10" },
    { label: "今日 Token", value: metrics.tokens_used_today.toLocaleString(), icon: Database, color: "text-cyan-500", bg: "bg-cyan-500/10" },
  ];

  return (
    <div>
      <h3 className="mb-4 text-sm font-semibold">系统健康</h3>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="rounded-xl border bg-card p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">{card.label}</span>
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${card.bg}`}>
                <card.icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </div>
            <p className="mt-2 text-xl font-bold">{card.value}</p>
          </div>
        ))}
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <h4 className="mb-3 text-xs font-medium text-muted-foreground">系统资源</h4>
          <div className="space-y-3">
            <div>
              <div className="mb-1 flex justify-between text-xs">
                <span>CPU</span>
                <span className="text-muted-foreground">{metrics.cpu_usage}%</span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${metrics.cpu_usage}%` }} />
              </div>
            </div>
            <div>
              <div className="mb-1 flex justify-between text-xs">
                <span>内存</span>
                <span className="text-muted-foreground">{metrics.memory_usage}%</span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${metrics.memory_usage}%` }} />
              </div>
            </div>
          </div>
        </div>
        <div className="rounded-xl border bg-card p-4">
          <h4 className="mb-3 text-xs font-medium text-muted-foreground">系统信息</h4>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">运行时间</span>
              <span>{metrics.system_uptime}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">活跃会话</span>
              <span>{metrics.active_sessions}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">用户数量</span>
              <span>{metrics.total_users}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
