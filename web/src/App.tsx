import React, { useState, useCallback, useRef } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useSession, type AgentState } from './hooks/useSession';
import ChatView from './components/ChatView';
import HistorySidebar from './components/HistorySidebar';
import SettingsPanel from './components/SettingsPanel';
import GuardrailModal from './components/GuardrailModal';
import './App.css';

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

const App: React.FC = () => {
  const {
    send,
    messages,
    isConnected,
    connect,
    disconnect,
    error: wsError,
  } = useWebSocket();

  const [task, setTask] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const taskSubmittedRef = useRef(false);

  const { state, pendingGuardrail } = useSession(messages, task);

  const isRunning = ['planning', 'executing', 'observing', 'correcting'].includes(state);

  // ---- Send task ----
  const handleSend = useCallback(
    (text: string) => {
      setTask(text);
      taskSubmittedRef.current = true;
      connect();
      // Small delay to let the connection open
      setTimeout(() => {
        send({ type: 'task.submit', content: text });
      }, 200);
    },
    [connect, send],
  );

  // ---- Cancel session ----
  const handleStop = useCallback(() => {
    send({ type: 'session.cancel' });
    disconnect();
  }, [send, disconnect]);

  // ---- Guardrail actions ----
  const handleGuardrailApprove = useCallback(() => {
    send({ type: 'guardrail.approve' });
  }, [send]);

  const handleGuardrailReject = useCallback(() => {
    send({ type: 'guardrail.reject' });
  }, [send]);

  // ---- Determine state for ChatView ----
  const chatState: AgentState =
    state === 'idle' && !task
      ? 'idle'
      : state;

  // ---- Connected / awaiting status for UI ----
  const awaitingHuman = state === 'awaiting_human';

  return (
    <div className="app">
      {/* Left sidebar — History */}
      <aside className="app__sidebar app__sidebar--left">
        <HistorySidebar />
      </aside>

      {/* Main — Chat */}
      <main className="app__main">
        <ChatView
          messages={messages}
          state={chatState}
          onSend={handleSend}
          onStop={handleStop}
        />

        {/* WebSocket error banner */}
        {wsError && (
          <div className="app__error-banner">{wsError}</div>
        )}

        {/* Connection status */}
        {!isConnected && taskSubmittedRef.current && state !== 'completed' && state !== 'error' && (
          <div className="app__connecting">
            Connecting...
          </div>
        )}

        {/* Awaiting human indicator */}
        {awaitingHuman && (
          <div className="app__awaiting-banner">
            Agent is waiting for your approval.
          </div>
        )}
      </main>

      {/* Right sidebar — Settings toggle / panel */}
      <aside className="app__sidebar app__sidebar--right">
        <button
          className="app__settings-toggle"
          onClick={() => setSettingsOpen(!settingsOpen)}
          type="button"
        >
          {settingsOpen ? 'Close Settings' : 'Settings'}
        </button>
        {settingsOpen && <SettingsPanel />}
      </aside>

      {/* Guardrail modal */}
      <GuardrailModal
        guardrail={pendingGuardrail}
        onApprove={handleGuardrailApprove}
        onReject={handleGuardrailReject}
      />
    </div>
  );
};

export default App;
