export interface StreamEventData { text?: string; id?: string; name?: string; args?: string; output?: string; message?: string; session_id?: string; thinking?: string; }
export interface ToolCallInfo { id: string; name: string; args: string; output?: string; status?: "pending" | "running" | "completed" | "error"; }
export interface ChatMessage { id: string; role: "user" | "assistant" | "system"; content: string; tool_calls?: ToolCallInfo[]; token_usage?: { prompt: number; completion: number; total: number; }; is_streaming?: boolean; thinking?: string; created_at: string; }
export interface SessionSummary { id: string; title: string; message_count: number; created_at: string; updated_at: string; }
export interface SessionDetail { id: string; title: string; messages: ChatMessage[]; created_at: string; updated_at: string; agent_id?: string; }

