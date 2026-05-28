export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";
export interface LogEntry { id: string; timestamp: string; level: LogLevel; message: string; source: string; trace_id?: string; details?: Record<string, unknown>; }
export interface LogFilter { level?: LogLevel[]; search?: string; source?: string; start_time?: string; end_time?: string; page?: number; limit?: number; }

