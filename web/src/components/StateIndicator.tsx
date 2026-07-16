import React from 'react';

interface StateIndicatorProps { state: string; }

const STATE_LABELS: Record<string, string> = {
  idle: 'Idle', planning: 'Planning', executing: 'Executing', observing: 'Observing',
  correcting: 'Correcting', awaiting_human: 'Awaiting Human', completed: 'Completed', error: 'Error',
};

const StateIndicator: React.FC<StateIndicatorProps> = ({ state }) => {
  const label = STATE_LABELS[state] || state;
  return (
    <div className="state-indicator">
      <span className={`state-indicator__orb state-indicator__orb--${state}`} />
      <span className="state-indicator__label">{label}</span>
    </div>
  );
};

export default StateIndicator;
