import { useRef, useState, useCallback, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type WsClientMessage =
  | { type: 'task.submit'; content: string; session_id?: string }
  | { type: 'session.new' }
  | { type: 'session.load'; session_id: string }
  | { type: 'guardrail.approve' }
  | { type: 'guardrail.reject' }
  | { type: 'session.cancel' }
  | { type: 'files.list' }
  | { type: 'files.download'; path: string };

export type WsServerMessage =
  | { type: 'state.change'; from: string; to: string }
  | { type: 'llm.response'; content: string; tool_calls?: unknown[] }
  | { type: 'llm.stream'; delta: string; index?: number; done?: boolean }
  | { type: 'tool.invoke'; tool: string; args: Record<string, unknown> }
  | { type: 'tool.result'; tool_name: string; exit_code: number; stdout?: string; stderr?: string; duration_ms?: number }
  | { type: 'guardrail.pending'; action: string; reason: string; tool?: string; args?: Record<string, unknown> }
  | { type: 'feedback.analysis'; verdict: string; failures?: Array<{ file: string; line?: number; function?: string; message: string }>; summary?: string; suggested_fix?: string; retry_count?: number }
  | { type: 'session.complete' }
  | { type: 'session.error'; message: string }
  | { type: 'session.created'; session_id: string }
  | { type: 'session.saved'; session_id: string }
  | { type: 'session.loaded'; session_id: string; task: string; message_count: number }
  | { type: 'file.created'; path: string }
  | { type: 'file.modified'; path: string }
  | { type: 'files.list'; files: Array<{ name: string; size: number; modified: string }> }
  | { type: 'files.content'; path: string; content: string; error?: string };

export interface UseWebSocketReturn {
  send: (msg: WsClientMessage) => void;
  messages: WsServerMessage[];
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  clearMessages: () => void;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

const _getWsUrl = () => {
  const token = localStorage.getItem('glimmer_token');
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const tokenParam = token ? `?token=${token}` : '';
  return `${protocol}//${location.host}/ws/session${tokenParam}`;
};

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef<WsClientMessage[]>([]);
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
    // Force-close any existing connection so every connect() starts fresh
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setError(null);
    setMessages([]);

    const ws = new WebSocket(_getWsUrl());

    ws.onopen = () => {
      setIsConnected(true);
      // Flush pending messages
      const pending = pendingRef.current;
      pendingRef.current = [];
      for (const msg of pending) {
        ws.send(JSON.stringify(msg));
      }
    };

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

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const send = useCallback((msg: WsClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      // Queue message to be sent once connected
      pendingRef.current.push(msg);
    } else {
      setError('WebSocket is not connected');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { send, messages, isConnected, connect, disconnect, clearMessages, error };
}
