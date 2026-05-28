export type AgentStatus = "active" | "inactive" | "error" | "deploying";
export type ModelProvider = "openai" | "deepseek" | "claude" | "custom";
export interface Agent { id: string; name: string; description: string; avatar?: string; model: string; provider: ModelProvider; temperature: number; max_tokens: number; top_p: number; system_prompt: string; tools: string[]; memory_enabled: boolean; knowledge_base_ids: string[]; status: AgentStatus; created_at: string; updated_at: string; user_id: string; }
export interface AgentFormValues { name: string; description: string; model: string; provider: ModelProvider; temperature: number; max_tokens: number; top_p: number; system_prompt: string; tools: string[]; memory_enabled: boolean; knowledge_base_ids: string[]; }

