import React, { useRef, useEffect } from 'react';
import { File } from 'lucide-react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
import { buildDisplayItems, parseUploadedFiles, type DisplayItem } from './messageTimeline';
import TextBubble from './TextBubble';
import UserBubble from './UserBubble';
import ToolCard from './ToolCard';
import FeedbackBanner from './FeedbackBanner';
import StateChip from './StateChip';

interface MessageListProps {
  messages: WsServerMessage[]; task: string; agentState: AgentState;
  userTasks?: Array<{text: string; files?: Array<{name: string; size: number}>}>;
  historyItems?: Array<{ id: number; type: string; data: unknown }>;
}

const MessageList: React.FC<MessageListProps> = ({ messages, task, agentState, historyItems, userTasks }) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  const items = buildDisplayItems(messages, task, agentState, historyItems, userTasks);

  if (items.length === 0) return (
    <div className="message-list message-list--empty">
      <div className="message-list__placeholder"><p>Submit a task to begin.</p><p className="message-list__hint">The agent will read, write, and execute code to complete your request.</p></div>
    </div>
  );

  const renderItem = (item: DisplayItem) => {
    switch (item.kind) {
      case 'user': { const d = item.data as { content: string; files?: Array<{name: string; size: number}> }; const parsed = parseUploadedFiles(d.content); const df = d.files && d.files.length > 0 ? d.files : parsed.files; const dc = parsed.cleanText || d.content; return (<>{df && df.length > 0 && (<div className="message-list__attachments">{df.map((f,i)=>(<span key={i} className="message-list__attachments-chip"><span className="message-list__attachments-icon"><File size={14} /></span><span className="message-list__attachments-name">{f.name}</span><span className="message-list__attachments-size">{f.size<1024?`${f.size}B`:f.size<1048576?`${(f.size/1024).toFixed(1)}KB`:`${(f.size/1048576).toFixed(1)}MB`}</span></span>))}</div>)}<UserBubble content={dc} /></>); }
      case 'state': { const d = item.data as { state: string; from?: string; toolName?: string; isActive: boolean }; return <StateChip state={d.state} toolName={d.toolName} isActive={d.isActive} />; }
      case 'llm': { const d = item.data as { content: string; isStreaming: boolean }; return <TextBubble content={d.content} isStreaming={d.isStreaming} />; }
      case 'tool': { const d = item.data as any; return <ToolCard toolName={d.toolName} args={d.args} exitCode={d.exitCode} stdout={d.stdout} stderr={d.stderr} durationMs={d.durationMs} structured={d.structured} status={d.status} />; }
      case 'feedback': { const d = item.data as any; return <FeedbackBanner verdict={d.verdict} summary={d.summary} failures={d.failures} suggestedFix={d.suggestedFix} retryCount={d.retryCount} />; }
      case 'session': { const d = item.data as { message: string; isError?: boolean }; return <div className={`message-list__session ${d.isError?'message-list__session--error':'message-list__session--complete'}`}>{d.message}</div>; }
      default: return null;
    }
  };

  return (
    <div className="message-list">
      {items.map(item => {
        if (item.kind === 'user') return <div key={item.id} className="message-list__turn message-list__turn--user">{renderItem(item)}</div>;
        if (item.kind === 'agent-group' && item.children) return <div key={item.id} className="message-list__turn message-list__turn--agent">{item.children.map(c => <div key={c.id} className="message-list__agent-item">{renderItem(c)}</div>)}</div>;
        return <div key={item.id} className="message-list__item">{renderItem(item)}</div>;
      })}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
