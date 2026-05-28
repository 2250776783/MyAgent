import { PageContainer } from "@/components/shared/page-container";
import { AgentForm } from "@/components/agents/agent-form";

export default function NewAgentPage() {
  return (
    <PageContainer className="max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">创建 Agent</h1>
        <p className="mt-1 text-sm text-muted-foreground">配置新的 AI Agent</p>
      </div>
      <AgentForm />
    </PageContainer>
  );
}
