import apiClient from "./client";
import type { Workflow } from "@/types/workflow";

export const workflowApi = {
  list: () => apiClient.get<{ success: boolean; data: Workflow[] }>("/workflows").then((r) => r.data),
  get: (id: string) => apiClient.get<{ success: boolean; data: Workflow }>(`/workflows/${id}`).then((r) => r.data),
  create: (data: Record<string, unknown>) => apiClient.post<{ success: boolean; data: Workflow }>("/workflows", data).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) => apiClient.put(`/workflows/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/workflows/${id}`).then((r) => r.data),
};
