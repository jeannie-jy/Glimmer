# Glimmer

A lightweight, model-agnostic AI coding agent with deterministic guardrails, Docker sandbox isolation, and a fairy-tale themed web UI.

> "每一次编码，都是一场施法" — SpellCraft your code with Glimmer.

---

## Features

- **State-machine-driven agent loop** — deterministic transitions via a pure-function state machine (IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → COMPLETED). No LLM involved in routing decisions.
- **Multi-provider LLM support** — Anthropic (Messages API) + OpenAI-compatible (DeepSeek, Qwen, Ollama, vLLM, etc.). Configurable base URL, model name, and API key per user.
- **Multi-user ready** — GitHub OAuth authentication, JWT middleware, per-user isolated configs with AES-256-GCM encrypted API keys, PostgreSQL persistence.
- **Docker sandbox** — Each agent session runs in an isolated container (`--network none`, 512MB memory limit, 1 CPU). Safe code execution for multi-tenant environments.
- **Three-layer guardrail system** — Layer 1: filesystem path sandbox. Layer 2: command whitelist. Layer 3: regex-based dangerous pattern blacklist. Each layer can ALLOW, BLOCK, or ASK_HUMAN.
- **Deterministic feedback analyzer** — exit-code and structured test-report analysis, not prompt-based. Multi-round self-correction with stuck-loop detection.
- **Fairy-tale Web UI** — React + TypeScript frontend with pink-white dream theme, Great Vibes calligraphic titles, framer-motion animations, Canvas glitter particles, fairy orbit, and live demo chat. Multi-page architecture: Home, About, Guide, Learn, Agent.
- **Real-time streaming** — WebSocket-based streaming token display, tool call cards, guardrail prompts, feedback banners, and settings panel.
- **Docker + docker-compose deployment** — production-ready with Nginx reverse proxy, SSL-ready, rate limiting (slowapi).

---

## Quick Start

### Local single-user mode

```bash
pip install -r requirements.txt
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
# Open http://localhost:8000
```

### Multi-user mode (requires PostgreSQL + Docker)

```bash
export GITHUB_CLIENT_ID=your_github_oauth_client_id
export GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
export GLIMMER_SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=your_db_password
docker-compose up -d
```

---

## Project Structure

```
glimmer/
├── harness/                       # Core library
│   ├── auth/                      #   Authentication
│   │   ├── jwt.py                 #     JWT creation & verification
│   │   ├── oauth.py               #     GitHub OAuth flow
│   │   └── crypto.py              #     AES-256-GCM credential encryption
│   ├── config/                    #   YAML config loading (local mode)
│   │   └── manager.py
│   ├── credentials/               #   API key storage (local mode)
│   │   └── manager.py
│   ├── db/                        #   PostgreSQL models & session
│   │   ├── database.py            #     Async connection pool
│   │   ├── models.py              #     User, UserConfig, Session, Message
│   │   └── migrations/            #     Alembic migrations
│   ├── feedback/                  #   Deterministic feedback analysis
│   │   ├── analyzer.py
│   │   ├── pytest_parser.py
│   │   └── retry_policy.py
│   ├── guardrails/                #   Three-layer safety system
│   │   ├── engine.py
│   │   ├── path_sandbox.py
│   │   ├── whitelist.py
│   │   └── patterns.py
│   ├── llm/                       #   Multi-provider LLM abstraction
│   │   ├── adapter.py             #     ABC for all providers
│   │   ├── anthropic.py           #     Anthropic Messages API
│   │   ├── mock.py                #     Pre-programmed responses (tests)
│   │   └── openai.py              #     OpenAI-compatible (DeepSeek, Qwen, etc.)
│   ├── memory/                    #   Decision & learning persistence
│   │   └── manager.py
│   ├── sandbox/                   #   Docker container management
│   │   └── docker_manager.py      #     Create/exec/destroy per session
│   ├── tools/                     #   Agent tool definitions
│   │   ├── registry.py
│   │   ├── code_search.py
│   │   ├── file_ops.py
│   │   └── shell.py
│   ├── __init__.py
│   ├── loop.py                    #   Main agent event loop
│   ├── models.py                  #   Shared Pydantic data models
│   └── state_machine.py           #   Deterministic state transition table
├── server/                        # FastAPI web server
│   ├── api/                       #   REST routes
│   │   ├── auth_routes.py         #     GitHub OAuth (login, callback, me)
│   │   ├── config_routes.py       #     Per-user config + credentials
│   │   └── session_routes.py      #     Session history CRUD
│   ├── static/                    #   Built frontend assets
│   ├── __init__.py
│   ├── main.py                    #   FastAPI app factory
│   └── ws_handler.py              #   WebSocket session handler (JWT auth)
├── web/                           # React + TypeScript frontend
│   ├── src/
│   │   ├── components/            #   UI components (20 files)
│   │   ├── contexts/              #   AuthContext (JWT state)
│   │   ├── hooks/                 #   useWebSocket, useSession, useGitHubStars
│   │   ├── pages/                 #   Home, About, Guide, Learn, Agent, Login
│   │   ├── services/              #   API client
│   │   └── styles/                #   CSS (magic tokens, animations, page styles)
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── tests/                         # Test suite (94+ tests)
├── docs/                          # Design specs & implementation plans
├── DESIGN.md                      # Fairy-Tale Dream design system reference
├── Dockerfile                     # Multi-stage build (Node + Python)
├── Dockerfile.sandbox             # Agent sandbox image
├── docker-compose.yml             # Production deployment (nginx + api + db)
├── nginx.conf                     # Reverse proxy config
├── pyinstaller.spec               # PyInstaller standalone binary
├── requirements.txt               # Python dependencies
├── .harness/
│   └── config.yaml                # Local-mode configuration
├── LICENSE                        # MIT
└── Makefile                       # Build commands
```

---

## Configuration

### Settings Panel (Web UI)

| Field | Description |
|-------|-------------|
| **Provider** | `Anthropic` or `OpenAI Compatible` |
| **Base URL** | OpenAI-compatible endpoint (e.g. `https://api.deepseek.com`) |
| **Model Name** | Model ID (e.g. `claude-sonnet-5`, `deepseek-chat`, `qwen-plus`) |
| **API Key** | Your API key (encrypted at rest) |

One-click Save stores both config and API key.

### Environment Variables (multi-user deployment)

| Variable | Required | Description |
|----------|----------|-------------|
| `GLIMMER_SECRET_KEY` | Yes | Master key for JWT signing + credential encryption |
| `GITHUB_CLIENT_ID` | Yes | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | Yes | GitHub OAuth App client secret |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OAUTH_REDIRECT_URI` | No | OAuth callback URL (default: `http://localhost:8000/api/auth/callback`) |
| `DOCKER_HOST` | No | Docker daemon socket |
| `SANDBOX_IMAGE` | No | Sandbox image (default: `glimmer-sandbox:latest`) |
| `WORKSPACE_ROOT` | No | User workspace root (default: `/workspace`) |

---

## Supported LLM Providers

| Provider | Base URL | Example Model |
|----------|----------|---------------|
| **Anthropic** | (built-in) | `claude-sonnet-5` |
| **OpenAI** | (built-in) | `gpt-4o` |
| **DeepSeek** | `https://api.deepseek.com` | `deepseek-chat` |
| **Qwen (通义千问)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| **Ollama** | `http://localhost:11434/v1` | `llama3` |
| **vLLM** | (custom) | any |

Any OpenAI-compatible API works — just enter the Base URL.

---

## Testing

```bash
# Full suite (94+ tests)
make test

# Unit tests only (82 tests, zero network)
make test-unit

# Integration tests (12 tests)
make test-integration

# Runnable demos
python tests/demo/demo_guardrail.py
python tests/demo/demo_sandbox.py
python tests/demo/demo_feedback_loop.py
```

---

## Design System

See [DESIGN.md](DESIGN.md) for the complete Fairy-Tale Dream design system:
- Pink-white palette (`#fefaf5` backgrounds, `#f8a4c8` accent)
- Great Vibes + Noto Serif SC + Inter typography
- Canvas glitter particles + framer-motion animations
- Fairy orbit around title with magic wand sparkle effects

---

## License

MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Jingyu Wang
