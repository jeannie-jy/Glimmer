import React, { useState, useCallback, useRef, useEffect } from 'react';
import PageTransition from '../components/PageTransition';
import { useWebSocket, type WsServerMessage } from '../hooks/useWebSocket';
import { useSession, type AgentState } from '../hooks/useSession';
import ChatView from '../components/ChatView';
import HistorySidebar from '../components/HistorySidebar';
import SettingsPanel from '../components/SettingsPanel';
import FilePanel from '../components/FilePanel';
import GuardrailModal from '../components/GuardrailModal';
import { getSession } from '../services/api';
import '../styles/agent.css';
import { Settings, FolderOpen } from 'lucide-react';

/** Convert a single DB message to a MessageList display item. */
function dbMsgToDisplayItem(
  msg: { type: string; payload: Record<string, unknown> },
  idx: number,
): { id: number; type: string; data: unknown } | null {
  const content = (msg.payload as { content?: string })?.content || '';
  if (!content) return null;
  if (msg.type === 'user') {
    return { id: -1000 - idx, type: 'user', data: { content } };
  }
  if (msg.type === 'assistant') {
    return { id: -1000 - idx, type: 'llm', data: { content, isStreaming: false } };
  }
  // Skip system, tool, etc. — not needed for display
  return null;
}

const AgentPage: React.FC = () => {
  const { send, messages, isConnected, connect, disconnect, clearMessages, error: wsError } = useWebSocket();
  const [task, setTask] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filesOpen, setFilesOpen] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [historyItems, setHistoryItems] = useState<Array<{ id: number; type: string; data: unknown }>>([]);
  const taskSubmittedRef = useRef(false);
  const { state, pendingGuardrail, sessionId } = useSession(messages, task);

  // Track session ID from server events
  useEffect(() => {
    if (sessionId && sessionId !== activeSessionId && historyItems.length === 0) {
      setActiveSessionId(sessionId);
    }
  }, [sessionId, activeSessionId, historyItems.length]);

  // Refresh history sidebar when a session completes or errors
  useEffect(() => {
    if (state === 'completed' || state === 'error') {
      setHistoryKey(k => k + 1);
    }
  }, [state]);

  // ---- Actions ----

  const handleSend = useCallback((text: string) => {
    setTask(text);
    taskSubmittedRef.current = true;
    setHistoryItems([]);  // exit history view on new message
    if (!isConnected) {
      connect();
      setTimeout(() => { send({ type: 'task.submit', content: text }); }, 300);
    } else {
      send({ type: 'task.submit', content: text });
    }
  }, [connect, send, isConnected]);

  const handleNewSession = useCallback(() => {
    send({ type: 'session.new' });
    setTask('');
    setActiveSessionId('');
    setHistoryItems([]);
    taskSubmittedRef.current = false;
    clearMessages();
  }, [send, clearMessages]);

  const handleLoadSession = useCallback(async (sessionId: string) => {
    try {
      const data = await getSession(sessionId);
      // Convert DB messages to display items for seamless rendering
      const items: Array<{ id: number; type: string; data: unknown }> = [];
      for (let i = 0; i < data.messages.length; i++) {
        const item = dbMsgToDisplayItem(data.messages[i], i);
        if (item) items.push(item);
      }
      setActiveSessionId(sessionId);
      setHistoryItems(items);
      setTask('');
      clearMessages();
    } catch {
      // Silently fail
    }
  }, [clearMessages]);

  const handleStop = useCallback(() => {
    send({ type: 'session.cancel' });
  }, [send]);

  const handleGuardrailApprove = useCallback(() => {
    send({ type: 'guardrail.approve' });
  }, [send]);

  const handleGuardrailReject = useCallback(() => {
    send({ type: 'guardrail.reject' });
  }, [send]);

  // ---- Derived display state ----
  const chatState: AgentState = state === 'idle' && !task ? 'idle' : state;
  const displayTask = historyItems.length > 0 ? '' : task;
  const displayState: AgentState = historyItems.length > 0
    ? (messages.length > 0 ? state : 'idle')
    : chatState;
  const awaitingHuman = state === 'awaiting_human';

  return (
    <PageTransition>
      <div className="agent-page">
        <aside className="agent-page__sidebar agent-page__sidebar--left">
          <HistorySidebar
            key={historyKey}
            activeSessionId={activeSessionId}
            onSelect={handleLoadSession}
            onNewSession={handleNewSession}
          />
        </aside>
        <main className="agent-page__main">
          <ChatView
            messages={messages}
            state={displayState}
            task={displayTask}
            onSend={handleSend}
            onStop={handleStop}
            onNewSession={handleNewSession}
            historyItems={historyItems.length > 0 ? historyItems : undefined}
          />
          {wsError && (
            <div className="agent-page__error-banner">{wsError}</div>
          )}
          {!isConnected && taskSubmittedRef.current && state !== 'completed' && state !== 'error' && (
            <div className="agent-page__connecting">Connecting...</div>
          )}
          {awaitingHuman && (
            <div className="agent-page__awaiting-banner">
              Agent is waiting for your approval.
            </div>
          )}
        </main>
        <aside className="agent-page__sidebar agent-page__sidebar--right">
          <div className="agent-page__sidebar-tabs">
            <button
              className={`agent-page__sidebar-tab ${settingsOpen ? 'agent-page__sidebar-tab--active' : ''}`}
              onClick={() => { setSettingsOpen(!settingsOpen); setFilesOpen(false); }}
              type="button"
            >
              <Settings size={14} /> Settings
            </button>
            <button
              className={`agent-page__sidebar-tab ${filesOpen ? 'agent-page__sidebar-tab--active' : ''}`}
              onClick={() => { setFilesOpen(!filesOpen); setSettingsOpen(false); }}
              type="button"
            >
              <FolderOpen size={14} /> Files
            </button>
          </div>
          {settingsOpen && <SettingsPanel />}
          {filesOpen && (
            <FilePanel
              messages={messages}
              onSend={(msg) => send(msg as { type: string; path?: string })}
              isConnected={isConnected}
            />
          )}
        </aside>
        <GuardrailModal
          guardrail={pendingGuardrail}
          onApprove={handleGuardrailApprove}
          onReject={handleGuardrailReject}
        />
      </div>
    </PageTransition>
  );
};

export default AgentPage;
