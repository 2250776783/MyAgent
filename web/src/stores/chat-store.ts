import { create } from "zustand";
import type { ChatMessage, ToolCallInfo } from "@/types/chat";
import type { SessionSummary } from "@/types/chat";
import { ChatWebSocket } from "@/lib/ws";
import { sessionsApi } from "@/api/sessions";
import { generateId } from "@/lib/utils";

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  isStreaming: boolean;
  error: string | null;
  sessions: SessionSummary[];
  sessionsLoading: boolean;
  wsConnected: boolean;

  sendMessage: (content: string) => void;
  stopStreaming: () => void;
  clearMessages: () => void;
  clearError: () => void;
  loadSessions: () => Promise<void>;
  switchSession: (id: string) => Promise<void>;
  newSession: () => void;
  removeSession: (id: string) => Promise<void>;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ||
  `${typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:"}//${typeof window !== "undefined" ? window.location.host : "localhost:3000"}/api/ws/chat`;

function createMessage(
  role: "user" | "assistant",
  content: string,
  extras?: Partial<ChatMessage>
): ChatMessage {
  return {
    id: generateId(),
    role,
    content,
    created_at: new Date().toISOString(),
    ...extras,
  };
}

// ---- Mock streaming (used when no backend available) ----
const MOCK_RESPONSES = [
  "你好！我是 AI 助手，有什么可以帮助你的吗？\n\n你可以问我以下类型的问题：\n\n- **代码相关**：编写、调试、优化代码\n- **知识问答**：技术概念、最佳实践\n- **文本处理**：总结、翻译、改写\n- **数据分析**：解释数据、生成报告",
  "这是一个很好的问题！让我来详细分析一下。\n\n## 关键要点\n\n1. **第一点**：这是最重要的考虑因素\n2. **第二点**：不要忽视这个方面\n3. **第三点**：基于以上分析，建议这样做\n\n```python\ndef example():\n    print(\"Hello, World!\")\n    return True\n```\n\n> 提示：这是一个引用块\n\n希望这个解释对你有帮助！",
];

function getMockResponse(_input: string): string {
  return MOCK_RESPONSES[Math.floor(Math.random() * MOCK_RESPONSES.length)];
}

async function mockStreamResponse(
  onToken: (text: string) => void,
  onDone: () => void,
  onToolCall?: (tc: ToolCallInfo) => void
): Promise<void> {
  const text = getMockResponse("");
  // Simulate thinking delay
  await new Promise((r) => setTimeout(r, 600));
  // Optionally show a mock tool call
  if (onToolCall && Math.random() > 0.5) {
    onToolCall({
      id: generateId(),
      name: "web_search",
      args: JSON.stringify({ query: "相关信息" }),
      status: "running",
    });
    await new Promise((r) => setTimeout(r, 800));
  }
  // Stream tokens
  const words = text.split(/(?<=\s)/);
  for (const word of words) {
    onToken(word);
    await new Promise((r) => setTimeout(r, 20 + Math.random() * 30));
  }
  onDone();
}

export const useChatStore = create<ChatState>((set, get) => {
  let ws: ChatWebSocket | null = null;
  let currentAssistantId: string | null = null;
  let abortStreaming = false;
  let unsubWs: (() => void) | null = null;

  function initWs() {
    if (ws) return;
    ws = new ChatWebSocket(WS_URL);
    unsubWs = ws.on((event) => {
      const { type, data } = event;
      switch (type) {
        case "token":
          appendToAssistant(data.text ?? "");
          break;
        case "tool_call":
          appendToolCall({
            id: data.id ?? "",
            name: data.name ?? "",
            args: data.args ?? "",
            status: "running",
          });
          break;
        case "tool_result":
          updateToolCallOutput(data.id ?? "", data.output ?? "");
          break;
        case "done":
          finalizeAssistant(data.session_id);
          break;
        case "error":
          set({ error: data.message ?? "连接错误", isStreaming: false });
          break;
      }
    });
    ws.connect();
    // Periodically check connection state (no direct callback for this)
    const checkInterval = setInterval(() => {
      if (!ws) { clearInterval(checkInterval); return; }
      set({ wsConnected: ws.isConnected });
    }, 5000);
  }

  function appendToAssistant(text: string) {
    set((state) => {
      const msgs = [...state.messages];
      const idx = msgs.findIndex((m) => m.id === currentAssistantId);
      if (idx === -1) return state;
      msgs[idx] = { ...msgs[idx], content: msgs[idx].content + text };
      return { messages: msgs };
    });
  }

  function appendToolCall(tc: ToolCallInfo) {
    set((state) => {
      const msgs = [...state.messages];
      const idx = msgs.findIndex((m) => m.id === currentAssistantId);
      if (idx === -1) return state;
      const msg = { ...msgs[idx] };
      const toolCalls = [...(msg.tool_calls ?? []), tc];
      msgs[idx] = { ...msg, tool_calls: toolCalls };
      return { messages: msgs };
    });
  }

  function updateToolCallOutput(toolCallId: string, output: string) {
    set((state) => {
      const msgs = [...state.messages];
      const msg = { ...msgs[msgs.length - 1] };
      const toolCalls = (msg.tool_calls ?? []).map((tc) =>
        tc.id === toolCallId ? { ...tc, output, status: "completed" as const } : tc
      );
      msgs[msgs.length - 1] = { ...msg, tool_calls: toolCalls };
      return { messages: msgs };
    });
  }

  function finalizeAssistant(sessionId?: string) {
    set((state) => {
      const msgs = [...state.messages];
      const idx = msgs.findIndex((m) => m.id === currentAssistantId);
      if (idx !== -1) {
        msgs[idx] = { ...msgs[idx], is_streaming: false };
      }
      return {
        messages: msgs,
        isStreaming: false,
        sessionId: sessionId || state.sessionId,
      };
    });
    currentAssistantId = null;
  }

  return {
    messages: [],
    sessionId: null,
    isStreaming: false,
    error: null,
    sessions: [],
    sessionsLoading: false,
    wsConnected: false,

    sendMessage: (content: string) => {
      if (!content.trim() || get().isStreaming) return;

      const userMsg = createMessage("user", content);
      const assistantMsg = createMessage("assistant", "", {
        is_streaming: true,
        tool_calls: [],
      });

      currentAssistantId = assistantMsg.id;
      abortStreaming = false;

      set((state) => ({
        messages: [...state.messages, userMsg, assistantMsg],
        isStreaming: true,
        error: null,
      }));

      // Try WebSocket first, fall back to mock streaming
      if (ws?.isConnected) {
        ws.send(content, get().sessionId ?? undefined);
      } else {
        // Mock streaming for development
        mockStreamResponse(
          (text) => {
            if (abortStreaming) return;
            appendToAssistant(text);
          },
          () => {
            if (abortStreaming) return;
            finalizeAssistant();
            get().loadSessions();
          },
          (tc) => {
            if (abortStreaming) return;
            appendToolCall(tc);
          }
        );
      }
    },

    stopStreaming: () => {
      abortStreaming = true;
      finalizeAssistant();
    },

    clearMessages: () => {
      set({ messages: [], error: null });
    },

    clearError: () => set({ error: null }),

    loadSessions: async () => {
      set({ sessionsLoading: true });
      try {
        const res = await sessionsApi.list();
        set({ sessions: res.data, sessionsLoading: false });
      } catch {
        set({ sessionsLoading: false });
      }
    },

    switchSession: async (id: string) => {
      set({ sessionId: id, messages: [], isStreaming: false });
      try {
        const res = await sessionsApi.get(id);
        set({
          messages: res.data.messages,
          sessionId: res.data.id,
        });
      } catch {
        set({ error: "加载会话失败" });
      }
    },

    newSession: () => {
      set({
        sessionId: null,
        messages: [],
        error: null,
        isStreaming: false,
      });
    },

    removeSession: async (id: string) => {
      try {
        await sessionsApi.delete(id);
        const { sessions, sessionId } = get();
        set({
          sessions: sessions.filter((s) => s.id !== id),
        });
        if (sessionId === id) {
          get().newSession();
        }
      } catch {
        set({ error: "删除会话失败" });
      }
    },
  };
});
