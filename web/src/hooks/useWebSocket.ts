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
  | { type: 'files.download'; path: string }
  | { type: 'files.upload'; path: string; content: string }
  | { type: 'files.delete'; path: string };

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
  | { type: 'files.deleted'; path: string }
  | { type: 'files.list'; files: Array<{ name: string; size: number; modified: string }> }
  | { type: 'files.content'; path: string; content: string; error?: string };

export interface UseWebSocketReturn {
  send: (msg: WsClientMessage) => void;
  messages: WsServerMessage[];
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  clearMessages: () => void;
  clearError: () => void;
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
  const retryRef = useRef(0);
  const timerRef = useRef<number | null>(null);
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
    // Force-close any existing connection so every connect() starts fresh.
    // wsRef is nulled BEFORE close so the stale socket's onclose (which
    // fires asynchronously) is ignored by the identity guard below.
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    setError(null);

    const ws = new WebSocket(_getWsUrl());

    ws.onopen = () => {
      if (wsRef.current !== ws) return; // stale socket opened — ignore
      retryRef.current = 0;
      setIsConnected(true);
      // Flush pending messages
      const pending = pendingRef.current;
      pendingRef.current = [];
      for (const msg of pending) {
        ws.send(JSON.stringify(msg));
      }
    };

    ws.onclose = () => {
      if (wsRef.current !== ws) return; // stale socket closed — ignore
      setIsConnected(false);
      // Unexpected close: reconnect with a small backoff (bounded retries)
      if (retryRef.current < 5) {
        retryRef.current += 1;
        timerRef.current = window.setTimeout(() => {
          timerRef.current = null;
          connect();
        }, 2000);
      }
    };

    ws.onerror = () => { if (wsRef.current === ws) setError('WebSocket connection error'); };
    ws.onmessage = onMessage;

    wsRef.current = ws;
  }, [onMessage]);

  const disconnect = useCallback(() => {
    // Null the ref first so the close event below is ignored
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const send = useCallback((msg: WsClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else {
      // Not (yet) connected: queue for delivery and make sure we connect.
      // Auto-reconnect flushes the queue on the next successful open.
      pendingRef.current.push(msg);
      connect();
    }
  }, [connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { send, messages, isConnected, connect, disconnect, clearMessages, clearError, error };
}
