import React, { useRef, useEffect } from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
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

type DisplayItem = {
  id: number; kind: 'user' | 'state' | 'llm' | 'tool' | 'feedback' | 'session' | 'agent-group';
  data: unknown; children?: DisplayItem[];
};

const UPLOAD_RE = /\[User has uploaded these files to the working directory:\s*([^\]]+)\]/;
function parseUploadedFiles(content: string): { cleanText: string; files?: Array<{name: string; size: number}> } {
  const m = content.match(UPLOAD_RE);
  if (!m) return { cleanText: content };
  const files: Array<{name: string; size: number}> = [];
  for (const part of m[1].split(/,\s*/)) {
    const fm = part.match(/^(.+?)\s+\(([^)]+)\)$/);
    if (fm) { let size = 0; const s = fm[2].trim(); if (s.endsWith('MB')) size = Math.round(parseFloat(s) * 1048576); else if (s.endsWith('KB')) size = Math.round(parseFloat(s) * 1024); else if (s.endsWith('B')) size = parseInt(s) || 0; files.push({ name: fm[1].trim(), size }); }
  }
  return { cleanText: content.replace(UPLOAD_RE, '').trim(), files: files.length > 0 ? files : undefined };
}

function buildDisplayItems(
  messages: WsServerMessage[], task: string, agentState: AgentState,
  historyItems?: Array<{ id: number; type: string; data: unknown }>,
  userTasks?: Array<{text: string; files?: Array<{name: string; size: number}>}>,
): DisplayItem[] {
  const rawItems: DisplayItem[] = (historyItems || []).map(h => ({ id: h.id, kind: h.type as DisplayItem['kind'], data: h.data }));
  let userTaskIdx = 0;
  const userMsgs = userTasks ? [...userTasks] : [];

  const emitUserIfNeeded = () => {
    if (userTaskIdx < userMsgs.length) {
      const um = userMsgs[userTaskIdx];
      rawItems.push({ id: -2000 - userTaskIdx, kind: 'user', data: { content: typeof um === 'string' ? um : um.text, files: typeof um === 'string' ? undefined : um.files } });
      userTaskIdx++;
    }
  };

  let i = 0;
  while (i < messages.length) {
    const msg = messages[i];
    if (msg.type === 'state.change' && msg.to === 'planning') emitUserIfNeeded();

    if (msg.type === 'state.change') {
      const state = msg.to;
      if (!['idle', 'completed', 'error'].includes(state)) {
        let toolName: string | undefined;
        if (state === 'executing') { let k = i + 1; while (k < messages.length) { if (messages[k].type === 'tool.invoke') { toolName = messages[k].tool; break; } if (messages[k].type === 'state.change') break; k++; } }
        let isActive = agentState === state;
        const so = ['idle','planning','executing','observing','correcting'];
        const ci = so.indexOf(agentState), ti = so.indexOf(state);
        if (ci > ti && ci !== -1 && ti !== -1) isActive = false;
        if (state === 'awaiting_human') isActive = agentState === 'awaiting_human';
        const pi = rawItems[rawItems.length - 1];
        if (!(pi?.kind === 'state' && (pi.data as {state:string}).state === state))
          rawItems.push({ id: i, kind: 'state', data: { state, from: msg.from, toolName, isActive } });
      }
      i++; continue;
    }

    if (msg.type === 'llm.response' || msg.type === 'llm.stream') {
      let content = msg.type === 'llm.response' ? msg.content : msg.delta; let j = i + 1;
      if (msg.type === 'llm.stream') while (j < messages.length && messages[j].type === 'llm.stream') { content += (messages[j] as typeof msg).delta; j++; }
      rawItems.push({ id: i, kind: 'llm', data: { content, isStreaming: false } }); i = j; continue;
    }

    if (msg.type === 'tool.invoke') {
      let result: WsServerMessage | null = null; let j = i + 1;
      while (j < messages.length) { if (messages[j].type === 'tool.result' && (messages[j] as any).tool_name === msg.tool) { result = messages[j]; break; } j++; }
      rawItems.push({ id: i, kind: 'tool', data: { toolName: msg.tool, args: msg.args, exitCode: (result as any)?.exit_code, stdout: (result as any)?.stdout, stderr: (result as any)?.stderr, durationMs: (result as any)?.duration_ms, structured: (result as any)?.structured, status: result ? 'completed' as const : 'invoked' as const } });
      i = result ? j + 1 : i + 1; continue;
    }

    if (msg.type === 'feedback.analysis') { rawItems.push({ id: i, kind: 'feedback', data: { verdict: msg.verdict, summary: msg.summary || '', failures: msg.failures || [], suggestedFix: msg.suggested_fix || '', retryCount: msg.retry_count || 0 } }); i++; continue; }
    if (msg.type === 'session.complete') { i++; continue; }
    if (msg.type === 'session.error') { rawItems.push({ id: i, kind: 'session', data: { message: msg.message, isError: true } }); i++; continue; }
    i++;
  }

  while (userTaskIdx < userMsgs.length) { const um = userMsgs[userTaskIdx]; rawItems.push({ id: -2000 - userTaskIdx, kind: 'user', data: { content: typeof um === 'string' ? um : um.text, files: typeof um === 'string' ? undefined : um.files } }); userTaskIdx++; }

  // Group consecutive non-user items into agent-group containers
  const grouped: DisplayItem[] = []; let agentBuffer: DisplayItem[] = [];
  const flush = () => { if (agentBuffer.length > 0) { grouped.push({ id: agentBuffer[0].id, kind: 'agent-group', data: {}, children: [...agentBuffer] }); agentBuffer = []; } };
  for (const item of rawItems) { if (item.kind === 'user' || item.kind === 'session') { flush(); grouped.push(item); } else { agentBuffer.push(item); } }
  flush();

  if (agentState === 'planning') {
    const lr = messages[messages.length - 1];
    if (!(lr?.type === 'llm.response' || lr?.type === 'session.complete' || lr?.type === 'session.error')) {
      const lg = grouped[grouped.length - 1];
      if (lg?.kind === 'agent-group' && lg.children && lg.children.length > 0) {
        const lc = lg.children[lg.children.length - 1];
        if (lc.kind !== 'llm') lg.children.push({ id: -2, kind: 'llm', data: { content: '', isStreaming: true } });
      } else if (!lg || lg.kind === 'user') {
        grouped.push({ id: -3, kind: 'agent-group', data: {}, children: [{ id: -2, kind: 'llm', data: { content: '', isStreaming: true } }] });
      }
    }
  }

  return grouped;
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
      case 'user': { const d = item.data as { content: string; files?: Array<{name: string; size: number}> }; const parsed = parseUploadedFiles(d.content); const df = d.files && d.files.length > 0 ? d.files : parsed.files; const dc = parsed.cleanText || d.content; return (<>{df && df.length > 0 && (<div className="message-list__attachments">{df.map((f,i)=>(<span key={i} className="message-list__attachments-chip"><span className="message-list__attachments-icon">📄</span><span className="message-list__attachments-name">{f.name}</span><span className="message-list__attachments-size">{f.size<1024?`${f.size}B`:f.size<1048576?`${(f.size/1024).toFixed(1)}KB`:`${(f.size/1048576).toFixed(1)}MB`}</span></span>))}</div>)}<UserBubble content={dc} /></>); }
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
