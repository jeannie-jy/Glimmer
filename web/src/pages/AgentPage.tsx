import React, { useState, useCallback, useRef, useEffect } from 'react';
import PageTransition from '../components/PageTransition';
import { useWebSocket, type WsServerMessage } from '../hooks/useWebSocket';
import type { Attachment } from '../components/InputBar';
import { useSession, type AgentState } from '../hooks/useSession';
import ChatView from '../components/ChatView';
import HistorySidebar from '../components/HistorySidebar';
import SettingsPanel from '../components/SettingsPanel';
import FilePanel from '../components/FilePanel';
import GuardrailModal from '../components/GuardrailModal';
import { getSession } from '../services/api';
import '../styles/agent.css';
import { Settings, FolderOpen } from 'lucide-react';

function dbMsgToDisplayItem(msg: { type: string; payload: Record<string, unknown> }, idx: number): { id: number; type: string; data: unknown } | null {
  const content = (msg.payload as { content?: string })?.content || '';
  if (!content) return null;
  if (msg.type === 'user') return { id: -1000 - idx, type: 'user', data: { content } };
  if (msg.type === 'assistant') return { id: -1000 - idx, type: 'llm', data: { content, isStreaming: false } };
  return null;
}

const AgentPage: React.FC = () => {
  const { send, messages, isConnected, connect, disconnect, clearMessages, clearError, error: wsError } = useWebSocket();
  const [task, setTask] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filesOpen, setFilesOpen] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [historyItems, setHistoryItems] = useState<Array<{ id: number; type: string; data: unknown }>>([]);
  const [userMessages, setUserMessages] = useState<Array<{text: string; files?: Array<{name: string; size: number}>}>>([]);
  const [focusKey, setFocusKey] = useState(0);
  const activeSessionIdRef = useRef(activeSessionId);
  useEffect(() => { activeSessionIdRef.current = activeSessionId; }, [activeSessionId]);
  const taskSubmittedRef = useRef(false);
  const { state, pendingGuardrail, sessionId } = useSession(messages, task);

  useEffect(() => { if (sessionId && sessionId !== activeSessionId && historyItems.length === 0) { setActiveSessionId(sessionId); setUserMessages([]); } }, [sessionId, activeSessionId, historyItems.length]);
  useEffect(() => { if (state === 'completed' || state === 'error') setHistoryKey(k => k + 1); }, [state]);
  useEffect(() => { if (wsError) { const t = setTimeout(() => clearError(), 3000); return () => clearTimeout(t); } }, [wsError, clearError]);
  useEffect(() => { connect(); return () => { disconnect(); }; }, []); // eslint-disable-line

  const handleSend = useCallback(async (text: string, attachments?: Attachment[]) => {
    setTask(text);
    const fileInfo = attachments?.map(a => ({ name: a.name, size: a.size }));
    setUserMessages(prev => [...prev, { text, files: fileInfo }]);
    taskSubmittedRef.current = true;
    let contextText = text;
    if (attachments && attachments.length > 0) {
      if (!isConnected) { connect(); await new Promise(r => setTimeout(r, 300)); }
      const fileList = attachments.map(a => `${a.name} (${a.size < 1024 ? `${a.size}B` : a.size < 1048576 ? `${(a.size/1024).toFixed(1)}KB` : `${(a.size/1048576).toFixed(1)}MB`})`).join(', ');
      for (const att of attachments) send({ type: 'files.upload', path: att.name, content: att.contentB64 } as any);
      await new Promise(r => setTimeout(r, 500));
      contextText = `[User has uploaded these files to the working directory: ${fileList}]\n\n${text || 'Please analyze the attached files.'}`;
    }
    const payload: { type: 'task.submit'; content: string; session_id?: string } = { type: 'task.submit', content: contextText };
    if (activeSessionIdRef.current) payload.session_id = activeSessionIdRef.current;
    if (!isConnected) { connect(); setTimeout(() => send(payload), 300); } else { send(payload); }
  }, [connect, send, isConnected]);

  const handleNewSession = useCallback(() => {
    if (isConnected) send({ type: 'session.new' });
    setTask(''); setActiveSessionId(''); setHistoryItems([]); setUserMessages([]);
    taskSubmittedRef.current = false; clearMessages();
  }, [send, clearMessages, isConnected]);

  const handleLoadSession = useCallback(async (sessionId: string) => {
    try {
      const data = await getSession(sessionId);
      const items: Array<{ id: number; type: string; data: unknown }> = [];
      for (let i = 0; i < data.messages.length; i++) { const item = dbMsgToDisplayItem(data.messages[i], i); if (item) items.push(item); }
      setActiveSessionId(sessionId); setHistoryItems(items); setTask(''); setUserMessages([]); clearMessages(); setFocusKey(k => k + 1);
    } catch {}
  }, [clearMessages]);

  const handleStop = useCallback(() => { send({ type: 'session.cancel' }); }, [send]);
  const handleGuardrailApprove = useCallback(() => { send({ type: 'guardrail.approve' }); }, [send]);
  const handleGuardrailReject = useCallback(() => { send({ type: 'guardrail.reject' }); }, [send]);

  const chatState: AgentState = state === 'idle' && !task ? 'idle' : state;
  const displayTask = historyItems.length > 0 ? '' : task;
  const displayState: AgentState = historyItems.length > 0 ? (messages.length > 0 ? state : 'idle') : chatState;
  const awaitingHuman = state === 'awaiting_human';

  return (
    <PageTransition>
      <div className="agent-page">
        <aside className="agent-page__sidebar agent-page__sidebar--left">
          <HistorySidebar key={historyKey} activeSessionId={activeSessionId} onSelect={handleLoadSession} onNewSession={handleNewSession} />
        </aside>
        <main className="agent-page__main">
          <ChatView messages={messages} state={displayState} task={displayTask} onSend={handleSend} onStop={handleStop} onNewSession={handleNewSession}
            userTasks={userMessages.length > 0 ? userMessages : undefined} historyItems={historyItems.length > 0 ? historyItems : undefined} focusKey={focusKey} />
          {wsError && <div className="agent-page__error-banner">{wsError}</div>}
          {!isConnected && taskSubmittedRef.current && state !== 'completed' && state !== 'error' && <div className="agent-page__connecting">Connecting...</div>}
          {awaitingHuman && <div className="agent-page__awaiting-banner">Agent is waiting for your approval.</div>}
        </main>
        <aside className="agent-page__sidebar agent-page__sidebar--right">
          <div className="agent-page__sidebar-tabs">
            <button className={`agent-page__sidebar-tab ${settingsOpen ? 'agent-page__sidebar-tab--active' : ''}`} onClick={() => { setSettingsOpen(!settingsOpen); setFilesOpen(false); }} type="button"><Settings size={14} /> Settings</button>
            <button className={`agent-page__sidebar-tab ${filesOpen ? 'agent-page__sidebar-tab--active' : ''}`} onClick={() => { setFilesOpen(!filesOpen); setSettingsOpen(false); }} type="button"><FolderOpen size={14} /> Files</button>
          </div>
          {settingsOpen && <SettingsPanel />}
          {filesOpen && <FilePanel messages={messages} onSend={(msg) => send(msg as { type: string; path?: string })} isConnected={isConnected} />}
        </aside>
        <GuardrailModal guardrail={pendingGuardrail} onApprove={handleGuardrailApprove} onReject={handleGuardrailReject} />
      </div>
    </PageTransition>
  );
};

export default AgentPage;
