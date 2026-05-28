"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import {
  ArrowLeft,
  Save,
  Play,
  Undo2,
  Redo2,
  Trash2,
  Workflow,
} from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { NodePalette } from "@/components/workflow/node-palette";
import { NodeConfigPanel } from "@/components/workflow/node-config-panel";
import { workflowApi } from "@/api/workflow";
import { useWorkflowStore } from "@/stores/workflow-store";
import type { Node, Edge } from "reactflow";

const WorkflowCanvas = dynamic(
  () => import("@/components/workflow/workflow-canvas").then((m) => ({ default: m.WorkflowCanvas })),
  { ssr: false }
);

export default function WorkflowEditorPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const isNew = id === "new";
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(!isNew);
  const initialized = useRef(false);

  const nodes = useWorkflowStore((s) => s.nodes);
  const edges = useWorkflowStore((s) => s.edges);
  const undo = useWorkflowStore((s) => s.undo);
  const redo = useWorkflowStore((s) => s.redo);
  const past = useWorkflowStore((s) => s.past);
  const future = useWorkflowStore((s) => s.future);
  const loadWorkflow = useWorkflowStore((s) => s.loadWorkflow);

  useEffect(() => {
    if (isNew) {
      setLoading(false);
      return;
    }
    if (initialized.current) return;
    initialized.current = true;

    workflowApi.get(id).then((res) => {
      const wf = res.data;
      setName(wf.name);
      setDescription(wf.description);
      loadWorkflow(
        (wf.nodes || []).map((n: Record<string, unknown>) => ({
          id: n.id as string,
          type: n.type as string,
          position: n.position as { x: number; y: number },
          data: n.data as Record<string, unknown>,
        })) as Node[],
        (wf.edges || []).map((e: Record<string, unknown>) => ({
          id: e.id as string,
          source: e.source as string,
          target: e.target as string,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
          animated: e.animated,
        })) as Edge[]
      );
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id, isNew, loadWorkflow]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const data = {
        name,
        description,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data,
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
          animated: e.animated,
        })),
      };
      if (isNew) {
        await workflowApi.create(data);
      } else {
        await workflowApi.update(id, data);
      }
      router.push("/workflow");
    } catch {} finally {
      setSaving(false);
    }
  }, [name, description, nodes, edges, id, isNew, router]);

  if (loading) {
    return (
      <PageContainer>
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-muted" />
          <div className="h-[600px] rounded-xl bg-muted" />
        </div>
      </PageContainer>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Top Bar */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/workflow")}
            className="rounded-md p-1 text-muted-foreground hover:bg-accent"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Workflow className="h-4 w-4 text-muted-foreground" />
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="工作流名称"
              className="text-sm font-medium bg-transparent outline-none border-none"
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={undo}
            disabled={past.length === 0}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-30"
          >
            <Undo2 className="h-4 w-4" />
          </button>
          <button
            onClick={redo}
            disabled={future.length === 0}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-30"
          >
            <Redo2 className="h-4 w-4" />
          </button>
          <div className="mx-1 h-5 w-px bg-border" />
          <button className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-emerald-600 hover:bg-emerald-500/10">
            <Play className="h-3.5 w-3.5" /> 运行
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5" /> {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex flex-1 min-h-0">
        {/* Left Sidebar - Node Palette */}
        <div className="w-44 shrink-0 border-r p-3 space-y-3 overflow-y-auto">
          <NodePalette />
          <NodeConfigPanel />
        </div>

        {/* Canvas */}
        <div className="flex-1">
          <WorkflowCanvas />
        </div>
      </div>
    </div>
  );
}
