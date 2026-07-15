import React, { useRef, useEffect } from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import TextBubble from './TextBubble';
import ToolCard from './ToolCard';
import FeedbackBanner from './FeedbackBanner';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MessageListProps {
  messages: WsServerMessage[];
}

// ---------------------------------------------------------------------------
// Helpers — pair tool.invoke → tool.result
// ---------------------------------------------------------------------------

/** Merge consecutive tool.invoke/tool.result pairs into one display entry. */
function buildDisplayItems(messages: WsServerMessage[]) {
  const items: Array<{ id: number; type: string; data: unknown }> = [];
  let i = 0;

  while (i < messages.length) {
    const msg = messages[i];

    if (msg.type === 'llm.response' || msg.type === 'llm.stream') {
      // Accumulate full content from potentially multiple stream messages
      let content = msg.type === 'llm.response' ? msg.content : msg.delta;
      let j = i + 1;

      // If this is a stream, aggregate adjacent stream deltas
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
    } else if (msg.type === 'tool.invoke') {
      // Look ahead for the corresponding result
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
    } else if (msg.type === 'feedback.analysis') {
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
    } else if (msg.type === 'session.complete') {
      items.push({
        id: i,
        type: 'session',
        data: { message: 'Session completed successfully' },
      });
      i++;
    } else if (msg.type === 'session.error') {
      items.push({
        id: i,
        type: 'session',
        data: { message: msg.message, isError: true },
      });
      i++;
    } else {
      i++;
    }
  }

  return items;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const items = buildDisplayItems(messages);

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
