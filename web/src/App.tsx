import { ChatWindow } from "./components/ChatWindow";
import { SessionSidebar } from "./components/SessionSidebar";

export default function App() {
  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-center border-b bg-white px-4 py-3 shadow-sm">
        <h1 className="text-lg font-semibold text-gray-800">MyAgent</h1>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <SessionSidebar />
        <main className="flex-1 overflow-hidden">
          <ChatWindow />
        </main>
      </div>
    </div>
  );
}
