import apiClient from "./client";

export const settingsApi = {
  get: () => apiClient.get("/settings").then((r) => r.data),
  update: (data: Record<string, unknown>) => apiClient.put("/settings", data).then((r) => r.data),
};

