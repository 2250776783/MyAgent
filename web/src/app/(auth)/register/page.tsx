"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { Bot } from "lucide-react";
export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError } = useAuthStore();
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "" });
  const [confirmError, setConfirmError] = useState("");
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirm) {
      setConfirmError("两次密码输入不一致");
      return;
    }
    setConfirmError("");
    clearError();
    try { await register(form.username, form.email, form.password); router.push("/dashboard"); } catch {}
  };
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary"><Bot className="h-7 w-7 text-primary-foreground" /></div>
        <h1 className="text-2xl font-bold">注册 MyAgent</h1>
        <p className="text-sm text-muted-foreground">创建您的 AI Agent 管理账号</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input placeholder="用户名" value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />
        <input type="email" placeholder="邮箱" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />
        <input type="password" placeholder="密码" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />
        <input type="password" placeholder="确认密码" value={form.confirm} onChange={(e) => setForm({...form, confirm: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />
        {confirmError && <p className="text-sm text-destructive">{confirmError}</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}
        <button type="submit" disabled={isLoading} className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{isLoading ? "注册中..." : "注册"}</button>
        <p className="text-center text-sm text-muted-foreground">已有账号? <Link href="/login" className="text-primary hover:underline">登录</Link></p>
      </form>
    </div>
  );
}
