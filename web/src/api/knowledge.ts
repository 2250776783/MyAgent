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
  delete: (id: string) => apiClient.delete(`/knowledge/files/${id}`),
  search: (query: string, limit?: number) =>
    apiClient.post<{ success: boolean; data: SearchResult[] }>("/knowledge/search", { query, limit }).then((r) => r.data),
};

