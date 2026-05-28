"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, Settings } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { SystemConfigForm } from "@/components/admin/system-config-form";

const mockConfigs = [
  { key: "max_tokens_per_user", value: "1000000", description: "用户每日 Token 上限" },
  { key: "max_conversations", value: "100", description: "每个用户最大会话数" },
  { key: "enable_registration", value: "true", description: "是否开放注册" },
  { key: "default_user_role", value: "USER", description: "新用户默认角色" },
  { key: "log_retention_days", value: "30", description: "日志保留天数" },
  { key: "rate_limit_per_minute", value: "60", description: "每分钟 API 请求上限" },
];

export default function AdminConfigPage() {
  const router = useRouter();

  const handleSave = (configs: { key: string; value: string; description?: string }[]) => {
    // Mock save
  };

  return (
    <PageContainer>
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => router.push("/admin")} className="rounded-md p-1 text-muted-foreground hover:bg-accent">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">系统配置</h1>
          <p className="mt-1 text-sm text-muted-foreground">管理系统设置和参数</p>
        </div>
      </div>
      <div className="rounded-xl border bg-card p-4">
        <SystemConfigForm configs={mockConfigs} onSave={handleSave} />
      </div>
    </PageContainer>
  );
}
