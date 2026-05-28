export type NodeType = "llm" | "tool" | "knowledge" | "code" | "input" | "output" | "condition";

export interface WorkflowNodeData {
  label: string;
  type: NodeType;
  config: Record<string, unknown>;
  [key: string]: unknown;
}

export interface WorkflowEdgeData {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  animated?: boolean;
  [key: string]: unknown;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNodeData[];
  edges: WorkflowEdgeData[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

