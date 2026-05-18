export interface StreamEventData {
  text?: string;
  id?: string;
  name?: string;
  args?: string;
  output?: string;
  message?: string;
  session_id?: string;
}

export interface ToolCallInfo {
  id: string;
  name: string;
  args: string;
  output?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCallInfo[];
  isStreaming?: boolean;
}
