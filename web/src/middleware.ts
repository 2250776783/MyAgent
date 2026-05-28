import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const authPaths = ["/login", "/register", "/forgot-password"];
const adminPaths = ["/admin"];
const publicPaths = ["/_next", "/favicon", "/api"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 跳过静态资源和 API 路径
  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token = request.cookies.get("access_token")?.value;
  const isOnAuthPage = authPaths.some((p) => pathname.startsWith(p));
  const isOnAdminPage = adminPaths.some((p) => pathname.startsWith(p));

  // 根路径重定向
  if (pathname === "/") {
    return NextResponse.redirect(
      new URL(token ? "/dashboard" : "/login", request.url)
    );
  }

  // 已登录用户访问登录页 → 跳仪表盘
  if (token && isOnAuthPage) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // 未登录用户访问受保护页面 → 跳登录
  if (!token && !isOnAuthPage) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // 管理员权限校验
  if (token && isOnAdminPage) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      if (payload.role !== "ADMIN") {
        return NextResponse.redirect(new URL("/dashboard", request.url));
      }
    } catch {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
