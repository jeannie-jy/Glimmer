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
          // The loop left awaiting_human (approve/reject resumed it, or the
          // guardrail was resolved some other way) — dismiss the modal.
          if (msg.to !== 'awaiting_human') {
            pendingGuardrail = null;
          }
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
          pendingGuardrail = null;
          break;
        case 'session.error':
          state = 'error';
          pendingGuardrail = null;
          break;
        case 'session.created':
          sessionId = msg.session_id;
          break;
        case 'session.saved':
          sessionId = msg.session_id;
          break;
      }
    }

    return { state, currentTask: task, retryCount, pendingGuardrail, sessionId };
  }, [messages, task]);
}
