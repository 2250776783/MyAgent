/**
 * 批量生成前端源文件脚本
 * 运行: node scripts/generate-files.js
 */
const fs = require("fs");
const path = require("path");

const BASE = path.resolve(__dirname, "..");
const SRC = path.join(BASE, "src");

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function write(filePath, content) {
  const full = path.join(SRC, filePath);
  ensureDir(path.dirname(full));
  fs.writeFileSync(full, content.trimStart() + "\n");
  console.log(`  ✓ ${filePath}`);
}

// ============================================================
// 1. PROVIDERS
// ============================================================
write("providers/theme-provider.tsx", `
"use client";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { type ThemeProviderProps } from "next-themes";

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
`);

write("providers/query-provider.tsx", `
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
`);

// ============================================================
// 2. STORES
// ============================================================
write("stores/auth-store.ts", `
import { create } from "zustand";
import type { User, AuthResponse } from "@/types/auth";
import { setTokens, clearTokens, getToken, decodeToken } from "@/lib/auth-utils";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  loadFromStorage: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await new Promise((r) => setTimeout(r, 500));
      const mockResponse: AuthResponse = {
        access_token: "mock_access_" + Date.now(),
        refresh_token: "mock_refresh_" + Date.now(),
        user: {
          id: "user_1",
          username: email.split("@")[0],
          email,
          avatar: "",
          role: email.includes("admin") ? "ADMIN" : "USER",
          created_at: new Date().toISOString(),
        },
      };
      setTokens(mockResponse.access_token, mockResponse.refresh_token);
      set({ user: mockResponse.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      set({ isLoading: false, error: err instanceof Error ? err.message : "登录失败" });
      throw err;
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true, error: null });
    try {
      await new Promise((r) => setTimeout(r, 500));
      const mockResponse: AuthResponse = {
        access_token: "mock_access_" + Date.now(),
        refresh_token: "mock_refresh_" + Date.now(),
        user: { id: "user_" + Date.now(), username, email, avatar: "", role: "USER", created_at: new Date().toISOString() },
      };
      setTokens(mockResponse.access_token, mockResponse.refresh_token);
      set({ user: mockResponse.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      set({ isLoading: false, error: err instanceof Error ? err.message : "注册失败" });
      throw err;
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false, error: null });
  },

  setUser: (user) => set({ user, isAuthenticated: true }),

  loadFromStorage: () => {
    const token = getToken();
    if (token) {
      const payload = decodeToken(token);
      if (payload) {
        set({
          user: { id: payload.sub, username: "用户", email: "", role: payload.role as "USER" | "ADMIN", created_at: "" },
          isAuthenticated: true,
        });
      }
    }
  },

  clearError: () => set({ error: null }),
}));
`);

write("stores/ui-store.ts", `
import { create } from "zustand";

interface UiState {
  sidebarCollapsed: boolean;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
}));
`);

// ============================================================
// 3. API LAYER
// ============================================================
write("api/client.ts", `
import axios from "axios";
import { getToken, getRefreshToken, setTokens, clearTokens } from "@/lib/auth-utils";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = \`Bearer \${token}\`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = \`Bearer \${token}\`;
          return apiClient(originalRequest);
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error("No refresh token");
        const res = await axios.post("/api/auth/refresh", { refresh_token: refreshToken });
        const { access_token, refresh_token } = res.data;
        setTokens(access_token, refresh_token);
        processQueue(null, access_token);
        originalRequest.headers.Authorization = \`Bearer \${access_token}\`;
        return apiClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
`);

// API modules
write("api/auth.ts", `
import apiClient from "./client";
import type { AuthResponse, User } from "@/types/auth";

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<AuthResponse>("/auth/login", { email, password }).then((r) => r.data),
  register: (username: string, email: string, password: string) =>
    apiClient.post<AuthResponse>("/auth/register", { username, email, password }).then((r) => r.data),
  logout: () => apiClient.post("/auth/logout"),
  refresh: (refreshToken: string) =>
    apiClient.post<{ access_token: string; refresh_token: string }>("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data),
  getProfile: () => apiClient.get<User>("/auth/profile").then((r) => r.data),
  updatePassword: (oldPassword: string, newPassword: string) =>
    apiClient.put("/auth/password", { old_password: oldPassword, new_password: newPassword }),
};
`);

write("api/agents.ts", `
import apiClient from "./client";
import type { Agent } from "@/types/agent";

export const agentsApi = {
  list: (params?: { page?: number; search?: string }) =>
    apiClient.get<{ success: boolean; data: Agent[]; total: number }>("/agents", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get<{ success: boolean; data: Agent }>(\`/agents/\${id}\`).then((r) => r.data),
  create: (data: Partial<Agent>) => apiClient.post<{ success: boolean; data: Agent }>("/agents", data).then((r) => r.data),
  update: (id: string, data: Partial<Agent>) => apiClient.put<{ success: boolean; data: Agent }>(\`/agents/\${id}\`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(\`/agents/\${id}\`),
};
`);

write("api/sessions.ts", `
import apiClient from "./client";
import type { SessionSummary, ChatMessage } from "@/types/chat";

export const sessionsApi = {
  list: () => apiClient.get<{ success: boolean; data: SessionSummary[] }>("/chat/sessions").then((r) => r.data),
  get: (id: string) => apiClient.get<{ success: boolean; data: { id: string; messages: ChatMessage[] } }>(\`/chat/sessions/\${id}\`).then((r) => r.data),
  create: () => apiClient.post<{ success: boolean; data: SessionSummary }>("/chat/session").then((r) => r.data),
  delete: (id: string) => apiClient.delete(\`/chat/sessions/\${id}\`),
};
`);

write("api/dashboard.ts", `
import apiClient from "./client";

export const dashboardApi = {
  getOverview: () => apiClient.get("/dashboard/overview").then((r) => r.data),
  getRecentChats: () => apiClient.get("/dashboard/recent-chats").then((r) => r.data),
  getRecentAgents: () => apiClient.get("/dashboard/recent-agents").then((r) => r.data),
};
`);

write("api/knowledge.ts", `
import apiClient from "./client";
import type { KnowledgeDocument, SearchResult } from "@/types/knowledge";

export const knowledgeApi = {
  list: () => apiClient.get<{ success: boolean; data: KnowledgeDocument[] }>("/knowledge/files").then((r) => r.data),
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post("/knowledge/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => { if (e.total && onProgress) onProgress(Math.round((e.loaded * 100) / e.total)); },
    }).then((r) => r.data);
  },
  delete: (id: string) => apiClient.delete(\`/knowledge/files/\${id}\`),
  search: (query: string, limit?: number) =>
    apiClient.post<{ success: boolean; data: SearchResult[] }>("/knowledge/search", { query, limit }).then((r) => r.data),
};
`);

write("api/memory.ts", `
import apiClient from "./client";
import type { Memory, MemorySearchParams } from "@/types/memory";

export const memoryApi = {
  list: (params?: { page?: number }) =>
    apiClient.get<{ success: boolean; data: Memory[] }>("/memory", { params }).then((r) => r.data),
  delete: (id: string) => apiClient.delete(\`/memory/\${id}\`),
  search: (params: MemorySearchParams) =>
    apiClient.post<{ success: boolean; data: Memory[] }>("/memory/search", params).then((r) => r.data),
};
`);

write("api/tools.ts", `
import apiClient from "./client";
import type { Tool } from "@/types/tool";

export const toolsApi = {
  list: () => apiClient.get<{ success: boolean; data: Tool[] }>("/tools").then((r) => r.data),
  update: (id: string, data: Partial<Tool>) => apiClient.put(\`/tools/\${id}\`, data).then((r) => r.data),
};
`);

write("api/logs.ts", `
import apiClient from "./client";
import type { LogEntry, LogFilter } from "@/types/log";

export const logsApi = {
  list: (filter?: LogFilter) =>
    apiClient.get<{ success: boolean; data: LogEntry[] }>("/logs", { params: filter }).then((r) => r.data),
};
`);

write("api/admin.ts", `
import apiClient from "./client";
import type { SystemMetrics } from "@/types/admin";

export const adminApi = {
  getUsers: () => apiClient.get("/admin/users").then((r) => r.data),
  updateUser: (id: string, data: Record<string, unknown>) => apiClient.put(\`/admin/users/\${id}\`, data).then((r) => r.data),
  deleteUser: (id: string) => apiClient.delete(\`/admin/users/\${id}\`),
  getSystemMetrics: () => apiClient.get<{ success: boolean; data: SystemMetrics }>("/admin/system").then((r) => r.data),
  updateConfig: (config: Record<string, unknown>) => apiClient.put("/admin/system", config).then((r) => r.data),
};
`);

write("api/settings.ts", `
import apiClient from "./client";

export const settingsApi = {
  get: () => apiClient.get("/settings").then((r) => r.data),
  update: (data: Record<string, unknown>) => apiClient.put("/settings", data).then((r) => r.data),
};
`);

console.log("\\n✓ API 层 + Stores + Providers 创建完成");
