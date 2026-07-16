import React from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
import MessageList from './MessageList';
import InputBar from './InputBar';
import StateIndicator from './StateIndicator';
import { Wand2, Plus } from 'lucide-react';

interface ChatViewProps {
  messages: WsServerMessage[];
  state: AgentState;
  task: string;
  onSend: (text: string) => void;
  onStop: () => void;
  onNewSession: () => void;
  historyItems?: Array<{ id: number; type: string; data: unknown }>;
}

const ChatView: React.FC<ChatViewProps> = ({ messages, state, task, onSend, onStop, onNewSession, historyItems }) => {
  const isRunning = ['planning', 'executing', 'observing', 'correcting'].includes(state);
  const isAwaiting = state === 'awaiting_human';
  const isViewingHistory = historyItems && historyItems.length > 0;
  const disabled = isRunning || isAwaiting || isViewingHistory;

  return (
    <div className="chat-view">
      <div className="chat-view__header">
        <h1 className="chat-view__title"><Wand2 size={22} /> Agent — 代码魔法</h1>
        <div className="chat-view__header-actions">
          <StateIndicator state={state} />
          <button
            className="chat-view__new-btn"
            onClick={onNewSession}
            title="New session"
            type="button"
          >
            <Plus size={18} />
          </button>
        </div>
      </div>
      <MessageList messages={messages} task={task} agentState={state} historyItems={historyItems} />
      <InputBar
        onSend={onSend}
        onStop={onStop}
        disabled={disabled}
        isRunning={isRunning}
        placeholder={
          isAwaiting
            ? 'Awaiting human approval...'
            : isRunning
              ? 'Agent is casting spells...'
              : 'Describe your task — the agent will cast a spell...'
        }
      />
    </div>
  );
};

export default ChatView;
