import { create } from "zustand";
import type { Node, Edge, OnNodesChange, OnEdgesChange, OnConnect } from "reactflow";
import {
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  NodePositionChange,
} from "reactflow";

interface HistoryEntry {
  nodes: Node[];
  edges: Edge[];
}

interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  past: HistoryEntry[];
  future: HistoryEntry[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setSelectedNode: (node: Node | null) => void;
  updateNodeConfig: (nodeId: string, config: Record<string, unknown>) => void;
  updateNodeLabel: (nodeId: string, label: string) => void;
  addNode: (type: string, position: { x: number; y: number }) => void;
  deleteSelected: () => void;
  undo: () => void;
  redo: () => void;
  loadWorkflow: (nodes: Node[], edges: Edge[]) => void;
  reset: () => void;
}

function pushHistory(
  past: HistoryEntry[],
  nodes: Node[],
  edges: Edge[]
): HistoryEntry[] {
  const entry = { nodes: structuredClone(nodes), edges: structuredClone(edges) };
  return [...past.slice(-49), entry];
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  past: [],
  future: [],

  onNodesChange: (changes) => {
    set((state) => {
      const newNodes = applyNodeChanges(changes, state.nodes);

      const hasPositionChange = changes.some(
        (c): c is NodePositionChange => c.type === "position" && c.dragging === false
      );
      if (hasPositionChange) {
        return {
          nodes: newNodes,
          past: pushHistory(state.past, state.nodes, state.edges),
          future: [],
        };
      }
      return { nodes: newNodes };
    });
  },

  onEdgesChange: (changes) => {
    set((state) => ({
      edges: applyEdgeChanges(changes, state.edges),
    }));
  },

  onConnect: (connection) => {
    set((state) => ({
      edges: addEdge({ ...connection, animated: true }, state.edges),
      past: pushHistory(state.past, state.nodes, state.edges),
      future: [],
    }));
  },

  setSelectedNode: (node) => set({ selectedNode: node }),

  updateNodeConfig: (nodeId, config) => {
    set((state) => {
      const newNodes = state.nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, config: { ...(n.data.config as Record<string, unknown>), ...config } } }
          : n
      );
      return {
        nodes: newNodes,
        past: pushHistory(state.past, state.nodes, state.edges),
        future: [],
        selectedNode: state.selectedNode?.id === nodeId
          ? { ...state.selectedNode, data: newNodes.find((n) => n.id === nodeId)!.data }
          : state.selectedNode,
      };
    });
  },

  updateNodeLabel: (nodeId, label) => {
    set((state) => {
      const newNodes = state.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, label } } : n
      );
      return {
        nodes: newNodes,
        past: pushHistory(state.past, state.nodes, state.edges),
        future: [],
        selectedNode: state.selectedNode?.id === nodeId
          ? { ...state.selectedNode, data: newNodes.find((n) => n.id === nodeId)!.data }
          : state.selectedNode,
      };
    });
  },

  addNode: (type, position) => {
    const { nodes, edges, past } = get();
    const id = `node_${Date.now()}`;
    const nodeTypes: Record<string, { label: string; color: string }> = {
      llm: { label: "LLM", color: "blue" },
      tool: { label: "工具", color: "orange" },
      knowledge: { label: "知识库", color: "green" },
      code: { label: "代码", color: "purple" },
      input: { label: "输入", color: "emerald" },
      output: { label: "输出", color: "cyan" },
      condition: { label: "条件", color: "yellow" },
    };
    const info = nodeTypes[type] || { label: type, color: "gray" };
    const newNode: Node = {
      id,
      type,
      position,
      data: { label: info.label, type, config: {} },
    };
    set({
      nodes: [...nodes, newNode],
      past: pushHistory(past, nodes, edges),
      future: [],
    });
  },

  deleteSelected: () => {
    const { nodes, edges, selectedNode, past } = get();
    if (!selectedNode) return;
    set({
      nodes: nodes.filter((n) => n.id !== selectedNode.id),
      edges: edges.filter(
        (e) => e.source !== selectedNode.id && e.target !== selectedNode.id
      ),
      selectedNode: null,
      past: pushHistory(past, nodes, edges),
      future: [],
    });
  },

  undo: () => {
    const { past, nodes, edges } = get();
    if (past.length === 0) return;
    const prev = past[past.length - 1];
    set({
      nodes: prev.nodes,
      edges: prev.edges,
      past: past.slice(0, -1),
      future: [{ nodes: structuredClone(nodes), edges: structuredClone(edges) }, ...get().future],
      selectedNode: null,
    });
  },

  redo: () => {
    const { future, nodes, edges } = get();
    if (future.length === 0) return;
    const next = future[0];
    set({
      nodes: next.nodes,
      edges: next.edges,
      future: future.slice(1),
      past: [...get().past, { nodes: structuredClone(nodes), edges: structuredClone(edges) }],
      selectedNode: null,
    });
  },

  loadWorkflow: (nodes, edges) => {
    set({
      nodes,
      edges,
      selectedNode: null,
      past: [],
      future: [],
    });
  },

  reset: () => {
    set({ nodes: [], edges: [], selectedNode: null, past: [], future: [] });
  },
}));
