import apiClient from "./client";
import type { LogEntry, LogFilter } from "@/types/log";

export const logsApi = {
  list: (filter?: LogFilter) =>
    apiClient.get<{ success: boolean; data: LogEntry[] }>("/logs", { params: filter }).then((r) => r.data),
};

