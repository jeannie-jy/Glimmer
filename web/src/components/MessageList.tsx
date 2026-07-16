import React, { useRef, useEffect } from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
import TextBubble from './TextBubble';
import UserBubble from './UserBubble';
import ToolCard from './ToolCard';
import FeedbackBanner from './FeedbackBanner';
import StateChip from './StateChip';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MessageListProps {
  messages: WsServerMessage[];
  task: string;
  agentState: AgentState;
  /** Pre-built display items from loaded session history (renders before WS messages) */
  historyItems?: Array<{ id: number; type: string; data: unknown }>;
}

// ---------------------------------------------------------------------------
// Helpers — build display items from raw WebSocket messages
// ---------------------------------------------------------------------------

function buildDisplayItems(
  messages: WsServerMessage[],
  task: string,
  agentState: AgentState,
  historyItems?: Array<{ id: number; type: string; data: unknown }>,
) {
  const items: Array<{ id: number; type: string; data: unknown }> = [...(historyItems || [])];
  let i = 0;

  // Prepend user task bubble if one was submitted
  if (task) {
    items.push({
      id: -1,
      type: 'user',
      data: { content: task },
    });
  }

  while (i < messages.length) {
    const msg = messages[i];

    // --- State change → inline thinking indicator ---
    if (msg.type === 'state.change') {
      const state = msg.to;
      // Skip idle and completed/error — those are shown as session banner or initial state
      const meaningful = !['idle', 'completed', 'error'].includes(state);
      if (meaningful) {
        // Look ahead for a tool.invoke right after this state change → capture tool name
        let toolName: string | undefined;
        if (state === 'executing') {
          let k = i + 1;
          while (k < messages.length) {
            if (messages[k].type === 'tool.invoke') {
              toolName = messages[k].tool;
              break;
            }
            if (messages[k].type === 'state.change') break;
            k++;
          }
        }

        // Determine if this state chip is still "active" — it is if no subsequent
        // "resolution" message has arrived yet (llm.response, tool.result, feedback,
        // another state.change to a different phase, or session terminal).
        let isActive = agentState === state;
        // If the current agentState has progressed past this state, it is resolved
        const stateOrder = ['idle', 'planning', 'executing', 'observing', 'correcting'];
        const currentIdx = stateOrder.indexOf(agentState);
        const thisIdx = stateOrder.indexOf(state);
        if (currentIdx > thisIdx && currentIdx !== -1 && thisIdx !== -1) {
          isActive = false;
        }
        // awaiting_human is special — only active when agent is actually awaiting
        if (state === 'awaiting_human') {
          isActive = agentState === 'awaiting_human';
        }

        // Collapse consecutive identical state transitions
        const prevItem = items[items.length - 1];
        const isDuplicate =
          prevItem?.type === 'state' &&
          (prevItem.data as { state: string }).state === state;

        if (!isDuplicate) {
          items.push({
            id: i,
            type: 'state',
            data: { state, from: msg.from, toolName, isActive },
          });
        }
      }
      i++;
      continue;
    }

    // --- LLM response (full) or stream deltas ---
    if (msg.type === 'llm.response' || msg.type === 'llm.stream') {
      let content = msg.type === 'llm.response' ? msg.content : msg.delta;
      let j = i + 1;

      // Aggregate adjacent stream deltas
      if (msg.type === 'llm.stream') {
        while (j < messages.length && messages[j].type === 'llm.stream') {
          content += (messages[j] as typeof msg).delta;
          j++;
        }
      }

      items.push({
        id: i,
        type: 'llm',
        data: { content, isStreaming: false },
      });
      i = j;
      continue;
    }

    // --- Tool invocation → paired with result ---
    if (msg.type === 'tool.invoke') {
      let result = null;
      let j = i + 1;
      while (j < messages.length) {
        if (messages[j].type === 'tool.result') {
          const r = messages[j];
          if (r.tool_name === msg.tool) {
            result = r;
            break;
          }
        }
        j++;
      }

      items.push({
        id: i,
        type: 'tool',
        data: {
          toolName: msg.tool,
          args: msg.args,
          exitCode: result?.exit_code,
          stdout: result?.stdout,
          stderr: result?.stderr,
          durationMs: result?.duration_ms,
          status: result ? ('completed' as const) : ('invoked' as const),
        },
      });
      i = result ? j + 1 : i + 1;
      continue;
    }

    // --- Feedback analysis ---
    if (msg.type === 'feedback.analysis') {
      items.push({
        id: i,
        type: 'feedback',
        data: {
          verdict: msg.verdict,
          summary: msg.summary || '',
          failures: msg.failures || [],
          suggestedFix: msg.suggested_fix || '',
          retryCount: msg.retry_count || 0,
        },
      });
      i++;
      continue;
    }

    // --- Session terminal ---
    // Skip session.complete — just a noise banner
    if (msg.type === 'session.complete') {
      i++;
      continue;
    }

    if (msg.type === 'session.error') {
      items.push({
        id: i,
        type: 'session',
        data: { message: msg.message, isError: true },
      });
      i++;
      continue;
    }

    // Skip unknown message types
    i++;
  }

  // --- Streaming placeholder: agent is planning but no response yet ---
  if (agentState === 'planning') {
    const lastRaw = messages[messages.length - 1];
    const hasResponse =
      lastRaw?.type === 'llm.response' ||
      lastRaw?.type === 'session.complete' ||
      lastRaw?.type === 'session.error';
    const lastItem = items[items.length - 1];
    const lastIsLLm = lastItem?.type === 'llm';
    if (!hasResponse && !lastIsLLm) {
      items.push({
        id: -2,
        type: 'llm',
        data: { content: '', isStreaming: true },
      });
    }
  }

  return items;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const MessageList: React.FC<MessageListProps> = ({
  messages,
  task,
  agentState,
  historyItems,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const items = buildDisplayItems(messages, task, agentState, historyItems);

  if (items.length === 0) {
    return (
      <div className="message-list message-list--empty">
        <div className="message-list__placeholder">
          <p>Submit a task to begin.</p>
          <p className="message-list__hint">
            The agent will read, write, and execute code to complete your
            request.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {items.map((item) => {
        switch (item.type) {
          // -- User bubble ---
          case 'user': {
            const d = item.data as { content: string };
            return (
              <div
                key={item.id}
                className="message-list__item message-list__item--user"
              >
                <UserBubble content={d.content} />
              </div>
            );
          }

          // --- State chip ---
          case 'state': {
            const d = item.data as {
              state: string;
              from?: string;
              toolName?: string;
              isActive: boolean;
            };
            return (
              <div
                key={item.id}
                className="message-list__item message-list__item--state"
              >
                <StateChip
                  state={d.state}
                  toolName={d.toolName}
                  isActive={d.isActive}
                />
              </div>
            );
          }

          // --- LLM text ---
          case 'llm': {
            const d = item.data as { content: string; isStreaming: boolean };
            return (
              <div key={item.id} className="message-list__item">
                <TextBubble
                  content={d.content}
                  isStreaming={d.isStreaming}
                />
              </div>
            );
          }

          // --- Tool card ---
          case 'tool': {
            const d = item.data as {
              toolName: string;
              args: Record<string, unknown>;
              exitCode?: number;
              stdout?: string;
              stderr?: string;
              durationMs?: number;
              status: 'invoked' | 'completed';
            };
            return (
              <div key={item.id} className="message-list__item">
                <ToolCard
                  toolName={d.toolName}
                  args={d.args}
                  exitCode={d.exitCode}
                  stdout={d.stdout}
                  stderr={d.stderr}
                  durationMs={d.durationMs}
                  status={d.status}
                />
              </div>
            );
          }

          // --- Feedback banner ---
          case 'feedback': {
            const d = item.data as {
              verdict: string;
              summary: string;
              failures: Array<{
                file: string;
                line?: number;
                function?: string;
                message: string;
              }>;
              suggestedFix: string;
              retryCount: number;
            };
            return (
              <div key={item.id} className="message-list__item">
                <FeedbackBanner
                  verdict={d.verdict}
                  summary={d.summary}
                  failures={d.failures}
                  suggestedFix={d.suggestedFix}
                  retryCount={d.retryCount}
                />
              </div>
            );
          }

          // --- Session terminal ---
          case 'session': {
            const d = item.data as { message: string; isError?: boolean };
            return (
              <div key={item.id} className="message-list__item">
                <div
                  className={`message-list__session ${
                    d.isError
                      ? 'message-list__session--error'
                      : 'message-list__session--complete'
                  }`}
                >
                  {d.message}
                </div>
              </div>
            );
          }

          default:
            return null;
        }
      })}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
