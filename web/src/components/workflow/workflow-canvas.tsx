"use client";

import { useCallback, useRef } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type Node,
  type Edge,
  SelectionMode,
  type NodeTypes,
} from "reactflow";
import "reactflow/dist/style.css";
import { useWorkflowStore } from "@/stores/workflow-store";
import {
  LLMNode,
  ToolNode,
  KnowledgeNode,
  CodeNode,
  InputNode,
  OutputNode,
  ConditionNode,
} from "./custom-nodes";

const nodeTypes: NodeTypes = {
  llm: LLMNode,
  tool: ToolNode,
  knowledge: KnowledgeNode,
  code: CodeNode,
  input: InputNode,
  output: OutputNode,
  condition: ConditionNode,
};

interface Props {
  onNodeClick?: (node: Node) => void;
  onPaneClick?: () => void;
}

export function WorkflowCanvas({ onNodeClick, onPaneClick }: Props) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const nodes = useWorkflowStore((s) => s.nodes);
  const edges = useWorkflowStore((s) => s.edges);
  const onNodesChange = useWorkflowStore((s) => s.onNodesChange);
  const onEdgesChange = useWorkflowStore((s) => s.onEdgesChange);
  const onConnect = useWorkflowStore((s) => s.onConnect);
  const setSelectedNode = useWorkflowStore((s) => s.setSelectedNode);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
      onNodeClick?.(node);
    },
    [setSelectedNode, onNodeClick]
  );

  const handlePaneClick = useCallback(() => {
    setSelectedNode(null);
    onPaneClick?.();
  }, [setSelectedNode, onPaneClick]);

  return (
    <div ref={reactFlowWrapper} className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        selectionMode={SelectionMode.Partial}
        fitView
        deleteKeyCode="Delete"
        multiSelectionKeyCode="Shift"
        className="rounded-xl"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(var(--border))" />
        <Controls showInteractive={false} className="rounded-lg border shadow-sm" />
        <MiniMap
          nodeStrokeColor="hsl(var(--primary))"
          nodeColor="hsl(var(--muted))"
          maskColor="hsl(var(--background) / 0.8)"
          className="rounded-lg border shadow-sm"
        />
      </ReactFlow>
    </div>
  );
}
