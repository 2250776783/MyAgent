import type { ToolCallInfo } from "../types/chat";

interface Props {
  toolCall: ToolCallInfo;
}

export function ToolCallCard({ toolCall }: Props) {
  let argsDisplay = toolCall.args;
  try {
    const parsed = JSON.parse(toolCall.args);
    argsDisplay = JSON.stringify(parsed, null, 2);
  } catch {
    // use raw string
  }

  return (
    <div className="my-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs">
      <div className="flex items-center gap-1 text-gray-600">
        <span className="font-medium text-blue-600">{toolCall.name}</span>
        {toolCall.output && <span className="text-green-500">已完成</span>}
        {!toolCall.output && <span className="text-yellow-500">执行中...</span>}
      </div>
      <div className="mt-1 text-gray-500">
        <span className="font-medium">参数:</span>{" "}
        <pre className="inline font-mono text-xs">{argsDisplay}</pre>
      </div>
      {toolCall.output && (
        <div className="mt-1 text-gray-500">
          <span className="font-medium">结果:</span> {toolCall.output.slice(0, 200)}
          {toolCall.output.length > 200 && "..."}
        </div>
      )}
    </div>
  );
}
