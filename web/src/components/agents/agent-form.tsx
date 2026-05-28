"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Save, ArrowLeft } from "lucide-react";
import { agentsApi } from "@/api/agents";
import type { Agent, AgentFormValues, ModelProvider } from "@/types/agent";

const MODEL_OPTIONS = [
  { provider: "openai", models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] },
  { provider: "deepseek", models: ["deepseek-chat", "deepseek-reasoner"] },
  { provider: "claude", models: ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"] },
  { provider: "custom", models: ["custom-model"] },
] as const;

const DEFAULT_VALUES: AgentFormValues = {
  name: "",
  description: "",
  model: "gpt-4o",
  provider: "openai",
  temperature: 0.7,
  max_tokens: 4096,
  top_p: 1,
  system_prompt: "你是一个有用的 AI 助手。",
  tools: [],
  memory_enabled: true,
  knowledge_base_ids: [],
};

interface Props {
  initialData?: Agent;
}

export function AgentForm({ initialData }: Props) {
  const router = useRouter();
  const [form, setForm] = useState<AgentFormValues>(() => {
    if (initialData) {
      return {
        name: initialData.name,
        description: initialData.description,
        model: initialData.model,
        provider: initialData.provider,
        temperature: initialData.temperature,
        max_tokens: initialData.max_tokens,
        top_p: initialData.top_p,
        system_prompt: initialData.system_prompt,
        tools: initialData.tools,
        memory_enabled: initialData.memory_enabled,
        knowledge_base_ids: initialData.knowledge_base_ids,
      };
    }
    return DEFAULT_VALUES;
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenCount, setTokenCount] = useState(() => estimateTokens(DEFAULT_VALUES.system_prompt));

  const updateField = <K extends keyof AgentFormValues>(key: K, value: AgentFormValues[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (key === "system_prompt") {
      setTokenCount(estimateTokens(value as string));
    }
    if (key === "provider") {
      const providerOpts = MODEL_OPTIONS.find((o) => o.provider === value);
      if (providerOpts) {
        setForm((prev) => ({ ...prev, provider: value as ModelProvider, model: providerOpts.models[0] }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (initialData) {
        await agentsApi.update(initialData.id, form);
      } else {
        await agentsApi.create(form);
      }
      router.push("/agents");
    } catch {
      setError("保存失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  const currentModels = MODEL_OPTIONS.find((o) => o.provider === form.provider)?.models || [];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      {/* Basic Info */}
      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-sm font-semibold">基本信息</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <label className="text-xs font-medium">名称</label>
            <input
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="Agent 名称"
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50"
              required
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <label className="text-xs font-medium">描述</label>
            <textarea
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              placeholder="Agent 描述"
              rows={2}
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50 resize-none"
            />
          </div>
        </div>
      </section>

      {/* Model Config */}
      <section className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-sm font-semibold">模型参数</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-medium">提供商</label>
            <select
              value={form.provider}
              onChange={(e) => updateField("provider", e.target.value as ModelProvider)}
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50"
            >
              {MODEL_OPTIONS.map((opt) => (
                <option key={opt.provider} value={opt.provider}>{opt.provider}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium">模型</label>
            <select
              value={form.model}
              onChange={(e) => updateField("model", e.target.value)}
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50"
            >
              {currentModels.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium">Temperature ({form.temperature})</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={form.temperature}
              onChange={(e) => updateField("temperature", parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium">Max Tokens</label>
            <input
              type="number"
              value={form.max_tokens}
              onChange={(e) => updateField("max_tokens", parseInt(e.target.value))}
              min={256}
              max={128000}
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium">Top P ({form.top_p})</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={form.top_p}
              onChange={(e) => updateField("top_p", parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium">记忆功能</label>
            <label className="flex items-center gap-2 rounded-lg border bg-background px-3 py-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={form.memory_enabled}
                onChange={(e) => updateField("memory_enabled", e.target.checked)}
              />
              启用长期记忆
            </label>
          </div>
        </div>
      </section>

      {/* System Prompt */}
      <section className="rounded-xl border bg-card p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold">系统提示词</h2>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
            ~{tokenCount} tokens
          </span>
        </div>
        <textarea
          value={form.system_prompt}
          onChange={(e) => updateField("system_prompt", e.target.value)}
          rows={10}
          className="w-full rounded-lg border bg-background p-3 font-mono text-xs leading-relaxed outline-none focus:border-primary/50 resize-y"
          style={{ minHeight: "200px" }}
        />
      </section>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> 返回
        </button>
        <button
          type="submit"
          disabled={saving || !form.name}
          className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {saving ? "保存中..." : (initialData ? "更新 Agent" : "创建 Agent")}
        </button>
      </div>
    </form>
  );
}

function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}
