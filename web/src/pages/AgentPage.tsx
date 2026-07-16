import React, { useState, useCallback, useRef } from 'react';
import PageTransition from '../components/PageTransition';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSession, type AgentState } from '../hooks/useSession';
import ChatView from '../components/ChatView';
import HistorySidebar from '../components/HistorySidebar';
import SettingsPanel from '../components/SettingsPanel';
import GuardrailModal from '../components/GuardrailModal';
import '../styles/agent.css';
import { Settings } from 'lucide-react';

const AgentPage: React.FC = () => {
  const { send, messages, isConnected, connect, disconnect, error: wsError } = useWebSocket();
  const [task, setTask] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const taskSubmittedRef = useRef(false);
  const { state, pendingGuardrail } = useSession(messages, task);

  const handleSend = useCallback((text: string) => {
    setTask(text); taskSubmittedRef.current = true; connect();
    setTimeout(() => { send({ type: 'task.submit', content: text }); }, 200);
  }, [connect, send]);

  const handleStop = useCallback(() => { send({ type: 'session.cancel' }); disconnect(); }, [send, disconnect]);
  const handleGuardrailApprove = useCallback(() => { send({ type: 'guardrail.approve' }); }, [send]);
  const handleGuardrailReject = useCallback(() => { send({ type: 'guardrail.reject' }); }, [send]);

  const chatState: AgentState = state === 'idle' && !task ? 'idle' : state;
  const awaitingHuman = state === 'awaiting_human';

  return (
    <PageTransition>
      <div className="agent-page">
        <aside className="agent-page__sidebar agent-page__sidebar--left"><HistorySidebar /></aside>
        <main className="agent-page__main">
          <ChatView messages={messages} state={chatState} onSend={handleSend} onStop={handleStop} />
          {wsError && <div className="agent-page__error-banner">{wsError}</div>}
          {!isConnected && taskSubmittedRef.current && state !== 'completed' && state !== 'error' && <div className="agent-page__connecting">Connecting...</div>}
          {awaitingHuman && <div className="agent-page__awaiting-banner">Agent is waiting for your approval.</div>}
        </main>
        <aside className="agent-page__sidebar agent-page__sidebar--right">
          <button className="agent-page__settings-toggle" onClick={() => setSettingsOpen(!settingsOpen)} type="button">{settingsOpen ? 'Close Settings' : <><Settings size={16} /> Settings</>}</button>
          {settingsOpen && <SettingsPanel />}
        </aside>
        <GuardrailModal guardrail={pendingGuardrail} onApprove={handleGuardrailApprove} onReject={handleGuardrailReject} />
      </div>
    </PageTransition>
  );
};

export default AgentPage;
