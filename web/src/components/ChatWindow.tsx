import { useChatStore } from "../store/chat";
import { InputBar } from "./InputBar";
import { MessageList } from "./MessageList";

export function ChatWindow() {
  const error = useChatStore((s) => s.error);
  const clearError = useChatStore((s) => s.clearError);

  return (
    <div className="flex h-full flex-col">
      {error && (
        <div className="mx-4 mt-2 flex items-center justify-between rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">
          <span>{error}</span>
          <button onClick={clearError} className="ml-2 font-bold hover:text-red-800">
            x
          </button>
        </div>
      )}
      <MessageList />
      <InputBar />
    </div>
  );
}
