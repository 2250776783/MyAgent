"use client";

import { useState } from "react";
import { Settings, Plus, Trash2 } from "lucide-react";

interface ConfigItem {
  key: string;
  value: string;
  description?: string;
}

interface Props {
  configs: ConfigItem[];
  onSave: (configs: ConfigItem[]) => void;
}

export function SystemConfigForm({ configs, onSave }: Props) {
  const [items, setItems] = useState<ConfigItem[]>(configs);
  const [hasChanges, setHasChanges] = useState(false);

  const updateItem = (index: number, field: keyof ConfigItem, value: string) => {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)));
    setHasChanges(true);
  };

  const addItem = () => {
    setItems((prev) => [...prev, { key: "", value: "", description: "" }]);
    setHasChanges(true);
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave(items);
    setHasChanges(false);
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold">系统配置</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={addItem}
            className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs hover:bg-muted"
          >
            <Plus className="h-3 w-3" /> 添加
          </button>
          {hasChanges && (
            <button
              onClick={handleSave}
              className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90"
            >
              保存
            </button>
          )}
        </div>
      </div>
      <div className="space-y-2">
        {items.map((item, index) => (
          <div key={index} className="flex items-start gap-2 rounded-lg border bg-card p-3">
            <Settings className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="flex-1 grid grid-cols-3 gap-2">
              <input
                value={item.key}
                onChange={(e) => updateItem(index, "key", e.target.value)}
                placeholder="配置键"
                className="rounded-lg border bg-background px-3 py-1.5 text-xs font-mono outline-none focus:border-primary/50"
              />
              <input
                value={item.value}
                onChange={(e) => updateItem(index, "value", e.target.value)}
                placeholder="配置值"
                className="rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
              />
              <input
                value={item.description || ""}
                onChange={(e) => updateItem(index, "description", e.target.value)}
                placeholder="描述（可选）"
                className="rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
              />
            </div>
            <button onClick={() => removeItem(index)} className="rounded p-1 text-muted-foreground hover:text-destructive">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
