"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { Bot } from "lucide-react";
export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [email, setEmail] = useState("zhangsan001@qq.com");
  const [password, setPassword] = useState("password123");
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); clearError();
    try { await login(email, password); router.push("/dashboard"); } catch {}
  };
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary"><Bot className="h-7 w-7 text-primary-foreground" /></div>
        <h1 className="text-2xl font-bold">登录 MyAgent</h1>
        <p className="text-sm text-muted-foreground">登录您的 AI Agent 管理平台</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">邮箱</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" required />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">密码</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" required />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <button type="submit" disabled={isLoading} className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{isLoading ? "登录中..." : "登录"}</button>
        <div className="flex items-center justify-between text-sm">
          <Link href="/register" className="text-primary hover:underline">注册账号</Link>
          <Link href="/forgot-password" className="text-muted-foreground hover:underline">忘记密码?</Link>
        </div>
      </form>
      <p className="text-center text-xs text-muted-foreground">演示账号: zhangsan001@qq.com / password123</p>
    </div>
  );
}
