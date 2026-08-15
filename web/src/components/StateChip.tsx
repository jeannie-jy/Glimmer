import React from 'react';
import { Sparkles, Wrench, Eye, RefreshCw, Hourglass, CheckCircle2, AlertTriangle, Wand2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Fairy-tale themed state labels
// ---------------------------------------------------------------------------

const STATE_LABELS: Record<string, { active: string; completed: string }> = {
  planning:        { active: 'Casting a spell...',       completed: 'Spell cast' },
  executing:       { active: 'Working magic...',         completed: 'Executed' },
  observing:       { active: 'Checking results...',      completed: 'Results checked' },
  correcting:      { active: 'Refining the spell...',    completed: 'Spell refined' },
  awaiting_human:  { active: 'Awaiting your approval',   completed: 'Approved' },
  completed:       { active: '',                         completed: 'Quest complete!' },
  error:           { active: 'Something went wrong',     completed: 'Error' },
  idle:            { active: '',                         completed: 'Ready to cast' },
};

const STATE_ICONS: Record<string, React.ComponentType<{ size?: number | string; className?: string }>> = {
  planning:       Sparkles,
  executing:      Wrench,
  observing:      Eye,
  correcting:     RefreshCw,
  awaiting_human: Hourglass,
  completed:      CheckCircle2,
  error:          AlertTriangle,
  idle:           Wand2,
};

const STATE_DOT_COLORS: Record<string, string> = {
  planning:       'var(--color-accent)',
  executing:      '#e6a817',
  observing:      '#f08a4b',
  correcting:     '#e066a0',
  awaiting_human: '#f06292',
  completed:      '#4caf50',
  error:          '#ef5350',
  idle:           '#9e9e9e',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface StateChipProps {
  state: string;
  toolName?: string;
  isActive: boolean;
}

const StateChip: React.FC<StateChipProps> = ({ state, toolName, isActive }) => {
  const labels = STATE_LABELS[state];
  if (!labels) return null;

  const label = isActive ? labels.active : labels.completed;
  if (!label) return null;

  // Append tool name to executing label when available
  const displayLabel =
    state === 'executing' && toolName
      ? labels.active.replace('{tool}', toolName)
      : label;

  const dotColor = STATE_DOT_COLORS[state] || 'var(--color-text-secondary)';
  const StateIcon = STATE_ICONS[state];

  return (
    <div className={`state-chip ${isActive ? 'state-chip--active' : ''}`}>
      <span
        className="state-chip__dot"
        style={{ backgroundColor: dotColor }}
      />
      {StateIcon && <StateIcon size={12} className="state-chip__icon" />}
      <span className="state-chip__text">{displayLabel}</span>
    </div>
  );
};

export default StateChip;
