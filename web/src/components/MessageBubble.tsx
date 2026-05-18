import type { ChatMessage } from "../types/chat";
import { ToolCallCard } from "./ToolCallCard";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? "rounded-br-md bg-blue-500 text-white"
            : "rounded-bl-md bg-white text-gray-800 shadow-sm"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        ) : (
          <>
            {message.toolCalls && message.toolCalls.length > 0 && (
              <div className="mb-2 space-y-1">
                {message.toolCalls.map((tc, i) => (
                  <ToolCallCard key={`${tc.id || i}`} toolCall={tc} />
                ))}
              </div>
            )}
            <div className="whitespace-pre-wrap text-sm">
              {message.content || (message.isStreaming ? "" : "...")}
              {message.isStreaming && (
                <span className="ml-0.5 inline-block h-4 w-2 animate-pulse bg-gray-400" />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
