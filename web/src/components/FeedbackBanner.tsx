import React, { useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Failure {
  file: string;
  line?: number;
  function?: string;
  message: string;
}

interface FeedbackBannerProps {
  verdict: string;
  summary: string;
  failures?: Failure[];
  suggestedFix?: string;
  retryCount: number;
}

// ---------------------------------------------------------------------------
// Verdict colour mapping
// ---------------------------------------------------------------------------

const VERDICT_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  pass: { bg: '#0d2818', border: '#3fb950', text: '#3fb950' },
  fail: { bg: '#2d0a0a', border: '#f85149', text: '#f85149' },
  warning: { bg: '#2d1f00', border: '#d29922', text: '#d29922' },
  unknown: { bg: '#161b22', border: '#8b949e', text: '#8b949e' },
};

const VERDICT_LABELS: Record<string, string> = {
  pass: 'PASS',
  fail: 'FAIL',
  warning: 'WARNING',
  unknown: 'UNKNOWN',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const FeedbackBanner: React.FC<FeedbackBannerProps> = ({
  verdict,
  summary,
  failures = [],
  suggestedFix,
  retryCount,
}) => {
  const [expanded, setExpanded] = useState(false);
  const colors = VERDICT_COLORS[verdict.toLowerCase()] || VERDICT_COLORS.unknown;
  const label = VERDICT_LABELS[verdict.toLowerCase()] || 'UNKNOWN';
  const hasDetails = failures.length > 0 || suggestedFix;

  return (
    <div
      className="feedback-banner"
      style={{
        borderLeftColor: colors.border,
        backgroundColor: colors.bg,
      }}
    >
      <button
        className="feedback-banner__header"
        onClick={() => setExpanded(!expanded)}
        type="button"
        style={{ cursor: hasDetails ? 'pointer' : 'default' }}
      >
        <span
          className="feedback-banner__verdict"
          style={{ color: colors.text }}
        >
          {label}
        </span>
        <span className="feedback-banner__summary">{summary}</span>
        <span className="feedback-banner__retry">
          Retry #{retryCount}
        </span>
        {hasDetails && (
          <span className="feedback-banner__expand">
            {expanded ? '▲' : '▼'}
          </span>
        )}
      </button>

      {expanded && hasDetails && (
        <div className="feedback-banner__body">
          {failures.length > 0 && (
            <div className="feedback-banner__failures">
              <div className="feedback-banner__section-title">Failures</div>
              {failures.map((f, i) => (
                <div key={i} className="feedback-banner__failure">
                  <span className="feedback-banner__failure-location">
                    {f.file}
                    {f.line !== undefined && `:${f.line}`}
                    {f.function && ` in ${f.function}`}
                  </span>
                  <p className="feedback-banner__failure-message">
                    {f.message}
                  </p>
                </div>
              ))}
            </div>
          )}

          {suggestedFix && (
            <div className="feedback-banner__fix">
              <div className="feedback-banner__section-title">
                Suggested Fix
              </div>
              <pre className="feedback-banner__code">{suggestedFix}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FeedbackBanner;
