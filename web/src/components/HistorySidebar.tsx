import React, { useEffect, useState } from 'react';
import { getSessionHistory } from '../services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface HistorySession {
  id: string;
  task: string;
  state: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const HistorySidebar: React.FC = () => {
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSessionHistory()
      .then((data) => {
        setSessions(data.sessions as HistorySession[]);
      })
      .catch(() => {
        // Silently fail — history is a stub
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="history-sidebar">
      <h2 className="history-sidebar__title">History</h2>

      {loading && (
        <p className="history-sidebar__hint">Loading...</p>
      )}

      {!loading && sessions.length === 0 && (
        <div className="history-sidebar__empty">
          <p className="history-sidebar__hint">
            No previous sessions yet.
          </p>
          <p className="history-sidebar__subhint">
            Session history will appear here once available.
          </p>
        </div>
      )}

      {sessions.length > 0 && (
        <ul className="history-sidebar__list">
          {sessions.map((s) => (
            <li key={s.id} className="history-sidebar__item">
              <span className="history-sidebar__task">{s.task}</span>
              <span className="history-sidebar__state">{s.state}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default HistorySidebar;
