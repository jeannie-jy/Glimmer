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
// Verdict labels
// ---------------------------------------------------------------------------

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
  const verdictKey =
    ['pass', 'fail', 'warning'].includes(verdict.toLowerCase())
      ? verdict.toLowerCase()
      : 'unknown';
  const label = VERDICT_LABELS[verdictKey] || 'UNKNOWN';
  const hasDetails = failures.length > 0 || suggestedFix;

  return (
    <div className={`feedback-banner feedback-banner--${verdictKey}`}>
      <button
        className="feedback-banner__header"
        onClick={() => setExpanded(!expanded)}
        type="button"
        style={{ cursor: hasDetails ? 'pointer' : 'default' }}
      >
        <span className={`feedback-banner__verdict feedback-banner__verdict--${verdictKey}`}>
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
