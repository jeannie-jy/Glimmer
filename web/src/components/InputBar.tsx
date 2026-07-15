import React, { useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface InputBarProps {
  onSend: (text: string) => void;
  onStop: () => void;
  disabled: boolean;
  isRunning: boolean;
  placeholder?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const InputBar: React.FC<InputBarProps> = ({
  onSend,
  onStop,
  disabled,
  isRunning,
  placeholder = 'Enter a task for the agent...',
}) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <div className="input-bar__container">
        <textarea
          className="input-bar__textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled && !isRunning}
          rows={2}
        />
        <div className="input-bar__actions">
          {isRunning ? (
            <button
              type="button"
              className="input-bar__btn input-bar__btn--stop"
              onClick={onStop}
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="input-bar__btn input-bar__btn--send"
              disabled={disabled || !text.trim()}
            >
              Send
            </button>
          )}
        </div>
      </div>
    </form>
  );
};

export default InputBar;
