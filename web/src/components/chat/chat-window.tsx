"use client";

import { useState } from "react";
import { useChatStore } from "@/stores/chat-store";
import { MessageList } from "./message-list";
import { InputBar } from "./input-bar";
import { SessionSidebar } from "./session-sidebar";
import { Menu } from "lucide-react";

export function ChatWindow() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { messages, isStreaming, sendMessage } = useChatStore();

  return (
    <div className="flex h-full">
      <SessionSidebar
        mobileOpen={sidebarOpen}
        onCloseMobile={() => setSidebarOpen(false)}
      />
      <div className="flex flex-1 flex-col">
        <div className="flex items-center gap-2 border-b px-4 py-2 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-1 text-muted-foreground hover:bg-accent"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="text-sm font-medium">聊天</span>
        </div>
        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          onSend={sendMessage}
        />
        <InputBar />
      </div>
    </div>
  );
}
