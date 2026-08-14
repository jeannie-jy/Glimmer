import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';

export type DisplayItem = {
  id: number; kind: 'user' | 'state' | 'llm' | 'tool' | 'feedback' | 'session' | 'agent-group';
  data: unknown; children?: DisplayItem[];
};

const UPLOAD_RE = /\[User has uploaded these files to the working directory:\s*([^\]]+)\]/;
export function parseUploadedFiles(content: string): { cleanText: string; files?: Array<{name: string; size: number}> } {
  const m = content.match(UPLOAD_RE);
  if (!m) return { cleanText: content };
  const files: Array<{name: string; size: number}> = [];
  for (const part of m[1].split(/,\s*/)) {
    const fm = part.match(/^(.+?)\s+\(([^)]+)\)$/);
    if (fm) { let size = 0; const s = fm[2].trim(); if (s.endsWith('MB')) size = Math.round(parseFloat(s) * 1048576); else if (s.endsWith('KB')) size = Math.round(parseFloat(s) * 1024); else if (s.endsWith('B')) size = parseInt(s) || 0; files.push({ name: fm[1].trim(), size }); }
  }
  return { cleanText: content.replace(UPLOAD_RE, '').trim(), files: files.length > 0 ? files : undefined };
}

export function buildDisplayItems(
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

  // A turn boundary: the loop enters PLANNING from a rest state, i.e. at the
  // start of a brand-new user request. Mid-turn re-entries into PLANNING
  // (observing→planning to generate the final answer, correcting→planning to
  // retry) must NOT emit the next user message — they belong to the same
  // Agent Run, which has to stay one uninterrupted block.
  const TURN_START_FROM = ['idle', 'completed', 'error'];
  const isTurnStartPlanning = (m: WsServerMessage) =>
    m.type === 'state.change' && m.to === 'planning' && TURN_START_FROM.includes(m.from);

  let i = 0;
  while (i < messages.length) {
    const msg = messages[i];
    if (isTurnStartPlanning(msg)) emitUserIfNeeded();

    if (msg.type === 'state.change') {
      const state = msg.to;
      if (!['idle', 'completed', 'error'].includes(state)) {
        let toolName: string | undefined;
        if (state === 'executing') { let k = i + 1; while (k < messages.length) { const m = messages[k]; if (m.type === 'tool.invoke') { toolName = m.tool; break; } if (m.type === 'state.change') break; k++; } }
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
