import React, { useEffect, useState } from 'react';
import { getSessionHistory } from '../services/api';
import { Plus, Trash2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface HistorySession {
  id: string;
  task: string;
  state: string;
  status: string;
  created_at: string;
  finished_at?: string | null;
}

interface HistorySidebarProps {
  activeSessionId: string;
  onSelect: (id: string) => void;
  onNewSession: () => void;
  onDelete: (id: string) => Promise<void>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return d.toLocaleDateString();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const HistorySidebar: React.FC<HistorySidebarProps> = ({
  activeSessionId,
  onSelect,
  onNewSession,
  onDelete,
}) => {
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState('');

  useEffect(() => {
    getSessionHistory()
      .then((data) => {
        setSessions(data.sessions as HistorySession[]);
      })
      .catch(() => {
        // Silently fail
      })
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    setDeletingId(id);
    try {
      await onDelete(id);
      setSessions(prev => prev.filter(s => s.id !== id));
    } catch {
      window.alert('Failed to delete conversation.');
    } finally {
      setDeletingId('');
    }
  };

  return (
    <div className="history-sidebar">
      <div className="history-sidebar__header">
        <h2 className="history-sidebar__title">History</h2>
        <button
          className="history-sidebar__new-btn"
          onClick={onNewSession}
          title="New session"
          type="button"
        >
          <Plus size={16} />
        </button>
      </div>

      {loading && (
        <p className="history-sidebar__hint">Loading...</p>
      )}

      {!loading && sessions.length === 0 && (
        <div className="history-sidebar__empty">
          <p className="history-sidebar__hint">
            No previous sessions yet.
          </p>
          <p className="history-sidebar__subhint">
            Your conversations will appear here.
          </p>
        </div>
      )}

      {sessions.length > 0 && (
        <ul className="history-sidebar__list">
          {sessions.map((s) => (
            <li
              key={s.id}
              className={`history-sidebar__item ${
                s.id === activeSessionId ? 'history-sidebar__item--active' : ''
              }`}
              onClick={() => onSelect(s.id)}
            >
              <span className="history-sidebar__task-row">
                <span className="history-sidebar__task">{s.task || 'Untitled session'}</span>
                <button
                  className="history-sidebar__delete-btn"
                  onClick={(e) => handleDelete(e, s.id)}
                  disabled={deletingId === s.id}
                  title="Delete conversation"
                  aria-label="Delete conversation"
                  type="button"
                >
                  <Trash2 size={14} />
                </button>
              </span>
              <span className="history-sidebar__meta">
                <span className="history-sidebar__state">{s.status || s.state || 'unknown'}</span>
                <span className="history-sidebar__time">{formatDate(s.finished_at || s.created_at)}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default HistorySidebar;
