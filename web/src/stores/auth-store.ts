import { create } from "zustand";
import type { User, AuthResponse } from "@/types/auth";
import { setTokens, clearTokens, getToken, decodeToken } from "@/lib/auth-utils";
import { authApi } from "@/api/auth";
import axios from "axios";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  loadFromStorage: () => Promise<void>;
  clearError: () => void;
}

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("；");
    }
    return err.response?.data?.message || `请求失败 (${err.response?.status || "未知错误"})`;
  }
  if (err instanceof Error) return err.message;
  return "操作失败，请稍后重试";
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login(email, password);
      setTokens(res.access_token, res.refresh_token);
      set({ user: res.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const msg = getErrorMessage(err);
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.register(username, email, password);
      setTokens(res.access_token, res.refresh_token);
      set({ user: res.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const msg = getErrorMessage(err);
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false, error: null });
  },

  setUser: (user) => set({ user, isAuthenticated: true }),

  loadFromStorage: async () => {
    const token = getToken();
    if (!token) return;

    // 先用 token 解码填充基本信息
    const payload = decodeToken(token);
    if (!payload) {
      clearTokens();
      return;
    }
    set({
      user: {
        id: payload.sub,
        username: "用户",
        email: "",
        role: payload.role as "USER" | "ADMIN",
        created_at: "",
      },
      isAuthenticated: true,
    });

    // 异步拉取完整用户信息
    try {
      const profile = await authApi.getProfile();
      set({ user: profile });
    } catch {
      // Token 可能已过期，但不阻断使用
    }
  },

  clearError: () => set({ error: null }),
}));
