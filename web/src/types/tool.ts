export interface Tool { id: string; name: string; description: string; icon: string; category: string; enabled: boolean; config: Record<string, unknown>; created_at: string; updated_at: string; }
export interface ToolConfig { id: string; tool_id: string; api_key?: string; base_url?: string; extra_params?: Record<string, unknown>; }
export interface ApiKeyInfo { id: string; name: string; key_preview: string; created_at: string; last_used?: string; }

