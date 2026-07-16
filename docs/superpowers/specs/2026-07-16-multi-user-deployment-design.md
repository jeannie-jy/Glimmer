# Glimmer Multi-User Deployment — Design Spec

**Date**: 2026-07-16
**Status**: Approved
**Type**: Server architecture design

---

## 1. Overview

Redesign Glimmer from a single-user localhost tool into a multi-user cloud-deployable platform. Add GitHub OAuth authentication, per-user isolated LLM configs, Docker-based sandboxed agent execution, persistent session storage, rate limiting, and production-ready networking.

### Design Goals

- **Multi-user**: Each user has isolated credentials, configs, and workspace
- **OAuth login**: GitHub login only, no password management
- **Docker sandbox**: Each Agent session runs in an isolated container
- **PostgreSQL**: Persistent storage for users, sessions, messages
- **Production networking**: Nginx reverse proxy, HTTPS, relative API URLs on frontend
- **Rate limiting**: Per-user and per-IP throttling

---

## 2. Architecture

```
┌──────────────────────────────────────────────┐
│                  Browser                      │
│       (React SPA, relative URLs)             │
└──────────────┬───────────────────────────────┘
               │ HTTPS
               ▼
┌──────────────────────────────────────────────┐
│               Nginx (:443)                    │
│  ├── /api/*, /ws/*  →  FastAPI (:8000)       │
│  ├── /*             →  static files          │
│  └── IP rate limiting                        │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│           FastAPI (:8000)                     │
│  ├── OAuth routes  →  GitHub OAuth            │
│  ├── JWT middleware (all /api/*, /ws/*)       │
│  ├── Config routes (per-user)                 │
│  ├── Session routes (CRUD)                    │
│  ├── WebSocket handler (Agent sessions)       │
│  ├── Docker manager (container lifecycle)     │
│  └── Rate limiter (slowapi)                   │
└──────┬───────────────────┬───────────────────┘
       │                   │
       ▼                   ▼
┌──────────────┐  ┌──────────────────┐
│  PostgreSQL  │  │  Docker daemon    │
│  ─────────   │  │  ─────────────   │
│  users       │  │  agent-{sid}     │
│  user_configs│  │  agent-{sid}     │
│  sessions    │  │  agent-{sid}     │
│  messages    │  │  ...             │
└──────────────┘  └──────────────────┘
```

---

## 3. Authentication

### GitHub OAuth Flow

```
1. User clicks [Login with GitHub]
2. Redirect to https://github.com/login/oauth/authorize?client_id=xxx
3. GitHub redirects back to /api/auth/callback?code=xxx
4. Server exchanges code for access_token via POST https://github.com/login/oauth/access_token
5. Server GETs user info from https://api.github.com/user
6. Server creates/updates user row in PostgreSQL
7. Server returns JWT token (expires 7 days)
8. Frontend stores JWT in localStorage, attaches to all API/WS requests
```

### JWT Payload

```json
{
  "sub": "<user-uuid>",
  "name": "username",
  "iat": 1234567890,
  "exp": 1234567890
}
```

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/auth/login` | No | Redirect to GitHub OAuth |
| GET | `/api/auth/callback` | No | OAuth callback, returns JWT |
| GET | `/api/auth/me` | JWT | Current user info |

### Middleware

All `/api/*` and `/ws/*` routes (except auth routes) require valid JWT in `Authorization: Bearer <token>` header. WebSocket attaches token via query param: `ws://host/ws/session?token=<jwt>`.

---

## 4. Data Model (PostgreSQL)

### Users

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id   BIGINT UNIQUE NOT NULL,
    login       VARCHAR(100) NOT NULL,
    name        VARCHAR(200),
    email       VARCHAR(200),
    avatar_url  VARCHAR(500),
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

### User Configs

```sql
CREATE TABLE user_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    provider        VARCHAR(50) NOT NULL DEFAULT 'anthropic',
    base_url        VARCHAR(500) DEFAULT '',
    model_id        VARCHAR(200) NOT NULL DEFAULT 'claude-sonnet-5',
    api_key_enc     TEXT,                          -- AES-256-GCM encrypted
    sandbox_image   VARCHAR(200) DEFAULT 'glimmer-sandbox:latest',
    max_tokens      INTEGER DEFAULT 4096,
    max_retries     INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### Sessions

```sql
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    task            TEXT NOT NULL,
    status          VARCHAR(20) DEFAULT 'running',  -- running / completed / error / cancelled
    container_id    VARCHAR(100),
    retry_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON sessions(user_id, created_at DESC);
```

### Messages

```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES sessions(id) ON DELETE CASCADE,
    type            VARCHAR(20) NOT NULL,           -- user / llm.response / llm.stream / tool.invoke / tool.result / feedback.analysis / session.complete / session.error
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_session ON messages(session_id, created_at);
```

---

## 5. Credential Encryption

API keys are encrypted at rest in PostgreSQL using AES-256-GCM. The encryption key is derived from a server-side secret (`GLIMMER_SECRET_KEY` environment variable) via HKDF.

```python
# Pseudocode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import os

def derive_key(secret: str) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"glimmer-creds").derive(secret.encode())

def encrypt(plaintext: str, secret: str) -> bytes:
    key = derive_key(secret)
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode(), None)
    return nonce + ct

def decrypt(data: bytes, secret: str) -> str:
    key = derive_key(secret)
    return AESGCM(key).decrypt(data[:12], data[12:], None).decode()
```

---

## 6. Docker Sandbox

### Container Lifecycle

```python
class DockerManager:
    async def create(self, user_id: str, session_id: str) -> str:
        """Create and start a sandbox container, return container_id."""
        container = await docker.containers.run(
            image=self.sandbox_image,
            command="sleep infinity",
            name=f"agent-{session_id}",
            network_mode="none",
            mem_limit="512m",
            cpu_limit=1.0,
            pids_limit=100,
            volumes={f"/workspace/{user_id}": {"bind": "/workspace", "mode": "rw"}},
            remove=True,          # --rm
            detach=True,
        )
        return container.id

    async def exec(self, container_id: str, cmd: str, timeout: int = 600) -> ExecResult:
        """Execute a command inside the container."""
        exec_id = await docker.exec_create(container_id, ["sh", "-c", cmd])
        output = await docker.exec_start(exec_id)
        exit_code = await docker.exec_inspect(exec_id)["ExitCode"]
        return ExecResult(exit_code=exit_code, stdout=output)

    async def destroy(self, container_id: str):
        """Stop and remove the container."""
        try:
            container = await docker.containers.get(container_id)
            await container.kill()
        except Exception:
            pass  # Already removed or never created
```

### Sandbox Image

```
FROM python:3.12-slim
RUN pip install pytest pytest-json-report && \
    apt-get update && apt-get install -y ripgrep git && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
CMD ["sleep", "infinity"]
```

### Resource Limits (per container)

| Limit | Value |
|-------|-------|
| Memory | 512 MB |
| CPU | 1 core |
| PIDs | 100 |
| Network | none (--network none) |
| Command timeout | 600s (10 min) |
| Session lifetime | 1800s (30 min) |

---

## 7. Rate Limiting

Using `slowapi` (FastAPI-compatible, backed by Redis or in-memory):

| Scope | Limit | Window |
|-------|-------|--------|
| Auth endpoints | 10 req | 1 minute |
| API endpoints (global) | 60 req | 1 minute per user |
| Agent task submission | 5 req | 1 minute per user |
| WebSocket connections | 3 concurrent | per user |

---

## 8. Frontend Changes

### Relative URLs (critical for deployment)

```typescript
// Before (hardcoded, broken in production):
const WS_URL = 'ws://localhost:8000/ws/session';
const BASE = 'http://localhost:8000';

// After (relative, works everywhere):
const WS_URL = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws/session`;
const BASE = '';  // relative API calls
```

### Login Flow

- Add `AuthContext` — tracks JWT, user info, login state
- Add `LoginPage` — GitHub OAuth button
- Add `ProtectedRoute` — redirect to login if no JWT
- JWT stored in `localStorage`, attached to fetch/WebSocket calls via `Authorization` header or query param

---

## 9. New Server Routes

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/auth/login` | No | Redirect to GitHub |
| GET | `/api/auth/callback` | No | OAuth callback |
| GET | `/api/auth/me` | JWT | Current user info |

### Config (per-user)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/config` | JWT | Get current user's config |
| PUT | `/api/config` | JWT | Update user's config |
| POST | `/api/config/credentials` | JWT | Store API key for user |
| DELETE | `/api/config/credentials` | JWT | Delete stored API key |

### Sessions
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/sessions` | JWT | List user's past sessions |
| GET | `/api/sessions/{id}` | JWT | Get session detail with messages |
| DELETE | `/api/sessions/{id}` | JWT | Delete a session |

### WebSocket
| Path | Auth | Description |
|------|------|-------------|
| `/ws/session` | JWT (query param) | Agent session handler |

---

## 10. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GLIMMER_SECRET_KEY` | Yes | Master key for credential encryption + JWT signing |
| `GITHUB_CLIENT_ID` | Yes | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | Yes | GitHub OAuth App client secret |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `DOCKER_HOST` | No | Docker daemon socket (default: unix:///var/run/docker.sock) |
| `SANDBOX_IMAGE` | No | Docker image for agent sandbox (default: glimmer-sandbox:latest) |
| `WORKSPACE_ROOT` | No | Host path for user workspaces (default: /workspace) |

---

## 11. Deployment (docker-compose)

```yaml
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./server/static:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on: [api]

  api:
    build: .
    environment:
      - GLIMMER_SECRET_KEY=${GLIMMER_SECRET_KEY}
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - DATABASE_URL=postgresql://glimmer:${DB_PASSWORD}@db:5432/glimmer
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - workspace_data:/workspace
    depends_on: [db]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: glimmer
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: glimmer
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
  workspace_data:
```

---

## 12. Implementation Order

1. **Database**: PostgreSQL schema + Alembic migrations + connection pool
2. **Auth**: GitHub OAuth flow + JWT middleware
3. **User Configs**: Per-user config CRUD + encrypted credential storage
4. **Docker Manager**: Container lifecycle (create, exec, destroy)
5. **Refactor AgentLoop**: Use DockerManager instead of local exec
6. **Session Persistence**: Save/load sessions + messages to PostgreSQL
7. **Frontend Auth**: AuthContext + LoginPage + ProtectedRoute + relative URLs
8. **Rate Limiting**: slowapi middleware
9. **Deployment**: docker-compose + nginx config + SSL

---

## 13. Constraints

- No breaking changes to the existing Agent state machine or feedback analyzer
- Frontend retains all current pages and the fairy-tale theme
- Local single-user mode still works (fallback when no DATABASE_URL set)
- Docker daemon required on the host for sandboxed execution
