/** REST API client for the Glimmer backend. */

const BASE = '';

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('glimmer_token');
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

export interface ConfigData {
  model_provider: string;
  model_id: string;
  base_url: string;
  max_tokens: number;
  max_retries: number;
  sandbox_root: string;
  command_whitelist_extra: string[];
  timeout_seconds: number;
  enabled_tools: string[];
  max_context_tokens: number;
  learnings_limit: number;
}

export interface CredentialsStatus {
  providers: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

export async function getConfig(): Promise<ConfigData> {
  const res = await fetch(`${BASE}/api/config`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`GET /api/config failed: ${res.status}`);
  return res.json();
}

export async function updateConfig(
  updates: Partial<ConfigData>,
): Promise<{ status: string; config: ConfigData }> {
  const res = await fetch(`${BASE}/api/config`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`PUT /api/config failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Credentials
// ---------------------------------------------------------------------------

export async function getCredentialsStatus(): Promise<CredentialsStatus> {
  const res = await fetch(`${BASE}/api/credentials/status`, { headers: authHeaders() });
  if (!res.ok)
    throw new Error(`GET /api/credentials/status failed: ${res.status}`);
  return res.json();
}

export async function storeCredential(
  provider: string,
  apiKey: string,
): Promise<void> {
  const res = await fetch(`${BASE}/api/credentials`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ provider, api_key: apiKey }),
  });
  if (!res.ok) throw new Error(`POST /api/credentials failed: ${res.status}`);
}

export async function deleteCredential(provider: string): Promise<void> {
  const res = await fetch(`${BASE}/api/credentials/${provider}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok)
    throw new Error(`DELETE /api/credentials/${provider} failed: ${res.status}`);
}

// ---------------------------------------------------------------------------
// Session history
// ---------------------------------------------------------------------------

export async function getSessionHistory(): Promise<{ sessions: unknown[] }> {
  const res = await fetch(`${BASE}/api/session/history`, { headers: authHeaders() });
  if (!res.ok)
    throw new Error(`GET /api/session/history failed: ${res.status}`);
  return res.json();
}
