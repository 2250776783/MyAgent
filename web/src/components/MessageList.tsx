import { useEffect, useRef } from "react";
import { useChatStore } from "../store/chat";
import { MessageBubble } from "./MessageBubble";

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-4xl">?</p>
          <p className="mt-2 text-sm">开始对话吧</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-1 overflow-y-auto px-4 py-4 scrollbar-thin">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
