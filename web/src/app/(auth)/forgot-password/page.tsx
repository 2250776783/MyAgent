"use client";
import { useState } from "react";
import Link from "next/link";
import { Bot, ArrowLeft } from "lucide-react";
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary"><Bot className="h-7 w-7 text-primary-foreground" /></div>
        <h1 className="text-2xl font-bold">忘记密码</h1>
        <p className="text-sm text-muted-foreground">重置您的账号密码</p>
      </div>
      {sent ? (
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">重置链接已发送到 {email}，请查看邮箱</p>
          <Link href="/login" className="inline-flex items-center gap-2 text-sm text-primary hover:underline"><ArrowLeft className="h-4 w-4" />返回登录</Link>
        </div>
      ) : (
        <form onSubmit={(e) => { e.preventDefault(); setSent(true); }} className="space-y-4">
          <input type="email" placeholder="输入注册邮箱" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />
          <button type="submit" className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">发送重置链接</button>
          <Link href="/login" className="flex items-center justify-center gap-2 text-sm text-muted-foreground hover:underline"><ArrowLeft className="h-4 w-4" />返回登录</Link>
        </form>
      )}
    </div>
  );
}
