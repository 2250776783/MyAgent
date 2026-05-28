import apiClient from "./client";
import type { Tool } from "@/types/tool";

export const toolsApi = {
  list: () => apiClient.get<{ success: boolean; data: Tool[] }>("/tools").then((r) => r.data),
  update: (id: string, data: Partial<Tool>) => apiClient.put(`/tools/${id}`, data).then((r) => r.data),
};

