import { useRef, useState, useCallback, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type WsClientMessage =
  | { type: 'task.submit'; content: string }
  | { type: 'guardrail.approve' }
  | { type: 'guardrail.reject' }
  | { type: 'session.cancel' };

export type WsServerMessage =
  | { type: 'state.change'; from: string; to: string }
  | { type: 'llm.response'; content: string; tool_calls?: unknown[] }
  | { type: 'llm.stream'; delta: string; index?: number; done?: boolean }
  | {
      type: 'tool.invoke';
      tool: string;
      args: Record<string, unknown>;
    }
  | {
      type: 'tool.result';
      tool_name: string;
      exit_code: number;
      stdout?: string;
      stderr?: string;
      duration_ms?: number;
    }
  | {
      type: 'guardrail.pending';
      action: string;
      reason: string;
      tool?: string;
      args?: Record<string, unknown>;
    }
  | {
      type: 'feedback.analysis';
      verdict: string;
      failures?: Array<{
        file: string;
        line?: number;
        function?: string;
        message: string;
      }>;
      summary?: string;
      suggested_fix?: string;
      retry_count?: number;
    }
  | { type: 'session.complete' }
  | { type: 'session.error'; message: string };

export interface UseWebSocketReturn {
  send: (msg: WsClientMessage) => void;
  messages: WsServerMessage[];
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

const WS_URL = 'ws://localhost:8000/ws/session';

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<WsServerMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onMessage = useCallback((event: MessageEvent) => {
    try {
      const data: WsServerMessage = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
    } catch {
      setError('Failed to parse WebSocket message');
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setError(null);
    setMessages([]);

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setError('WebSocket connection error');
    ws.onmessage = onMessage;

    wsRef.current = ws;
  }, [onMessage]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const send = useCallback(
    (msg: WsClientMessage) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(msg));
      } else {
        setError('WebSocket is not connected');
      }
    },
    [],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { send, messages, isConnected, connect, disconnect, error };
}
