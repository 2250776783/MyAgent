import { useEffect } from "react";
import { useChatStore } from "../store/chat";

export function SessionSidebar() {
  const {
    sessions,
    sessionId: currentId,
    loadSessions,
    switchSession,
    newSession,
    removeSession,
    isStreaming,
  } = useChatStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  function formatTime(ts: number): string {
    const d = new Date(ts * 1000);
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  return (
    <aside className="flex w-60 flex-col border-r bg-white">
      <div className="border-b p-3">
        <button
          onClick={newSession}
          disabled={isStreaming}
          className="w-full rounded-lg border border-dashed border-gray-300 px-3 py-2 text-sm text-gray-500 transition-colors hover:border-blue-400 hover:text-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          + 新对话
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto">
        {sessions.length === 0 && (
          <p className="px-3 pt-4 text-center text-xs text-gray-400">
            暂无会话记录
          </p>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`group flex cursor-pointer items-center px-3 py-2.5 text-sm transition-colors hover:bg-gray-50 ${
              s.id === currentId ? "bg-blue-50 text-blue-700" : "text-gray-700"
            }`}
            onClick={() => switchSession(s.id)}
          >
            <span className="min-w-0 flex-1 truncate">
              {formatTime(s.created_at)}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeSession(s.id);
              }}
              className="ml-1 rounded p-0.5 text-gray-300 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
              title="删除会话"
            >
              x
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
