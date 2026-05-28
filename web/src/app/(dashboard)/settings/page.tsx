"use client";

import { useState } from "react";
import { PageContainer } from "@/components/shared/page-container";
import { ProfileForm } from "@/components/settings/profile-form";
import { PreferenceForm } from "@/components/settings/preference-form";
import { AppearanceToggle } from "@/components/settings/appearance-toggle";
import { User, Palette, Settings } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");

  const tabs = [
    { id: "profile", label: "个人资料", icon: User },
    { id: "appearance", label: "外观", icon: Palette },
    { id: "preferences", label: "偏好", icon: Settings },
  ] as const;

  return (
    <PageContainer className="max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">设置</h1>
        <p className="mt-1 text-sm text-muted-foreground">管理你的账户和偏好</p>
      </div>

      <div className="mb-6 flex gap-1 rounded-lg border bg-muted/30 p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === "profile" && (
        <div className="rounded-xl border bg-card p-6">
          <ProfileForm
            initialData={{ username: "admin", email: "admin@example.com" }}
            onSave={(data) => console.log("save profile", data)}
          />
        </div>
      )}
      {activeTab === "appearance" && (
        <div className="rounded-xl border bg-card p-6">
          <h3 className="mb-4 text-sm font-semibold">主题模式</h3>
          <AppearanceToggle />
        </div>
      )}
      {activeTab === "preferences" && (
        <div className="rounded-xl border bg-card p-6">
          <PreferenceForm onSave={(prefs) => console.log("save prefs", prefs)} />
        </div>
      )}
    </PageContainer>
  );
}
