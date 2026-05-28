export type DocumentStatus = "pending" | "indexing" | "indexed" | "failed";
export interface KnowledgeDocument { id: string; filename: string; file_type: string; file_size: number; chunk_count: number; status: DocumentStatus; created_at: string; updated_at: string; }
export interface SearchResult { id: string; content: string; score: number; document_id: string; document_name: string; }

