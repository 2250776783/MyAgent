import apiClient from "./client";

export const dashboardApi = {
  getOverview: () => apiClient.get("/dashboard/overview").then((r) => r.data),
  getRecentChats: () => apiClient.get("/dashboard/recent-chats").then((r) => r.data),
  getRecentAgents: () => apiClient.get("/dashboard/recent-agents").then((r) => r.data),
};

