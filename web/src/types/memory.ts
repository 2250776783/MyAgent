export type MemoryType = "episodic" | "semantic" | "procedural";
export interface Memory { id: string; type: MemoryType; content: string; importance_score: number; confidence_score: number; tags: string[]; source: string; created_at: string; accessed_at: string; }
export interface MemorySearchParams { query: string; type?: MemoryType; limit?: number; min_importance?: number; }

