"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Workflow,
  Library,
  Brain,
  Wrench,
  ScrollText,
  Settings,
  Shield,
  X,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { SIDEBAR_ITEMS } from "@/lib/constants";

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Workflow,
  Library,
  Brain,
  Wrench,
  ScrollText,
  Settings,
  Shield,
};

export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useUiStore();

  const visibleItems = SIDEBAR_ITEMS.filter(
    (item) => user && (item.roles as readonly string[]).includes(user.role)
  );

  const sidebarContent = (
    <div className="flex h-full flex-col bg-sidebar border-r border-sidebar-border">
      <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-semibold text-sidebar-foreground">
          <Bot className="h-6 w-6 text-sidebar-primary" />
          <span>MyAgent</span>
        </Link>
        <button
          onClick={() => setSidebarOpen(false)}
          className="rounded-md p-1 text-sidebar-foreground/50 hover:text-sidebar-foreground lg:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {visibleItems.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              }`}
            >
              {Icon && <Icon className="h-4 w-4 flex-shrink-0" />}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-sidebar-border p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-sidebar-foreground/60">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          <span className="truncate">{user?.username || "用户"}</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <aside className="hidden lg:flex lg:w-60 lg:flex-col">
        {sidebarContent}
      </aside>
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-60">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
