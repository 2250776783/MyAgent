"use client";

import { useState } from "react";
import { Globe, Clock, Bell } from "lucide-react";

interface Props {
  onSave: (prefs: { language: string; timezone: string; notifications: boolean }) => void;
}

export function PreferenceForm({ onSave }: Props) {
  const [language, setLanguage] = useState("zh-CN");
  const [timezone, setTimezone] = useState("Asia/Shanghai");
  const [notifications, setNotifications] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);

  const handleSave = () => {
    onSave({ language, timezone, notifications });
    setHasChanges(false);
  };

  const markChanged = () => setHasChanges(true);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Globe className="h-4 w-4 text-muted-foreground" />
        <div className="flex-1">
          <label className="mb-1 block text-xs text-muted-foreground">语言</label>
          <select
            value={language}
            onChange={(e) => { setLanguage(e.target.value); markChanged(); }}
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none"
          >
            <option value="zh-CN">中文（简体）</option>
            <option value="en-US">English (US)</option>
            <option value="ja-JP">日本語</option>
          </select>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <div className="flex-1">
          <label className="mb-1 block text-xs text-muted-foreground">时区</label>
          <select
            value={timezone}
            onChange={(e) => { setTimezone(e.target.value); markChanged(); }}
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none"
          >
            <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
            <option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</option>
            <option value="America/New_York">America/New_York (UTC-5)</option>
            <option value="Europe/London">Europe/London (UTC+0)</option>
          </select>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">通知</span>
        </div>
        <button
          onClick={() => { setNotifications(!notifications); setHasChanges(true); }}
          className={`relative h-5 w-9 rounded-full transition-colors ${notifications ? "bg-primary" : "bg-input"}`}
        >
          <span className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${notifications ? "translate-x-4" : ""}`} />
        </button>
      </div>
      {hasChanges && (
        <button
          onClick={handleSave}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          保存偏好
        </button>
      )}
    </div>
  );
}
