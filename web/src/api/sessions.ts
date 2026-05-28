import apiClient from "./client";
import type { SessionSummary, ChatMessage } from "@/types/chat";

export const sessionsApi = {
  list: () => apiClient.get<{ success: boolean; data: SessionSummary[] }>("/chat/sessions").then((r) => r.data),
  get: (id: string) => apiClient.get<{ success: boolean; data: { id: string; messages: ChatMessage[] } }>(`/chat/sessions/${id}`).then((r) => r.data),
  create: () => apiClient.post<{ success: boolean; data: SessionSummary }>("/chat/session").then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/chat/sessions/${id}`),
};

