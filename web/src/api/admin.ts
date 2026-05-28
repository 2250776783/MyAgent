import apiClient from "./client";
import type { SystemMetrics } from "@/types/admin";

export const adminApi = {
  getUsers: () => apiClient.get("/admin/users").then((r) => r.data),
  updateUser: (id: string, data: Record<string, unknown>) => apiClient.put(`/admin/users/${id}`, data).then((r) => r.data),
  deleteUser: (id: string) => apiClient.delete(`/admin/users/${id}`),
  getSystemMetrics: () => apiClient.get<{ success: boolean; data: SystemMetrics }>("/admin/system").then((r) => r.data),
  updateConfig: (config: Record<string, unknown>) => apiClient.put("/admin/system", config).then((r) => r.data),
};

