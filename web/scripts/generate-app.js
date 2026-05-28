const fs = require("fs");
const path = require("path");
const SRC = path.resolve(__dirname, "..", "src");

function w(f, lines) {
  const full = path.join(SRC, f);
  const d = path.dirname(full);
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(full, lines.join("\n") + "\n", "utf8");
  console.log("  + " + f);
}

function sq(s) { return "'" + s + "'"; }
function dq(s) { return '"' + s + '"'; }

// Helper to write JSX with proper string escaping
function jsx(str) { return str; }

// ===== 1. Root layout =====
w("app/layout.tsx", [
  `import type { Metadata } from "next";`,
  `import { Inter } from "next/font/google";`,
  `import "./globals.css";`,
  `import { ThemeProvider } from "@/providers/theme-provider";`,
  `import { QueryProvider } from "@/providers/query-provider";`,
  `const inter = Inter({ subsets: ["latin"] });`,
  `export const metadata: Metadata = {`,
  `  title: "MyAgent - AI Agent 平台",`,
  `  description: "现代化 AI Agent 管理平台",`,
  `};`,
  `export default function RootLayout({ children }: { children: React.ReactNode }) {`,
  `  return (`,
  `    <html lang="zh-CN" suppressHydrationWarning>`,
  `      <body className={inter.className}>`,
  `        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>`,
  `          <QueryProvider>{children}</QueryProvider>`,
  `        </ThemeProvider>`,
  `      </body>`,
  `    </html>`,
  `  );`,
  `}`,
]);

w("app/page.tsx", [
  `import { redirect } from "next/navigation";`,
  `export default function Home() { redirect("/dashboard"); }`,
]);

w("app/not-found.tsx", [
  `import Link from "next/link";`,
  `export default function NotFound() {`,
  `  return (`,
  `    <div className="flex min-h-screen flex-col items-center justify-center gap-4">`,
  `      <h1 className="text-4xl font-bold">404</h1>`,
  `      <p className="text-muted-foreground">页面未找到</p>`,
  `      <Link href="/dashboard" className="text-primary hover:underline">返回首页</Link>`,
  `    </div>`,
  `  );`,
  `}`,
]);

w("app/error.tsx", [
  `"use client";`,
  `export default function Error({ reset }: { error: Error; reset: () => void }) {`,
  `  return (`,
  `    <div className="flex min-h-screen flex-col items-center justify-center gap-4">`,
  `      <h2 className="text-2xl font-bold">出错了</h2>`,
  `      <button onClick={reset} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">重试</button>`,
  `    </div>`,
  `  );`,
  `}`,
]);

// ===== 2. Middleware =====
w("middleware.ts", [
  `import { NextResponse } from "next/server";`,
  `import type { NextRequest } from "next/server";`,
  `const authPaths = ["/login", "/register", "/forgot-password"];`,
  `const adminPaths = ["/admin"];`,
  `export function middleware(request: NextRequest) {`,
  `  const { pathname } = request.nextUrl;`,
  `  const token = request.cookies.get("access_token")?.value;`,
  `  if (pathname.startsWith("/_next") || pathname.startsWith("/favicon")) return NextResponse.next();`,
  `  if (token && authPaths.some((p) => pathname.startsWith(p)))`,
  `    return NextResponse.redirect(new URL("/dashboard", request.url));`,
  `  if (!token && !authPaths.some((p) => pathname.startsWith(p)))`,
  `    return NextResponse.redirect(new URL("/login", request.url));`,
  `  if (token && adminPaths.some((p) => pathname.startsWith(p))) {`,
  `    try { const p = JSON.parse(atob(token.split(".")[1])); if (p.role !== "ADMIN") return NextResponse.redirect(new URL("/dashboard", request.url)); }`,
  `    catch { return NextResponse.redirect(new URL("/login", request.url)); }`,
  `  }`,
  `  return NextResponse.next();`,
  `}`,
  `export const config = { matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"] };`,
]);

// ===== 3. Auth =====
w("app/(auth)/layout.tsx", [
  `export default function AuthLayout({ children }: { children: React.ReactNode }) {`,
  `  return (`,
  `    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-muted/50 to-background p-4">`,
  `      <div className="w-full max-w-md">{children}</div>`,
  `    </div>`,
  `  );`,
  `}`,
]);

w("app/(auth)/login/page.tsx", [
  `"use client";`,
  `import { useState } from "react";`,
  `import { useRouter } from "next/navigation";`,
  `import Link from "next/link";`,
  `import { useAuthStore } from "@/stores/auth-store";`,
  `import { Bot } from "lucide-react";`,
  `export default function LoginPage() {`,
  `  const router = useRouter();`,
  `  const { login, isLoading, error, clearError } = useAuthStore();`,
  `  const [email, setEmail] = useState("admin@myagent.ai");`,
  `  const [password, setPassword] = useState("password");`,
  `  const handleSubmit = async (e: React.FormEvent) => {`,
  `    e.preventDefault(); clearError();`,
  `    try { await login(email, password); router.push("/dashboard"); } catch {}`,
  `  };`,
  `  return (`,
  `    <div className="space-y-6">`,
  `      <div className="flex flex-col items-center gap-2 text-center">`,
  `        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary"><Bot className="h-7 w-7 text-primary-foreground" /></div>`,
  `        <h1 className="text-2xl font-bold">登录 MyAgent</h1>`,
  `        <p className="text-sm text-muted-foreground">登录您的 AI Agent 管理平台</p>`,
  `      </div>`,
  `      <form onSubmit={handleSubmit} className="space-y-4">`,
  `        <div className="space-y-2">`,
  `          <label className="text-sm font-medium">邮箱</label>`,
  `          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" required />`,
  `        </div>`,
  `        <div className="space-y-2">`,
  `          <label className="text-sm font-medium">密码</label>`,
  `          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" required />`,
  `        </div>`,
  `        {error && <p className="text-sm text-destructive">{error}</p>}`,
  `        <button type="submit" disabled={isLoading} className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{isLoading ? "登录中..." : "登录"}</button>`,
  `        <div className="flex items-center justify-between text-sm">`,
  `          <Link href="/register" className="text-primary hover:underline">注册账号</Link>`,
  `          <Link href="/forgot-password" className="text-muted-foreground hover:underline">忘记密码?</Link>`,
  `        </div>`,
  `      </form>`,
  `      <p className="text-center text-xs text-muted-foreground">演示账号: admin@myagent.ai / 任意密码</p>`,
  `    </div>`,
  `  );`,
  `}`,
]);

w("app/(auth)/register/page.tsx", [
  `"use client";`,
  `import { useState } from "react";`,
  `import { useRouter } from "next/navigation";`,
  `import Link from "next/link";`,
  `import { useAuthStore } from "@/stores/auth-store";`,
  `import { Bot } from "lucide-react";`,
  `export default function RegisterPage() {`,
  `  const router = useRouter();`,
  `  const { register, isLoading, error, clearError } = useAuthStore();`,
  `  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "" });`,
  `  const handleSubmit = async (e: React.FormEvent) => {`,
  `    e.preventDefault(); if (form.password !== form.confirm) return;`,
  `    clearError(); try { await register(form.username, form.email, form.password); router.push("/dashboard"); } catch {}`,
  `  };`,
  `  return (`,
  `    <div className="space-y-6">`,
  `      <div className="flex flex-col items-center gap-2 text-center">`,
  `        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary"><Bot className="h-7 w-7 text-primary-foreground" /></div>`,
  `        <h1 className="text-2xl font-bold">注册 MyAgent</h1>`,
  `        <p className="text-sm text-muted-foreground">创建您的 AI Agent 管理账号</p>`,
  `      </div>`,
  `      <form onSubmit={handleSubmit} className="space-y-4">`,
  `        <input placeholder="用户名" value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />`,
  `        <input type="email" placeholder="邮箱" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />`,
  `        <input type="password" placeholder="密码" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />`,
  `        <input type="password" placeholder="确认密码" value={form.confirm} onChange={(e) => setForm({...form, confirm: e.target.value})} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />`,
  `        {error && <p className="text-sm text-destructive">{error}</p>}`,
  `        <button type="submit" disabled={isLoading} className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{isLoading ? "注册中..." : "注册"}</button>`,
  `        <p className="text-center text-sm text-muted-foreground">已有账号? <Link href="/login" className="text-primary hover:underline">登录</Link></p>`,
  `      </form>`,
  `    </div>`,
  `  );`,
  `}`,
]);

w("app/(auth)/forgot-password/page.tsx", [
  `"use client";`,
  `import { useState } from "react";`,
  `import Link from "next/link";`,
  `import { Bot, ArrowLeft } from "lucide-react";`,
  `export default function ForgotPasswordPage() {`,
  `  const [email, setEmail] = useState("");`,
  `  const [sent, setSent] = useState(false);`,
  `  return (`,
  `    <div className="space-y-6">`,
  `      <div className="flex flex-col items-center gap-2 text-center">`,
  `        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary"><Bot className="h-7 w-7 text-primary-foreground" /></div>`,
  `        <h1 className="text-2xl font-bold">忘记密码</h1>`,
  `        <p className="text-sm text-muted-foreground">重置您的账号密码</p>`,
  `      </div>`,
  `      {sent ? (`,
  `        <div className="text-center space-y-4">`,
  `          <p className="text-sm text-muted-foreground">重置链接已发送到 {email}，请查看邮箱</p>`,
  `          <Link href="/login" className="inline-flex items-center gap-2 text-sm text-primary hover:underline"><ArrowLeft className="h-4 w-4" />返回登录</Link>`,
  `        </div>`,
  `      ) : (`,
  `        <form onSubmit={(e) => { e.preventDefault(); setSent(true); }} className="space-y-4">`,
  `          <input type="email" placeholder="输入注册邮箱" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2 text-sm" required />`,
  `          <button type="submit" className="w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">发送重置链接</button>`,
  `          <Link href="/login" className="flex items-center justify-center gap-2 text-sm text-muted-foreground hover:underline"><ArrowLeft className="h-4 w-4" />返回登录</Link>`,
  `        </form>`,
  `      )}`,
  `    </div>`,
  `  );`,
  `}`,
]);

// ===== 4. Dashboard layout =====
w("app/(dashboard)/layout.tsx", [
  `"use client";`,
  `import { useEffect } from "react";`,
  `import { useRouter } from "next/navigation";`,
  `import { useAuthStore } from "@/stores/auth-store";`,
  `import { useUiStore } from "@/stores/ui-store";`,
  `import { AppSidebar } from "@/components/layout/app-sidebar";`,
  `import { AppHeader } from "@/components/layout/app-header";`,
  `export default function DashboardLayout({ children }: { children: React.ReactNode }) {`,
  `  const { isAuthenticated, loadFromStorage } = useAuthStore();`,
  `  const router = useRouter();`,
  `  const sidebarOpen = useUiStore((s) => s.sidebarOpen);`,
  `  useEffect(() => { loadFromStorage(); }, []);`,
  `  useEffect(() => {`,
  `    if (typeof window !== "undefined" && !isAuthenticated) {`,
  `      const token = localStorage.getItem("access_token");`,
  `      if (!token) router.push("/login");`,
  `    }`,
  `  }, [isAuthenticated, router]);`,
  `  return (`,
  `    <div className="flex h-screen overflow-hidden bg-background">`,
  `      <AppSidebar />`,
  `      <div className="flex flex-1 flex-col overflow-hidden">`,
  `        <AppHeader />`,
  `        <main className="flex-1 overflow-y-auto p-6">`,
  `          <div className="mx-auto max-w-7xl">{children}</div>`,
  `        </main>`,
  `      </div>`,
  `      {sidebarOpen && <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => useUiStore.getState().setSidebarOpen(false)} />}`,
  `    </div>`,
  `  );`,
  `}`,
]);

console.log("Done: " + 15 + " files created");
