"use client";

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { useState } from "react";
import { Copy, Check, Bot, User, Brain } from "lucide-react";
import type { ChatMessage, ToolCallInfo } from "@/types/chat";
import { ToolCallCard } from "./tool-call-card";

interface Props {
  message: ChatMessage;
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="group relative my-2 overflow-hidden rounded-lg border">
      <div className="flex items-center justify-between bg-muted px-4 py-1.5 text-xs text-muted-foreground">
        <span>{language || "text"}</span>
        <button onClick={handleCopy} className="flex items-center gap-1 hover:text-foreground">
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "已复制" : "复制"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function InlineCode({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded-md bg-muted px-1.5 py-0.5 text-sm font-mono text-foreground">
      {children}
    </code>
  );
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
        isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
      }`}>
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={`max-w-[80%] space-y-2 ${isUser ? "items-end" : "items-start"}`}>
        {isUser ? (
          <div className="rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground">
            {message.content}
          </div>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none break-words">
            {message.thinking && (
              <details className="mb-2 rounded-lg border border-muted">
                <summary className="flex cursor-pointer items-center gap-2 p-2 text-xs text-muted-foreground hover:text-foreground">
                  <Brain className="h-3.5 w-3.5" />
                  推理过程
                </summary>
                <div className="border-t bg-muted/30 p-3 text-xs text-muted-foreground">
                  {message.thinking}
                </div>
              </details>
            )}
            <Markdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  const codeStr = String(children).replace(/\n$/, "");
                  if (match) {
                    return <CodeBlock language={match[1]} code={codeStr} />;
                  }
                  return <InlineCode>{children}</InlineCode>;
                },
                pre({ children }) {
                  return <>{children}</>;
                },
              }}
            >
              {message.content}
            </Markdown>
            {message.tool_calls && message.tool_calls.length > 0 && (
              <div className="mt-3 space-y-2">
                {message.tool_calls.map((tc) => (
                  <ToolCallCard key={tc.id} toolCall={tc} />
                ))}
              </div>
            )}
          </div>
        )}
        <div className={`flex gap-2 px-1 ${isUser ? "justify-end" : "justify-start"}`}>
          {message.is_streaming && (
            <span className="inline-flex gap-0.5">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-foreground/40" style={{ animationDelay: "0ms" }} />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-foreground/40" style={{ animationDelay: "150ms" }} />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-foreground/40" style={{ animationDelay: "300ms" }} />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
