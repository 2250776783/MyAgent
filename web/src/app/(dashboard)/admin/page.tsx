"use client";

import { useState, useEffect } from "react";
import { Shield, Users, Settings, Activity } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { MonitoringPanel } from "@/components/admin/monitoring-panel";
import { adminApi } from "@/api/admin";
import type { SystemMetrics } from "@/types/admin";

export default function AdminPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.getSystemMetrics().then((res) => {
      setMetrics(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <PageContainer>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-24 rounded-xl bg-muted" />
            ))}
          </div>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">管理后台</h1>
        <p className="mt-1 text-sm text-muted-foreground">系统监控和配置管理</p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <a
          href="/admin/users"
          className="flex items-center gap-4 rounded-xl border bg-card p-4 transition-all hover:shadow-md hover:border-accent-foreground/20"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
            <Users className="h-5 w-5 text-blue-500" />
          </div>
          <div>
            <p className="text-sm font-medium">用户管理</p>
            <p className="text-xs text-muted-foreground">查看和管理用户</p>
          </div>
        </a>
        <a
          href="/admin/config"
          className="flex items-center gap-4 rounded-xl border bg-card p-4 transition-all hover:shadow-md hover:border-accent-foreground/20"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
            <Settings className="h-5 w-5 text-purple-500" />
          </div>
          <div>
            <p className="text-sm font-medium">系统配置</p>
            <p className="text-xs text-muted-foreground">管理系统设置</p>
          </div>
        </a>
        <div className="flex items-center gap-4 rounded-xl border bg-card p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
            <Activity className="h-5 w-5 text-green-500" />
          </div>
          <div>
            <p className="text-sm font-medium">系统状态</p>
            <p className="text-xs text-muted-foreground">{metrics?.system_uptime || "-"}</p>
          </div>
        </div>
      </div>

      {metrics && <MonitoringPanel metrics={metrics} />}
    </PageContainer>
  );
}
