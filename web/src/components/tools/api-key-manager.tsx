"use client";

import { useState } from "react";
import { Key, Eye, EyeOff, Copy, Plus, Trash2 } from "lucide-react";
import type { ApiKeyInfo } from "@/types/tool";

interface Props {
  keys: ApiKeyInfo[];
  onAdd: (name: string, key: string) => void;
  onDelete: (id: string) => void;
}

export function ApiKeyManager({ keys, onAdd, onDelete }: Props) {
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");
  const [newKey, setNewKey] = useState("");
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());

  const toggleVisible = (id: string) => {
    setVisibleKeys((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleAdd = () => {
    if (!newName.trim() || !newKey.trim()) return;
    onAdd(newName.trim(), newKey.trim());
    setNewName("");
    setNewKey("");
    setShowAdd(false);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {}
  };

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">API 密钥管理</h3>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-1 text-xs text-primary hover:underline"
        >
          <Plus className="h-3 w-3" /> 添加密钥
        </button>
      </div>

      {showAdd && (
        <div className="mb-3 rounded-lg border bg-muted/30 p-3 space-y-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="密钥名称"
            className="w-full rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
          />
          <input
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            placeholder="API Key"
            type="password"
            className="w-full rounded-lg border bg-background px-3 py-1.5 text-xs outline-none focus:border-primary/50"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowAdd(false)}
              className="rounded-lg px-3 py-1 text-xs text-muted-foreground hover:bg-muted"
            >
              取消
            </button>
            <button
              onClick={handleAdd}
              className="rounded-lg bg-primary px-3 py-1 text-xs text-primary-foreground hover:bg-primary/90"
            >
              添加
            </button>
          </div>
        </div>
      )}

      {keys.length === 0 ? (
        <p className="text-xs text-muted-foreground">暂无密钥</p>
      ) : (
        <div className="space-y-2">
          {keys.map((ak) => (
            <div key={ak.id} className="flex items-center justify-between rounded-lg border bg-card px-3 py-2">
              <div className="flex items-center gap-2">
                <Key className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-medium">{ak.name}</span>
                <span className="text-xs text-muted-foreground font-mono">
                  {visibleKeys.has(ak.id) ? "..." : ak.key_preview}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => toggleVisible(ak.id)} className="rounded p-1 text-muted-foreground hover:text-foreground">
                  {visibleKeys.has(ak.id) ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </button>
                <button onClick={() => copyToClipboard(ak.key_preview)} className="rounded p-1 text-muted-foreground hover:text-foreground">
                  <Copy className="h-3 w-3" />
                </button>
                <button onClick={() => onDelete(ak.id)} className="rounded p-1 text-muted-foreground hover:text-destructive">
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
