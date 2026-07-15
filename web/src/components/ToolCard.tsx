import React, { useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ToolCardProps {
  toolName: string;
  args: Record<string, unknown>;
  exitCode?: number;
  stdout?: string;
  stderr?: string;
  durationMs?: number;
  status: 'invoked' | 'completed';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const ToolCard: React.FC<ToolCardProps> = ({
  toolName,
  args,
  exitCode,
  stdout,
  stderr,
  durationMs,
  status,
}) => {
  const [expanded, setExpanded] = useState(false);

  const isSuccess = exitCode === 0;
  const statusMod =
    status === 'invoked' ? 'invoked' : isSuccess ? 'success' : 'error';

  return (
    <div className={`tool-card ${expanded ? 'tool-card--expanded' : ''}`}>
      <button
        className="tool-card__header"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <span className={`tool-card__icon tool-card__icon--${statusMod}`}>
          {status === 'invoked' ? '▶' : isSuccess ? '✓' : '✗'}
        </span>
        <span className="tool-card__name">{toolName}</span>
        {durationMs !== undefined && (
          <span className="tool-card__duration">
            {(durationMs / 1000).toFixed(1)}s
          </span>
        )}
        <span className={`tool-card__status tool-card__status--${statusMod}`}>
          {status === 'invoked' ? 'Running...' : `Exit ${exitCode}`}
        </span>
        <span className="tool-card__expand">
          {expanded ? '▲' : '▼'}
        </span>
      </button>

      {expanded && (
        <div className="tool-card__body">
          <div className="tool-card__section">
            <div className="tool-card__section-title">Arguments</div>
            <pre className="tool-card__code">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>

          {stdout !== undefined && (
            <div className="tool-card__section">
              <div className="tool-card__section-title">stdout</div>
              <pre className="tool-card__code tool-card__code--stdout">
                {stdout || '(empty)'}
              </pre>
            </div>
          )}

          {stderr !== undefined && stderr && (
            <div className="tool-card__section">
              <div className="tool-card__section-title">stderr</div>
              <pre className="tool-card__code tool-card__code--stderr">
                {stderr}
              </pre>
            </div>
          )}

          {exitCode !== undefined && (
            <div className="tool-card__section">
              <span className="tool-card__meta">
                Exit code: {exitCode}
                {durationMs !== undefined &&
                  ` | Duration: ${(durationMs / 1000).toFixed(2)}s`}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ToolCard;
