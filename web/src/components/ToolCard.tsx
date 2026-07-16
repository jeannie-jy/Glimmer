import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Search, FileText, Terminal, FlaskConical } from 'lucide-react';

interface TestFailure { file: string; line?: number; function?: string; message: string; }
interface TestStructured { passed: number; failed: number; errors: number; failures: TestFailure[]; }

interface ToolCardProps {
  toolName: string; args: Record<string, unknown>; exitCode?: number;
  stdout?: string; stderr?: string; durationMs?: number;
  structured?: Record<string, unknown> | null; status: 'invoked' | 'completed';
}

function parseSearchResults(stdout: string): Array<{ file: string; line: string; text: string }> {
  const results: Array<{ file: string; line: string; text: string }> = [];
  for (const line of stdout.split('\n')) {
    const m = line.match(/^(.+?):(\d+):(.*)/);
    if (m) results.push({ file: m[1], line: m[2], text: m[3] });
  }
  return results;
}

const TOOL_ICONS: Record<string, React.ReactNode> = {
  read_file: <FileText size={16} />, write_file: <FileText size={16} />,
  execute_shell: <Terminal size={16} />, run_tests: <FlaskConical size={16} />, search_code: <Search size={16} />,
};
const TOOL_LABELS: Record<string, string> = {
  read_file: 'Read file', write_file: 'Write file', execute_shell: 'Shell',
  run_tests: 'Run tests', search_code: 'Search',
};

const ToolCard: React.FC<ToolCardProps> = ({ toolName, args, exitCode, stdout, stderr, durationMs, structured, status }) => {
  const [expanded, setExpanded] = useState(false);
  const isSuccess = exitCode === 0;
  const statusMod = status === 'invoked' ? 'invoked' : isSuccess ? 'success' : 'error';
  const label = TOOL_LABELS[toolName] || toolName;
  const icon = TOOL_ICONS[toolName] || null;
  const testResults = (structured as TestStructured | null);
  const hasTestResults = testResults && (testResults.passed > 0 || testResults.failed > 0 || testResults.errors > 0);
  const isSearch = toolName === 'search_code';
  const searchResults = isSearch && stdout ? parseSearchResults(stdout) : [];

  return (
    <div className={`tool-card ${expanded ? 'tool-card--expanded' : ''}`}>
      <button className="tool-card__header" onClick={() => setExpanded(!expanded)} type="button">
        <span className={`tool-card__icon tool-card__icon--${statusMod}`}>{status === 'invoked' ? '▶' : isSuccess ? '✓' : '✗'}</span>
        <span className="tool-card__icon-label">{icon}</span>
        <span className="tool-card__name">{label}</span>
        {durationMs !== undefined && <span className="tool-card__duration">{(durationMs / 1000).toFixed(1)}s</span>}
        <span className={`tool-card__status tool-card__status--${statusMod}`}>{status === 'invoked' ? 'Running...' : `Exit ${exitCode}`}</span>
        <span className="tool-card__expand">{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div className="tool-card__body">
          {hasTestResults && (
            <div className="tool-card__test-summary">
              {testResults.passed > 0 && <span className="tool-card__test-badge tool-card__test-badge--pass"><CheckCircle size={14} /> {testResults.passed} passed</span>}
              {testResults.failed > 0 && <span className="tool-card__test-badge tool-card__test-badge--fail"><XCircle size={14} /> {testResults.failed} failed</span>}
              {testResults.errors > 0 && <span className="tool-card__test-badge tool-card__test-badge--error"><AlertTriangle size={14} /> {testResults.errors} errors</span>}
            </div>
          )}
          {testResults?.failures && testResults.failures.length > 0 && (
            <div className="tool-card__section"><div className="tool-card__section-title">Failures</div>
              {testResults.failures.map((f, i) => (
                <div key={i} className="tool-card__failure">
                  <span className="tool-card__failure-loc">{f.file}{f.line ? `:${f.line}` : ''}</span>
                  <span className="tool-card__failure-func">{f.function}</span>
                  <pre className="tool-card__failure-msg">{f.message}</pre>
                </div>
              ))}
            </div>
          )}
          {searchResults.length > 0 && (
            <div className="tool-card__section"><div className="tool-card__section-title">{searchResults.length} match{searchResults.length !== 1 ? 'es' : ''}</div>
              <div className="tool-card__search-results">
                {searchResults.slice(0, 50).map((r, i) => (
                  <div key={i} className="tool-card__search-item"><span className="tool-card__search-loc">{r.file}:{r.line}</span><span className="tool-card__search-text">{r.text}</span></div>
                ))}
                {searchResults.length > 50 && <div className="tool-card__search-more">... and {searchResults.length - 50} more matches</div>}
              </div>
            </div>
          )}
          <div className="tool-card__section"><div className="tool-card__section-title">Arguments</div><pre className="tool-card__code">{JSON.stringify(args, null, 2)}</pre></div>
          {stdout !== undefined && !hasTestResults && !(isSearch && searchResults.length > 0) && (
            <div className="tool-card__section"><div className="tool-card__section-title">stdout</div><pre className="tool-card__code tool-card__code--stdout">{stdout || '(empty)'}</pre></div>
          )}
          {stderr !== undefined && stderr && <div className="tool-card__section"><div className="tool-card__section-title">stderr</div><pre className="tool-card__code tool-card__code--stderr">{stderr}</pre></div>}
          {exitCode !== undefined && <div className="tool-card__section"><span className="tool-card__meta">Exit code: {exitCode}{durationMs !== undefined && ` | Duration: ${(durationMs / 1000).toFixed(2)}s`}</span></div>}
        </div>
      )}
    </div>
  );
};

export default ToolCard;
