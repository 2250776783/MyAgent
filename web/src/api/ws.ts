import type { StreamEventData } from "../types/chat";

type EventHandler = {
  onToken: (text: string) => void;
  onToolCall: (data: StreamEventData) => void;
  onToolResult: (data: StreamEventData) => void;
  onDone: (sessionId: string) => void;
  onError: (message: string) => void;
};

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private handlers: EventHandler | null = null;
  private url: string;
  private messageQueue: Array<{ message: string; sessionId?: string }> = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  constructor(url: string) {
    this.url = url;
  }

  connect(handlers: EventHandler): void {
    this.handlers = handlers;
    this.intentionalClose = false;
    this._open();
  }

  private _open(): void {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      if (this.ws.readyState === WebSocket.OPEN) return;
      this.ws.close();
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this._flushQueue();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const { type, data } = JSON.parse(event.data) as {
          type: string;
          data: StreamEventData;
        };
        this._dispatch(type, data);
      } catch {
        console.warn("Failed to parse WebSocket message:", event.data);
      }
    };

    this.ws.onerror = () => {
      // don't report to user — auto-reconnect handles it silently
    };

    this.ws.onclose = () => {
      if (!this.intentionalClose && this.handlers) {
        this._scheduleReconnect();
      }
    };
  }

  private _dispatch(type: string, data: StreamEventData): void {
    if (!this.handlers) return;
    switch (type) {
      case "token":
        this.handlers.onToken(data.text ?? "");
        break;
      case "tool_call":
        this.handlers.onToolCall(data);
        break;
      case "tool_result":
        this.handlers.onToolResult(data);
        break;
      case "done":
        this.handlers.onDone(data.session_id ?? "");
        break;
      case "error":
        this.handlers.onError(data.message ?? "未知错误");
        break;
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.handlers) {
        this._open();
      }
    }, 1000);
  }

  private _flushQueue(): void {
    if (!this.ws) return;
    for (const item of this.messageQueue) {
      this.ws.send(JSON.stringify({ message: item.message, session_id: item.sessionId }));
    }
    this.messageQueue = [];
  }

  send(message: string, sessionId?: string): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message, session_id: sessionId }));
      return true;
    }
    // queue for when connection is ready
    this.messageQueue.push({ message, sessionId });
    return false;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  hasQueuedMessages(): boolean {
    return this.messageQueue.length > 0;
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.handlers = null;
    this.messageQueue = [];
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }
}
