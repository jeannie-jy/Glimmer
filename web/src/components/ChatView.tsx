import React from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
import type { Attachment } from './InputBar';
import MessageList from './MessageList';
import InputBar from './InputBar';
import StateIndicator from './StateIndicator';
import { Wand2, Plus } from 'lucide-react';

interface ChatViewProps {
  messages: WsServerMessage[];
  state: AgentState;
  task: string;
  onSend: (text: string, attachments?: Attachment[]) => void;
  onStop: () => void;
  onNewSession: () => void;
  userTasks?: Array<{text: string; files?: Array<{name: string; size: number}>}>;
  historyItems?: Array<{ id: number; type: string; data: unknown }>;
  focusKey?: number;
}

const ChatView: React.FC<ChatViewProps> = ({ messages, state, task, onSend, onStop, onNewSession, userTasks, historyItems, focusKey }) => {
  const isRunning = ['planning', 'executing', 'observing', 'correcting'].includes(state);
  const isAwaiting = state === 'awaiting_human';
  const disabled = isRunning || isAwaiting;

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
      <MessageList messages={messages} task={task} agentState={state} userTasks={userTasks} historyItems={historyItems} />
      <InputBar
        onSend={onSend}
        onStop={onStop}
        disabled={disabled}
        isRunning={isRunning}
        focusKey={focusKey}
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
