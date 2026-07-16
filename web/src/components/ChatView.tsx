import React from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
import MessageList from './MessageList';
import InputBar from './InputBar';
import StateIndicator from './StateIndicator';
import { Wand2 } from 'lucide-react';

interface ChatViewProps {
  messages: WsServerMessage[];
  state: AgentState;
  onSend: (text: string) => void;
  onStop: () => void;
}

const ChatView: React.FC<ChatViewProps> = ({ messages, state, onSend, onStop }) => {
  const isRunning = ['planning', 'executing', 'observing', 'correcting'].includes(state);
  const isAwaiting = state === 'awaiting_human';
  const disabled = isRunning || isAwaiting || state === 'completed';

  return (
    <div className="chat-view">
      <div className="chat-view__header">
        <h1 className="chat-view__title"><Wand2 size={22} /> Agent — 代码魔法</h1>
        <StateIndicator state={state} />
      </div>
      <MessageList messages={messages} />
      <InputBar
        onSend={onSend} onStop={onStop} disabled={disabled} isRunning={isRunning}
        placeholder={isAwaiting ? 'Awaiting human approval...' : isRunning ? 'Agent is casting spells...' : 'Describe your task — the agent will cast a spell...'}
      />
    </div>
  );
};

export default ChatView;
