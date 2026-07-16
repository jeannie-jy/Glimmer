import React, { useState, useCallback, useEffect } from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import { File, Folder, Download, Eye, RefreshCw } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FileInfo {
  name: string;
  size: number;
  modified: string;
}

interface FilePanelProps {
  messages: WsServerMessage[];
  /** Callback to send a WebSocket message (for download requests) */
  onSend: (msg: { type: string; path?: string }) => void;
  /** Active session ID for sync */
  isConnected: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getLang(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || '';
  const map: Record<string, string> = {
    py: 'py', js: 'js', ts: 'ts', tsx: 'tsx', jsx: 'jsx',
    css: 'css', html: 'html', json: 'json', yaml: 'yaml', yml: 'yaml',
    md: 'md', txt: 'txt', sh: 'sh', sql: 'sql', rs: 'rs', go: 'go',
    java: 'java', c: 'c', cpp: 'cpp', h: 'c', rb: 'rb', php: 'php',
  };
  return map[ext] || 'txt';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const FilePanel: React.FC<FilePanelProps> = ({ messages, onSend, isConnected }) => {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [previewContent, setPreviewContent] = useState<string>('');
  const [previewPath, setPreviewPath] = useState<string>('');

  // Derive file list from file.created / file.modified events
  useEffect(() => {
    let changed = false;
    const next = [...files];
    for (const msg of messages) {
      if (msg.type === 'file.created') {
        const exists = next.find(f => f.name === msg.path);
        if (!exists) {
          next.push({ name: msg.path, size: 0, modified: '' });
          changed = true;
        }
      } else if (msg.type === 'file.modified') {
        const f = next.find(f => f.name === msg.path);
        if (!f) {
          next.push({ name: msg.path, size: 0, modified: '' });
        }
        changed = true;
      } else if (msg.type === 'files.list') {
        // Full sync from server
        setFiles(msg.files as FileInfo[]);
        return;
      }
    }
    if (changed) setFiles(next);
  }, [messages]); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for files.content responses (from download requests)
  useEffect(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      if (msg.type === 'files.content' && msg.path === previewPath && msg.content) {
        setPreviewContent(msg.content);
        break;
      }
    }
  }, [messages, previewPath]);

  // Request full file list from server when connected
  useEffect(() => {
    if (isConnected) {
      onSend({ type: 'files.list' });
    }
  }, [isConnected]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRefresh = useCallback(() => {
    onSend({ type: 'files.list' });
  }, [onSend]);

  const handleDownload = useCallback((path: string) => {
    // Trigger download via WebSocket → server reads file → sends files.content
    setPreviewPath(path);
    onSend({ type: 'files.download', path });
  }, [onSend]);

  const handlePreview = useCallback((path: string) => {
    setPreviewPath(path);
    setPreviewFile(path);
    onSend({ type: 'files.download', path });
  }, [onSend]);

  // Actual download to browser
  const triggerBrowserDownload = useCallback((filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename.split('/').pop() || filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  // When a files.content arrives for download, trigger browser download
  useEffect(() => {
    if (previewPath && previewContent && !previewFile) {
      triggerBrowserDownload(previewPath, previewContent);
      setPreviewPath('');
      setPreviewContent('');
    }
  }, [previewPath, previewContent, previewFile, triggerBrowserDownload]);

  // Group files by directory
  const grouped: Record<string, FileInfo[]> = {};
  for (const f of files) {
    const dir = f.name.includes('/') ? f.name.substring(0, f.name.lastIndexOf('/')) : '';
    if (!grouped[dir]) grouped[dir] = [];
    grouped[dir].push(f);
  }

  return (
    <div className="file-panel">
      <div className="file-panel__header">
        <h3 className="file-panel__title">Files</h3>
        <button className="file-panel__refresh" onClick={handleRefresh} title="Refresh" type="button">
          <RefreshCw size={14} />
        </button>
      </div>

      {files.length === 0 && (
        <p className="file-panel__empty">
          No files yet. Ask the agent to create or modify files.
        </p>
      )}

      <div className="file-panel__list">
        {Object.entries(grouped).map(([dir, dirFiles]) => (
          <div key={dir || '__root'} className="file-panel__group">
            {dir && <div className="file-panel__dir"><Folder size={12} /> {dir}</div>}
            {dirFiles.map((f) => (
              <div key={f.name} className="file-panel__item">
                <span className="file-panel__item-name" title={f.name}>
                  <File size={12} />
                  <span>{dir ? f.name.split('/').pop() : f.name}</span>
                </span>
                <span className="file-panel__item-size">{formatSize(f.size)}</span>
                <span className="file-panel__item-actions">
                  <button
                    className="file-panel__action"
                    onClick={() => handlePreview(f.name)}
                    title="Preview"
                    type="button"
                  >
                    <Eye size={12} />
                  </button>
                  <button
                    className="file-panel__action"
                    onClick={() => handleDownload(f.name)}
                    title="Download"
                    type="button"
                  >
                    <Download size={12} />
                  </button>
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Preview modal */}
      {previewFile && (
        <div className="file-panel__preview-overlay" onClick={() => setPreviewFile(null)}>
          <div className="file-panel__preview" onClick={(e) => e.stopPropagation()}>
            <div className="file-panel__preview-header">
              <span className="file-panel__preview-path">{previewFile}</span>
              <span className="file-panel__preview-lang">{getLang(previewFile)}</span>
              <button
                className="file-panel__preview-download"
                onClick={() => {
                  triggerBrowserDownload(previewFile, previewContent);
                  setPreviewFile(null);
                }}
                type="button"
              >
                <Download size={14} /> Download
              </button>
              <button className="file-panel__preview-close" onClick={() => setPreviewFile(null)} type="button">✕</button>
            </div>
            <pre className="file-panel__preview-code">
              <code>{previewContent || 'Loading...'}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilePanel;
