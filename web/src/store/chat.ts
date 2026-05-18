import { create } from "zustand";
import type { ChatMessage } from "../types/chat";
import { ChatWebSocket } from "../api/ws";
import {
  type SessionSummary,
  fetchSessions as apiFetchSessions,
  fetchSessionMessages,
  deleteSession as apiDeleteSession,
} from "../api/client";

const WS_URL = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/ws/chat`;

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  isStreaming: boolean;
  error: string | null;
  sessions: SessionSummary[];
  sendMessage: (content: string) => void;
  clearMessages: () => void;
  clearError: () => void;
  loadSessions: () => Promise<void>;
  switchSession: (id: string) => Promise<void>;
  newSession: () => void;
  removeSession: (id: string) => Promise<void>;
}

function createMessage(role: "user" | "assistant", content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    toolCalls: role === "assistant" ? [] : undefined,
    isStreaming: role === "assistant",
  };
}

export const useChatStore = create<ChatState>((set, get) => {
  let ws: ChatWebSocket | null = null;
  let currentAssistantMsgId: string | null = null;

  function cleanupWs() {
    ws?.disconnect();
    ws = null;
    currentAssistantMsgId = null;
  }

  function initWs() {
    if (ws) return;
    ws = new ChatWebSocket(WS_URL);
    // connect silently — errors are not shown for transient failures
    ws.connect({
      onToken: (text: string) => {
        set((state) => {
          const msgs = [...state.messages];
          const idx = msgs.findIndex((m) => m.id === currentAssistantMsgId);
          if (idx === -1) return state;
          msgs[idx] = { ...msgs[idx], content: msgs[idx].content + text };
          return { messages: msgs };
        });
      },
      onToolCall: (data: any) => {
        set((state) => {
          const msgs = [...state.messages];
          const idx = msgs.findIndex((m) => m.id === currentAssistantMsgId);
          if (idx === -1) return state;
          const msg = { ...msgs[idx] };
          msg.toolCalls = [
            ...(msg.toolCalls ?? []),
            { id: data.id ?? "", name: data.name ?? "", args: data.args ?? "" },
          ];
          msgs[idx] = msg;
          return { messages: msgs };
        });
      },
      onToolResult: (data: any) => {
        set((state) => {
          const msgs = [...state.messages];
          const idx = msgs.findIndex((m) => m.id === currentAssistantMsgId);
          if (idx === -1) return state;
          const msg = { ...msgs[idx] };
          const toolCalls = [...(msg.toolCalls ?? [])];
          const last = toolCalls.length - 1;
          if (last >= 0 && toolCalls[last].name === data.name) {
            toolCalls[last] = { ...toolCalls[last], output: data.output };
          }
          msg.toolCalls = toolCalls;
          msgs[idx] = msg;
          return { messages: msgs };
        });
      },
      onDone: (sessionId: string) => {
        set((state) => ({
          sessionId,
          isStreaming: false,
          messages: state.messages.map((m) =>
            m.id === currentAssistantMsgId ? { ...m, isStreaming: false } : m,
          ),
        }));
        currentAssistantMsgId = null;
        refreshSessions();
      },
      onError: (message: string) => {
        set((state) => ({
          error: message,
          isStreaming: false,
          messages: state.messages.map((m) =>
            m.id === currentAssistantMsgId ? { ...m, isStreaming: false } : m,
          ),
        }));
        currentAssistantMsgId = null;
      },
    });
  }

  function ensureConnected(): boolean {
    if (ws && ws.isConnected()) return true;
    // ws exists and will auto-reconnect — just queue the message
    return false;
  }

  async function refreshSessions() {
    try {
      const sessions = await apiFetchSessions();
      set({ sessions });
    } catch {
      // ignore
    }
  }

  // eager init
  initWs();

  return {
    messages: [],
    sessionId: null,
    isStreaming: false,
    error: null,
    sessions: [],

    sendMessage(content: string) {
      const { isStreaming } = get();
      if (isStreaming || !content.trim()) return;

      const userMsg = createMessage("user", content);
      const assistantMsg = createMessage("assistant", "");
      currentAssistantMsgId = assistantMsg.id;

      set((state) => ({
        messages: [...state.messages, userMsg, assistantMsg],
        isStreaming: true,
        error: null,
      }));

      ensureConnected();
      const sent = ws!.send(content, get().sessionId ?? undefined);
      if (!sent) {
        // message queued — will send when ws connects
        // if queue grows stale, surface an error
        setTimeout(() => {
          if (ws?.hasQueuedMessages()) {
            set((state) => ({
              error: "WebSocket 连接超时，请检查后端是否启动",
              isStreaming: false,
              messages: state.messages.map((m) =>
                m.id === currentAssistantMsgId ? { ...m, isStreaming: false } : m,
              ),
            }));
            currentAssistantMsgId = null;
            // reconnect attempt
            cleanupWs();
            initWs();
          }
        }, 8000);
      }
    },

    clearMessages() {
      set({ messages: [], sessionId: null, isStreaming: false, error: null });
    },

    clearError() {
      set({ error: null });
    },

    async loadSessions() {
      await refreshSessions();
    },

    async switchSession(id: string) {
      cleanupWs();
      set({ isStreaming: false, error: null });
      const msgs = await fetchSessionMessages(id);
      set({
        sessionId: id,
        messages: msgs.map((m) => createMessage(m.role, m.content)),
      });
      initWs();
    },

    newSession() {
      cleanupWs();
      set({ messages: [], sessionId: null, isStreaming: false, error: null });
      initWs();
    },

    async removeSession(id: string) {
      await apiDeleteSession(id);
      const { sessionId } = get();
      if (sessionId === id) {
        set({ sessionId: null, messages: [] });
      }
      refreshSessions();
    },
  };
});
