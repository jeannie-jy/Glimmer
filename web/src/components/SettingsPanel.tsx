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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const PROVIDERS = ['anthropic', 'openai'];

const SettingsPanel: React.FC = () => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [credStatus, setCredStatus] = useState<CredentialsStatus | null>(null);
  const [provider, setProvider] = useState('anthropic');
  const [modelId, setModelId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // Load config & credential status on mount
  useEffect(() => {
    Promise.all([getConfig(), getCredentialsStatus()])
      .then(([cfg, creds]) => {
        setConfig(cfg);
        setCredStatus(creds);
        setProvider(cfg.model_provider);
        setModelId(cfg.model_id);
      })
      .catch((err: Error) =>
        setMessage({ type: 'error', text: err.message }),
      );
  }, []);

  const handleSaveConfig = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const result = await updateConfig({
        model_provider: provider,
        model_id: modelId,
      });
      setConfig(result.config);
      setMessage({ type: 'success', text: 'Configuration saved.' });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save config';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) return;
    setSaving(true);
    setMessage(null);
    try {
      await storeCredential(provider, apiKey);
      setApiKey('');
      const creds = await getCredentialsStatus();
      setCredStatus(creds);
      setMessage({ type: 'success', text: 'API key saved.' });
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to save API key';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteApiKey = async (prov: string) => {
    setMessage(null);
    try {
      await deleteCredential(prov);
      const creds = await getCredentialsStatus();
      setCredStatus(creds);
      setMessage({ type: 'success', text: `Key for ${prov} deleted.` });
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to delete API key';
      setMessage({ type: 'error', text: msg });
    }
  };

  return (
    <div className="settings-panel">
      <h2 className="settings-panel__title">Settings</h2>

      {message && (
        <div className={`settings-panel__message settings-panel__message--${message.type}`}>
          {message.text}
        </div>
      )}

      {/* ---- Provider & Model ---- */}
      <div className="settings-panel__section">
        <label className="settings-panel__label">Provider</label>
        <select
          className="settings-panel__select"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
        >
          {PROVIDERS.map((p) => (
            <option key={p} value={p}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="settings-panel__section">
        <label className="settings-panel__label">Model ID</label>
        <input
          className="settings-panel__input"
          type="text"
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          placeholder="claude-sonnet-5"
        />
      </div>

      <button
        className="settings-panel__btn"
        onClick={handleSaveConfig}
        disabled={saving}
      >
        {saving ? 'Saving...' : 'Save Config'}
      </button>

      {/* ---- API Key ---- */}
      <div className="settings-panel__divider" />

      <div className="settings-panel__section">
        <label className="settings-panel__label">API Key</label>
        <input
          className="settings-panel__input"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
        />
      </div>

      <button
        className="settings-panel__btn"
        onClick={handleSaveApiKey}
        disabled={saving || !apiKey.trim()}
      >
        {saving ? 'Saving...' : 'Save API Key'}
      </button>

      {/* ---- Credential status ---- */}
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
                  <button
                    className="settings-panel__cred-delete"
                    onClick={() => handleDeleteApiKey(prov)}
                    type="button"
                  >
                    Delete
                  </button>
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
