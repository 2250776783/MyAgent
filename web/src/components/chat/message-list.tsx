"use client";

import { useEffect, useRef } from "react";
import { MessageBubble } from "./message-bubble";
import { WelcomeScreen } from "./welcome-screen";
import type { ChatMessage } from "@/types/chat";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (prompt: string) => void;
}

export function MessageList({ messages, isStreaming, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isStreaming || messages.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  if (messages.length === 0) {
    return <WelcomeScreen onSend={onSend} />;
  }

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-6 sm:px-6">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
