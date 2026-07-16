import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, X, Send, AlertTriangle } from 'lucide-react';

const MAX_FILE_SIZE = 95 * 1024;

export interface Attachment { name: string; size: number; contentB64: string; }

interface InputBarProps {
  onSend: (text: string, attachments?: Attachment[]) => void; onStop: () => void;
  disabled: boolean; isRunning: boolean; placeholder?: string; focusKey?: number;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => { const result = reader.result as string; const idx = result.indexOf('base64,'); resolve(idx >= 0 ? result.substring(idx + 7) : result); };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

const InputBar: React.FC<InputBarProps> = ({ onSend, onStop, disabled, isRunning, placeholder, focusKey }) => {
  const [text, setText] = useState(''); const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false); const [sizeError, setSizeError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null); const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (focusKey !== undefined && focusKey > 0) textareaRef.current?.focus(); }, [focusKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); const trimmed = text.trim();
    if (!trimmed && files.length === 0) return;
    if (uploading || disabled) return;
    const attachments: Attachment[] = [];
    if (files.length > 0) { setUploading(true);
      for (const file of files) { try { attachments.push({ name: file.name, size: file.size, contentB64: await readFileAsBase64(file) }); } catch {} }
      setUploading(false); setFiles([]);
    }
    onSend(trimmed || 'Please analyze the attached files', attachments.length > 0 ? attachments : undefined); setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); } };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);
    const oversized = selected.filter(f => f.size > MAX_FILE_SIZE);
    if (oversized.length > 0) { const names = oversized.map(f => `${f.name} (${(f.size/1024).toFixed(0)}KB)`).join(', '); setSizeError(`${names} exceed${oversized.length>1?'':'s'} 95KB limit`); setTimeout(() => setSizeError(null), 4000); }
    setFiles(prev => [...prev, ...selected.filter(f => f.size <= MAX_FILE_SIZE)]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (idx: number) => { setFiles(prev => prev.filter((_, i) => i !== idx)); };

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      {files.length > 0 && (<div className="input-bar__chips">{files.map((f, i) => (
        <span key={i} className="input-bar__chip"><span className="input-bar__chip-icon">📄</span><span className="input-bar__chip-name">{f.name}</span><span className="input-bar__chip-size">{formatSize(f.size)}</span><button className="input-bar__chip-close" onClick={() => removeFile(i)} type="button"><X size={12} /></button></span>
      ))}</div>)}
      {sizeError && (<div className="input-bar__size-error"><AlertTriangle size={14} /> {sizeError}</div>)}
      <div className="input-bar__container">
        <button className="input-bar__attach-btn" onClick={() => fileInputRef.current?.click()} disabled={disabled} title="Attach files" type="button"><Paperclip size={18} /></button>
        <input ref={fileInputRef} type="file" multiple onChange={handleFileSelect} style={{ display: 'none' }} accept=".py,.c,.cpp,.h,.java,.js,.ts,.jsx,.tsx,.css,.html,.json,.yaml,.yml,.md,.txt,.csv,.sh,.sql,.rs,.go,.rb,.php,.zip,.tar.gz,.tgz" />
        <textarea ref={textareaRef} className="input-bar__textarea" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={handleKeyDown} placeholder={placeholder || 'Enter a task for the agent...'} disabled={disabled || uploading} rows={2} />
        <div className="input-bar__actions">
          {isRunning ? (<button type="button" className="input-bar__btn input-bar__btn--stop" onClick={onStop}>Stop</button>) : (<button type="submit" className="input-bar__btn input-bar__btn--send" disabled={disabled || uploading || (!text.trim() && files.length === 0)}><Send size={16} /></button>)}
        </div>
      </div>
    </form>
  );
};

export default InputBar;
