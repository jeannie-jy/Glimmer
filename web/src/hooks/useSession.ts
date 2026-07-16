import { useMemo } from 'react';
import type { WsServerMessage } from './useWebSocket';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AgentState =
  | 'idle'
  | 'planning'
  | 'executing'
  | 'observing'
  | 'correcting'
  | 'awaiting_human'
  | 'completed'
  | 'error';

export interface PendingGuardrail {
  action: string;
  reason: string;
  tool?: string;
  args?: Record<string, unknown>;
}

export interface SessionInfo {
  state: AgentState;
  currentTask: string;
  retryCount: number;
  pendingGuardrail: PendingGuardrail | null;
  sessionId: string;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSession(
  messages: WsServerMessage[],
  task: string,
): SessionInfo {
  return useMemo(() => {
    let state: AgentState = 'idle';
    let retryCount = 0;
    let pendingGuardrail: PendingGuardrail | null = null;
    let sessionId = '';

    for (const msg of messages) {
      switch (msg.type) {
        case 'state.change':
          state = msg.to as AgentState;
          break;
        case 'feedback.analysis':
          retryCount = msg.retry_count ?? retryCount;
          break;
        case 'guardrail.pending':
          pendingGuardrail = {
            action: msg.action,
            reason: msg.reason,
            tool: msg.tool,
            args: msg.args,
          };
          break;
        case 'session.complete':
          state = 'completed';
          break;
        case 'session.error':
          state = 'error';
          break;
        case 'session.created':
          sessionId = msg.session_id;
          break;
      }
    }

    return { state, currentTask: task, retryCount, pendingGuardrail, sessionId };
  }, [messages, task]);
}
