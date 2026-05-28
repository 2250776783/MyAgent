"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  MessageSquare,
  Trash2,
  Search,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { formatRelativeTime } from "@/lib/utils";

interface Props {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function SessionSidebar({ mobileOpen, onCloseMobile }: Props) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const {
    sessions,
    sessionId,
    sessionsLoading,
    loadSessions,
    newSession,
    switchSession,
    removeSession,
  } = useChatStore();

  useEffect(() => {
    loadSessions();
  }, []);

  const filteredSessions = sessions.filter(
    (s) => !search || s.title.toLowerCase().includes(search.toLowerCase())
  );

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b p-3">
        <h2 className="text-sm font-semibold">会话历史</h2>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground hidden lg:block"
        >
          {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      <div className="p-2">
        <button
          onClick={() => { newSession(); onCloseMobile?.(); }}
          className="flex w-full items-center gap-2 rounded-lg border border-dashed p-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          <Plus className="h-4 w-4" />
          新建会话
        </button>
      </div>

      <div className="px-2 pb-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索会话..."
            className="w-full rounded-md border bg-background py-1.5 pl-8 pr-3 text-xs outline-none focus:border-primary/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {sessionsLoading ? (
          <div className="space-y-2 p-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        ) : filteredSessions.length === 0 ? (
          <p className="p-4 text-center text-xs text-muted-foreground">
            {search ? "未找到匹配的会话" : "暂无会话记录"}
          </p>
        ) : (
          <div className="space-y-1">
            {filteredSessions.map((s) => (
              <div
                key={s.id}
                className={`group flex cursor-pointer items-center gap-2 rounded-lg p-2 text-sm hover:bg-accent ${
                  s.id === sessionId ? "bg-accent font-medium" : ""
                }`}
                onClick={() => { switchSession(s.id); onCloseMobile?.(); }}
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs">{s.title || "新会话"}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {formatRelativeTime(s.updated_at || s.created_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); removeSession(s.id); }}
                  className="shrink-0 rounded p-1 text-muted-foreground opacity-0 hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  if (mobileOpen) {
    return (
      <>
        <div className="fixed inset-0 z-40 bg-black/50" onClick={onCloseMobile} />
        <div className="fixed inset-y-0 left-0 z-50 w-72 border-r bg-background">
          {sidebarContent}
        </div>
      </>
    );
  }

  if (collapsed) return null;

  return (
    <div className="hidden w-72 border-r bg-muted/10 lg:block">
      {sidebarContent}
    </div>
  );
}
