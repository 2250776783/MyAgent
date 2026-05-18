export interface SessionSummary {
  id: string;
  created_at: number;
}

export interface ChatMessageData {
  role: "user" | "assistant";
  content: string;
}

export async function fetchSessions(): Promise<SessionSummary[]> {
  const res = await fetch("/api/sessions");
  const data = await res.json();
  return data.sessions ?? [];
}

export async function fetchSessionMessages(
  sessionId: string,
): Promise<ChatMessageData[]> {
  const res = await fetch(`/api/sessions/${sessionId}/messages`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.messages ?? [];
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  const res = await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
  return res.ok;
}
