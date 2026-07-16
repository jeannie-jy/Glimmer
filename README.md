[English](README.md) | [中文](README.zh.md)

---

# Glimmer

A lightweight, model-agnostic coding agent harness with deterministic guardrails and mock-driven testing.

Built from scratch as a final project for the AI4SE course, this harness demonstrates a complete agent loop with state-machine-driven execution, multi-provider LLM support, a three-layer guardrail system, deterministic feedback analysis with multi-round self-correction, and a real-time web UI.

---

## Features

- **State-machine-driven agent loop** -- deterministic transitions via a pure-function state machine (IDLE -> PLANNING -> EXECUTING -> OBSERVING -> CORRECTING -> COMPLETED). No LLM is involved in routing decisions.
- **Multi-provider LLM support** -- pluggable adapters for Anthropic (Messages API) and OpenAI (Chat Completions API), plus a Mock adapter for zero-network testing.
- **Three-layer guardrail system** -- Layer 1: filesystem path sandbox. Layer 2: command whitelist. Layer 3: regex-based dangerous pattern blacklist. Each layer can ALLOW, BLOCK, or ASK_HUMAN.
- **Deterministic feedback analyzer** -- exit-code and structured test-report analysis, not prompt-based. Works identically with or without an LLM. Multi-round self-correction via a retry policy that detects stuck loops.
- **Web UI with real-time streaming** -- React + TypeScript frontend (Open Design / Linear design system, see `DESIGN.md`), FastAPI + WebSocket backend. Streaming token display, tool call cards, guardrail prompts, feedback banners, and a settings panel.
- **Docker + PyInstaller dual distribution** -- run in a container or as a standalone executable.
- **Secure credential storage** -- OS keyring (desktop) with AES-GCM encrypted file fallback (Docker). Keys never appear in logs, git history, or plaintext config.

---

## Quick Start

```bash
pip install -r requirements.txt
cp .harness/config.yaml .harness/config.yaml   # already present; edit provider/model
make run
# Open http://localhost:8000
```

---

## Project Structure

```
lite-agent-harness/
├── docs/                          # Course requirements & design specs
├── harness/                       # Core library
│   ├── config/                    #   YAML config loading & merging
│   │   └── manager.py
│   ├── credentials/               #   Secure API key storage
│   │   └── manager.py
│   ├── feedback/                  #   Deterministic feedback analysis
│   │   ├── analyzer.py            #     Verdict dispatch by tool type
│   │   ├── pytest_parser.py       #     Pytest JSON report parser
│   │   └── retry_policy.py        #     Retry limits & stuck detection
│   ├── guardrails/                #   Three-layer safety system
│   │   ├── engine.py              #     Orchestrator
│   │   ├── path_sandbox.py        #     Layer 1: filesystem boundary
│   │   ├── whitelist.py           #     Layer 2: command allow list
│   │   └── patterns.py            #     Layer 3: regex blacklist
│   ├── llm/                       #   Multi-provider LLM abstraction
│   │   ├── adapter.py             #     ABC for all providers
│   │   ├── anthropic.py           #     Anthropic Messages API
│   │   ├── mock.py                #     Pre-programmed responses for tests
│   │   └── openai.py              #     OpenAI Chat Completions API
│   ├── memory/                    #   Decision & learning persistence
│   │   └── manager.py
│   ├── tools/                     #   Agent tool definitions
│   │   ├── registry.py            #     Registration & dispatch
│   │   ├── code_search.py         #     ripgrep / Python grep
│   │   ├── file_ops.py            #     read_file / write_file
│   │   └── shell.py               #     execute_shell / run_tests
│   ├── __init__.py
│   ├── loop.py                    #   Main agent event loop
│   ├── models.py                  #   Shared pydantic data models
│   └── state_machine.py           #   Deterministic state transition table
├── server/                        # FastAPI web server
│   ├── api/                       #   REST routes
│   │   ├── config_routes.py       #     GET/PUT /api/config
│   │   ├── credential_routes.py   #     GET/POST/DELETE /api/credentials
│   │   └── session_routes.py      #     GET /api/session/history
│   ├── static/                    #   Built frontend assets
│   ├── __init__.py
│   ├── main.py                    #   FastAPI app factory
│   └── ws_handler.py              #   WebSocket session handler
├── tests/                         # Test suite
│   ├── demo/                      #   Runnable demonstrations
│   │   ├── demo_guardrail.py
│   │   ├── demo_feedback_loop.py
│   │   └── demo_sandbox.py
│   ├── integration/               #   Integration tests (12 tests)
│   │   ├── test_agent_loop.py
│   │   └── test_websocket.py
│   ├── unit/                      #   Unit tests (82 tests)
│   │   ├── test_config_merge.py
│   │   ├── test_credential_mask.py
│   │   ├── test_feedback_analyzer.py
│   │   ├── test_feedback_retry.py
│   │   ├── test_guardrail_patterns.py
│   │   ├── test_guardrail_sandbox.py
│   │   ├── test_llm_mock.py
│   │   ├── test_memory_manager.py
│   │   ├── test_state_machine.py
│   │   └── test_tool_registry.py
│   ├── __init__.py
│   └── conftest.py                # Shared fixtures
├── web/                           # React + TypeScript frontend
│   ├── src/
│   │   ├── components/            #   UI components
│   │   ├── hooks/                 #   React hooks (WebSocket, session)
│   │   ├── services/              #   API client
│   │   └── ...
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .harness/
│   └── config.yaml                # Project-level harness configuration
├── DESIGN.md                       # Open Design / Linear design tokens
├── Dockerfile                     # Docker multi-stage build
├── LICENSE                        # MIT
├── Makefile                       # Build, test, run targets
├── pyinstaller.spec               # PyInstaller spec for standalone binary
├── pytest.ini                     # Pytest configuration
└── requirements.txt               # Python dependencies
```

---

## Installation

### Prerequisites

- **Python 3.12+** (developed on 3.14)
- **Node.js 22+** (for frontend development; pre-built static files are included)
- **ripgrep** (optional, but recommended for fast code search; falls back to Python `re`)

### Python Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `pydantic`, `pyyaml`, `anthropic`, `openai`, `fastapi`, `uvicorn`, `keyring`, `cryptography`, `pytest`, `httpx`.

### Frontend Build (optional -- pre-built static files are in `server/static/`)

```bash
cd web
npm install
npm run build
# Output goes to server/static/
```

---

## Running

| Command | Description |
|---|---|
| `make run` | Start the development server (uvicorn with hot-reload on `localhost:8000`) |
| `make test` | Run all unit + integration tests |
| `make test-unit` | Run only unit tests (82 tests, zero network) |
| `make test-integration` | Run only integration tests (12 tests) |
| `make build-web` | Build the React frontend |
| `make build-docker` | Build the Docker image |
| `make build-binary` | Build a standalone executable via PyInstaller |
| `make clean` | Remove build artifacts |

### Development Server

```bash
make run
# or directly:
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open `http://localhost:8000` in your browser. The WebSocket handler starts when you submit a task through the UI.

### Standalone Binary

```bash
make build-binary
# ./dist/lite-agent-harness  (or lite-agent-harness.exe on Windows)
```

---

## Configuration

Configuration is managed by `ConfigManager` which merges three layers (highest priority first):

1. **Project config**: `.harness/config.yaml`
2. **Global config**: `~/.harness/config.yaml`
3. **Built-in defaults**: `ConfigData()` model defaults

### `.harness/config.yaml` Sections

```yaml
model:
  provider: anthropic        # "anthropic", "openai", or unsupported -> Mock
  model_id: claude-sonnet-5  # e.g., "gpt-4o", "claude-sonnet-5-20251001"
  max_tokens: 4096

guardrails:
  max_retries: 3             # Maximum self-correction attempts
  sandbox_root: .            # Restrict file access to this directory
  command_whitelist_extra: [] # Additional allowed commands
  timeout_seconds: 30        # Shell command timeout

tools:
  enabled: [read_file, write_file, execute_shell, run_tests, search_code]

memory:
  max_context_tokens: 8000
  learnings_limit: 20
```

The REST API at `GET /api/config` returns the merged configuration. `PUT /api/config` updates the project-level file.

---

## Credential Management

### Setting API Keys

**Via Web UI**: Open the Settings panel and enter your API key for the selected provider (Anthropic or OpenAI).

**Via environment variable** (for headless / Docker use): The LLM adapters read the relevant key directly from the environment if provided.

### Storage

- **Desktop (keyring available)**: Keys are stored in the OS keychain (`keyring` library).
- **Docker / headless (keyring unavailable)**: Keys are encrypted with AES-GCM and stored at `.harness/credentials/{provider}.enc`. The encryption key is derived via HKDF from the `HARNESS_KEY_PASSWORD` environment variable.

### Security

- Keys are **never** logged, written to git, or stored in plaintext config files.
- The `mask()` method returns a safe display string: `sk-...ab12`.
- The credentials REST API never returns full keys.
- Threat model: local single-user tool. OS keyring protection prevents casual theft; AES-GCM fallback prevents plaintext exposure in Docker volumes.

---

## Distribution

### Docker

```bash
make build-docker
# or manually:
docker build -t lite-agent-harness .
docker run -p 8000:8000 -e HARNESS_KEY_PASSWORD=<your-password> lite-agent-harness
```

Multi-stage build: Node 22-alpine builds the frontend, Python 3.12-slim runs the server. Listens on `0.0.0.0:8000`.

### PyInstaller Binary

```bash
make build-binary
# Output: dist/lite-agent-harness (or .exe on Windows)
```

**Known limitations:**
- Windows SmartScreen may warn on unsigned binaries.
- ripgrep is recommended for `search_code` speed; falls back to Python regex if unavailable.
- The binary is a single-file executable with embedded data directories.

---

## Testing

### Test Suite

| Suite | Count | Scope |
|---|---|---|
| Unit tests | 82 | All components in isolation, zero network, mock LLM |
| Integration tests | 12 | Full agent loop, WebSocket, REST API via TestClient |
| **Total** | **94** | |

```bash
# Full suite
make test

# Individual suites
make test-unit
make test-integration

# Specific test file
python -m pytest tests/unit/test_state_machine.py -v
```

### Runnable Demos

```bash
python tests/demo/demo_guardrail.py       # Guardrail intercepts rm -rf /
python tests/demo/demo_sandbox.py         # Path sandbox + command whitelist
python tests/demo/demo_feedback_loop.py   # Agent failure -> correction -> completion
```

### Testing Philosophy

- **Zero network in unit tests**: All tests use `MockLLMAdapter` with pre-programmed responses.
- **Deterministic state machine**: `transition()` is a pure function tested without any LLM.
- **Feedback analyzer is code, not prompts**: Verdicts come from exit codes and structured JSON, never from LLM judgment.
- **Guardrails are tested in isolation**: Each layer (path, whitelist, pattern) has its own test file.

---

## Agent Architecture

### State Machine

```
     TASK_SUBMIT
  IDLE ---------> PLANNING
                    |  |
           LLM_FINISH | LLM_TOOL_USE
              |       |
           COMPLETED  v
                   EXECUTING
                  /    |     \
          GUARD_ALLOW | GUARD_BLOCK / GUARD_ASK_HUMAN
             |        |          |
         OBSERVING    +--> AWAITING_HUMAN
          / | \                 |
 FEEDBACK_FAIL  | FEEDBACK_PASS | HUMAN_APPROVE / HUMAN_REJECT
     |          |                |
CORRECTING      +<---------------+
     |
RETRY / MAX_RETRIES --> PLANNING or COMPLETED
```

Transitions are computed by the pure function `transition(state, event) -> state` in `harness/state_machine.py`. No LLM call is involved in routing -- this guarantees deterministic behavior for testing.

### Three-Layer Guardrails

| Layer | Component | Action | Scope |
|---|---|---|---|
| 1 | `PathSandbox` | BLOCK | File reads/writes outside the sandbox root |
| 2 | `CommandWhitelist` | ASK_HUMAN | Shell commands not in the allowed list |
| 3 | `PatternBlacklist` | BLOCK or ASK_HUMAN | Dangerous patterns (`rm -rf /`, `DROP TABLE`, force push, curl pipe bash, etc.) |

### Feedback & Self-Correction

The `FeedbackAnalyzer` examines tool results deterministically:

- `run_tests`: Parses `pytest-json-report` output for structured failure details. Generates a suggested fix listing each failed test with file, line, and message.
- `execute_shell`: Verdict based on exit code.
- `write_file`: Verdict based on exit code.
- `read_file` / `search_code`: Returns `UNKNOWN` (no objective pass/fail signal).

The `RetryPolicy` limits retries (`max_retries`, default 3) and detects stuck loops by comparing the last 3 failure signatures. If they are identical, the loop terminates early.

---

## Security Boundary

- **Single-user local tool**: Listens on `localhost:8000` only. Not designed for multi-user or public network exposure.
- **No authentication**: The WebSocket and REST API have no auth layer. Access is restricted by network binding.
- **Guardrails are defense-in-depth**: They provide reasonable safety for code-generation tasks, but are not security guarantees. Regex-based pattern matching can be bypassed by encoding or indirection.
- **Credential threat model**: Keys are stored in the OS keyring on desktop, or AES-GCM encrypted on disk in Docker. The encryption password (`HARNESS_KEY_PASSWORD`) must be provided via environment variable. Keys are never logged or exposed in git.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Jingyu Wang
