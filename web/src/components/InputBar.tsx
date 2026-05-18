import { type FormEvent, useRef } from "react";
import { useChatStore } from "../store/chat";

export function InputBar() {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isStreaming, clearMessages } = useChatStore();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const value = inputRef.current?.value.trim();
    if (!value) return;
    sendMessage(value);
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t bg-white p-4">
      <textarea
        ref={inputRef}
        onKeyDown={handleKeyDown}
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        rows={1}
        className="max-h-32 min-h-[40px] flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
        disabled={isStreaming}
      />
      <button
        type="submit"
        disabled={isStreaming}
        className="rounded-lg bg-blue-500 px-4 py-2 text-sm text-white transition-colors hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
      >
        发送
      </button>
      <button
        type="button"
        onClick={clearMessages}
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-500 transition-colors hover:bg-gray-100"
      >
        清空
      </button>
    </form>
  );
}
