import React, { useEffect, useState } from 'react';
import {
  getConfig,
  updateConfig,
  getCredentialsStatus,
  storeCredential,
  deleteCredential,
  type ConfigData,
  type CredentialsStatus,
} from '../services/api';

const SettingsPanel: React.FC = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [credStatus, setCredStatus] = useState<CredentialsStatus | null>(null);
  const [provider, setProvider] = useState('anthropic');
  const [baseUrl, setBaseUrl] = useState('');
  const [modelId, setModelId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    Promise.all([getConfig(), getCredentialsStatus()])
      .then(([cfg, creds]) => {
        setConfig(cfg);
        setCredStatus(creds);
        setProvider(cfg.model_provider);
        setBaseUrl(cfg.base_url || '');
        setModelId(cfg.model_id);
      })
      .catch((err: Error) => setMessage({ type: 'error', text: err.message }));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      // Save config
      const result = await updateConfig({
        model_provider: provider,
        model_id: modelId,
        base_url: baseUrl,
      });
      setConfig(result.config);

      // Save API key if provided
      if (apiKey.trim()) {
        await storeCredential(provider, apiKey.trim());
        setApiKey('');
        const creds = await getCredentialsStatus();
        setCredStatus(creds);
      }

      setMessage({ type: 'success', text: 'Saved.' });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteKey = async (prov: string) => {
    setMessage(null);
    try {
      await deleteCredential(prov);
      const creds = await getCredentialsStatus();
      setCredStatus(creds);
      setMessage({ type: 'success', text: `Key for ${prov} deleted.` });
    } catch (err: unknown) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to delete key' });
    }
  };

  const showBaseUrl = provider !== 'anthropic';

  return (
    <div className="settings-panel">
      <h2 className="settings-panel__title">Settings</h2>

      {message && (
        <div className={`settings-panel__message settings-panel__message--${message.type}`}>{message.text}</div>
      )}

      <div className="settings-panel__section">
        <label className="settings-panel__label">Provider</label>
        <select className="settings-panel__select" value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="anthropic">Anthropic</option>
          <option value="openai">OpenAI Compatible</option>
        </select>
      </div>

      {showBaseUrl && (
        <div className="settings-panel__section">
          <label className="settings-panel__label">Base URL</label>
          <input className="settings-panel__input" type="text" value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://api.deepseek.com" />
          <p className="settings-panel__hint">支持 OpenAI / DeepSeek / Qwen / Ollama / vLLM 等</p>
        </div>
      )}

      <div className="settings-panel__section">
        <label className="settings-panel__label">Model Name</label>
        <input className="settings-panel__input" type="text" value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          placeholder={provider === 'anthropic' ? 'claude-sonnet-5' : 'deepseek-chat'} />
      </div>

      <div className="settings-panel__divider" />

      <div className="settings-panel__section">
        <label className="settings-panel__label">API Key</label>
        <input className="settings-panel__input" type="password" value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..." />
      </div>

      <button className="settings-panel__btn" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save'}
      </button>

      <div className="settings-panel__divider" />

      <div className="settings-panel__section">
        <label className="settings-panel__label">Stored Keys</label>
        {credStatus ? (
          <ul className="settings-panel__cred-list">
            {Object.entries(credStatus.providers).map(([prov, status]) => (
              <li key={prov} className="settings-panel__cred-item">
                <span className="settings-panel__cred-provider">{prov}</span>
                <span className="settings-panel__cred-status">{status}</span>
                {status.startsWith('configured') && (
                  <button className="settings-panel__cred-delete" onClick={() => handleDeleteKey(prov)} type="button">Delete</button>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="settings-panel__hint">Loading...</p>
        )}
      </div>
    </div>
  );
};

export default SettingsPanel;
