import apiClient from "./client";
import type { Memory, MemorySearchParams } from "@/types/memory";

export const memoryApi = {
  list: (params?: { page?: number }) =>
    apiClient.get<{ success: boolean; data: Memory[] }>("/memory", { params }).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/memory/${id}`),
  search: (params: MemorySearchParams) =>
    apiClient.post<{ success: boolean; data: Memory[] }>("/memory/search", params).then((r) => r.data),
};

