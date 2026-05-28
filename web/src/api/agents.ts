import apiClient from "./client";
import type { Agent } from "@/types/agent";

export const agentsApi = {
  list: (params?: { page?: number; search?: string }) =>
    apiClient.get<{ success: boolean; data: Agent[]; total: number }>("/agents", { params }).then((r) => r.data),
  get: (id: string) => apiClient.get<{ success: boolean; data: Agent }>(`/agents/${id}`).then((r) => r.data),
  create: (data: Partial<Agent>) => apiClient.post<{ success: boolean; data: Agent }>("/agents", data).then((r) => r.data),
  update: (id: string, data: Partial<Agent>) => apiClient.put<{ success: boolean; data: Agent }>(`/agents/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/agents/${id}`),
};

