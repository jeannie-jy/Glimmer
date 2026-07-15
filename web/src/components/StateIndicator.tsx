import React from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StateIndicatorProps {
  state: string;
}

// ---------------------------------------------------------------------------
// State labels
// ---------------------------------------------------------------------------

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
  const label = STATE_LABELS[state] || state;

  return (
    <div className="state-indicator">
      <span className={`state-indicator__dot state-indicator__dot--${state}`} />
      <span className="state-indicator__label">{label}</span>
    </div>
  );
};

export default StateIndicator;
