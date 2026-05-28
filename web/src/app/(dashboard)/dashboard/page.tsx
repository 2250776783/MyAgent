"use client";

import { useEffect, useState } from "react";
import { Bot, MessageSquare, Workflow, Database, TrendingUp } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { PageContainer } from "@/components/shared/page-container";
import { StatsCard } from "@/components/dashboard/stats-card";

const overviewData = [
  { name: "第1周", messages: 240, agents: 12 },
  { name: "第2周", messages: 456, agents: 18 },
  { name: "第3周", messages: 389, agents: 25 },
  { name: "第4周", messages: 678, agents: 32 },
  { name: "第5周", messages: 890, agents: 40 },
  { name: "第6周", messages: 1200, agents: 48 },
  { name: "第7周", messages: 1560, agents: 55 },
];

const recentActivity = [
  { type: "chat", text: "用户与 AI 助手进行对话", time: "2 分钟前" },
  { type: "agent", text: "Agent \"数据分析师\" 配置已更新", time: "15 分钟前" },
  { type: "knowledge", text: "新文档 \"技术手册 v3\" 已上传", time: "1 小时前" },
  { type: "workflow", text: "工作流 \"数据处理\" 执行完成", time: "2 小时前" },
  { type: "memory", text: "记忆系统完成每日反思", time: "3 小时前" },
  { type: "tool", text: "工具 \"WebSearch\" 调用次数达 1000", time: "5 小时前" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalMessages: "5,413",
    totalChats: "1,247",
    totalAgents: "55",
    avgResponseTime: "1.2s",
  });

  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">仪表盘</h1>
        <p className="text-sm text-muted-foreground mt-1">
          欢迎回来，以下是系统运行概览
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="总消息数"
          value={stats.totalMessages}
          description="累计消息量"
          trend={{ value: 12.5, positive: true }}
          icon={<MessageSquare className="h-5 w-5" />}
        />
        <StatsCard
          title="总会话数"
          value={stats.totalChats}
          description="活跃对话"
          trend={{ value: 8.2, positive: true }}
          icon={<Bot className="h-5 w-5" />}
        />
        <StatsCard
          title="Agent 数量"
          value={stats.totalAgents}
          description="已部署 Agent"
          trend={{ value: 15, positive: true }}
          icon={<Workflow className="h-5 w-5" />}
        />
        <StatsCard
          title="平均响应"
          value={stats.avgResponseTime}
          description="API 响应时间"
          trend={{ value: 3.1, positive: false }}
          icon={<TrendingUp className="h-5 w-5" />}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-sm font-semibold">消息趋势</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={overviewData}>
                <defs>
                  <linearGradient id="msgGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="messages"
                  stroke="hsl(var(--primary))"
                  fill="url(#msgGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <h2 className="mb-4 text-sm font-semibold">最近活动</h2>
          <div className="space-y-3">
            {recentActivity.map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-primary/60" />
                <div>
                  <p className="text-xs text-foreground">{item.text}</p>
                  <p className="text-[10px] text-muted-foreground">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-sm font-semibold">Agent 增长趋势</h2>
        <div className="h-60">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={overviewData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Line
                type="monotone"
                dataKey="agents"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </PageContainer>
  );
}
