import React from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StateIndicatorProps {
  state: string;
}

// ---------------------------------------------------------------------------
// State colour mapping
// ---------------------------------------------------------------------------

const STATE_COLORS: Record<string, string> = {
  idle: '#8b949e',
  planning: '#58a6ff',
  executing: '#d29922',
  observing: '#f0883e',
  correcting: '#f85149',
  awaiting_human: '#bc8cff',
  completed: '#3fb950',
  error: '#f85149',
};

const STATE_LABELS: Record<string, string> = {
  idle: 'Idle',
  planning: 'Planning',
  executing: 'Executing',
  observing: 'Observing',
  correcting: 'Correcting',
  awaiting_human: 'Awaiting Human',
  completed: 'Completed',
  error: 'Error',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const StateIndicator: React.FC<StateIndicatorProps> = ({ state }) => {
  const color = STATE_COLORS[state] || '#8b949e';
  const label = STATE_LABELS[state] || state;

  return (
    <div className="state-indicator">
      <span
        className="state-indicator__dot"
        style={{ backgroundColor: color }}
      />
      <span className="state-indicator__label">{label}</span>
    </div>
  );
};

export default StateIndicator;
