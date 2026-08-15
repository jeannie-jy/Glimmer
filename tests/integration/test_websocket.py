"""Integration tests for the FastAPI server + WebSocket handler."""
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from harness.config import ConfigManager
from harness.credentials import CredentialManager
from harness.llm.mock import MockLLMAdapter
from harness.models import LLMResponse, ToolCall
from harness.tools.registry import ToolRegistry
from harness.tools.shell import ExecuteShellTool

from server import ws_handler
from server.api.config_routes import router as config_router, configure_fallback as configure_config
from server.api.session_routes import router as session_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_root() -> Path:
    return Path.cwd()


@pytest.fixture
def config_manager(project_root: Path) -> ConfigManager:
    return ConfigManager(project_root)


@pytest.fixture
def credential_manager(project_root: Path) -> CredentialManager:
    return CredentialManager(project_root)


@pytest.fixture
def default_tools() -> ToolRegistry:
    tools = ToolRegistry()
    tools.register(ExecuteShellTool(cwd=Path.cwd()))
    return tools


def build_app(
    config_manager: ConfigManager,
    credential_manager: CredentialManager,
    tool_registry: ToolRegistry | None = None,
    llm_override: object | None = None,
) -> FastAPI:
    """Build a configured FastAPI test app."""
    app = FastAPI(title="Test Harness")

    configure_config(config_manager, credential_manager)
    configure_config(config_manager, credential_manager)
    ws_handler.configure(
        app,
        config_manager=config_manager,
        credential_manager=credential_manager,
        tool_registry=tool_registry,
        llm_override=llm_override,
    )

    app.include_router(ws_handler.router)
    app.include_router(config_router, prefix="/api")
    app.include_router(session_router, prefix="/api")
    return app


# ---------------------------------------------------------------------------
# WebSocket tests
# ---------------------------------------------------------------------------

class TestWebSocketSession:
    """Tests for the /ws/session WebSocket endpoint."""

    def test_simple_complete_flow(self, config_manager, credential_manager):
        """Connect -> submit task -> receive events -> session complete."""
        mock = MockLLMAdapter([
            LLMResponse(content="Hello, world!", stop_reason="complete"),
        ])
        app = build_app(config_manager, credential_manager, llm_override=mock)

        with TestClient(app).websocket_connect("/ws/session") as ws:
            ws.send_json({"type": "task.submit", "content": "Say hello"})

            # 1. session.created — announced before the turn so the frontend
            #    learns the session id even for fresh bootstrap sessions.
            evt = ws.receive_json()
            assert evt["type"] == "session.created"
            session_id = evt["session_id"]
            assert session_id

            # 2. user.message — the submitted task echoed at its turn start.
            evt = ws.receive_json()
            assert evt["type"] == "user.message"
            assert evt["content"] == "Say hello"

            # 3. state.change: idle -> planning
            evt = ws.receive_json()
            assert evt["type"] == "state.change"
            assert evt["from"] == "idle"
            assert evt["to"] == "planning"

            # 4. llm.response
            evt = ws.receive_json()
            assert evt["type"] == "llm.response"
            assert "Hello, world!" in evt["content"]

            # 5. state.change: planning -> completed
            evt = ws.receive_json()
            assert evt["type"] == "state.change"
            assert evt["from"] == "planning"
            assert evt["to"] == "completed"

            # 6. session.complete
            evt = ws.receive_json()
            assert evt["type"] == "session.complete"
            assert "session_id" in evt

    def test_multi_turn_echoes_each_task_before_its_run(self, config_manager, credential_manager):
        """Every turn echoes its submitted task as user.message before the
        turn's first planning transition; the session id stays stable."""
        mock = MockLLMAdapter([
            LLMResponse(content="First answer.", stop_reason="complete"),
            LLMResponse(content="Second answer.", stop_reason="complete"),
        ])
        app = build_app(config_manager, credential_manager, llm_override=mock)

        with TestClient(app).websocket_connect("/ws/session") as ws:
            ws.send_json({"type": "task.submit", "content": "Task one"})
            events = []
            for _ in range(30):
                evt = ws.receive_json()
                events.append(evt)
                if evt["type"] == "session.complete":
                    break

            created = [e for e in events if e["type"] == "session.created"]
            assert len(created) == 1, events
            session_id = created[0]["session_id"]

            users = [e for e in events if e["type"] == "user.message"]
            assert [u["content"] for u in users] == ["Task one"]
            idx_user = events.index(users[0])
            idx_planning = events.index(
                next(e for e in events if e["type"] == "state.change" and e["to"] == "planning")
            )
            assert idx_user < idx_planning

            ws.send_json({"type": "task.submit", "content": "Task two"})
            events2 = []
            for _ in range(30):
                evt = ws.receive_json()
                events2.append(evt)
                if evt["type"] == "session.complete":
                    break

            users2 = [e for e in events2 if e["type"] == "user.message"]
            assert [u["content"] for u in users2] == ["Task two"]
            assert any(
                e["type"] == "state.change" and e.get("from") == "completed" and e.get("to") == "planning"
                for e in events2
            ), events2

    def test_tool_use_flow(self, config_manager, credential_manager, default_tools):
        """Agent uses a tool, events include tool.invoke and tool.result."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="I'll run the tests.",
                stop_reason="tool_use",
                tool_calls=[ToolCall(
                    id="tc1",
                    name="execute_shell",
                    arguments={"command": "echo hello"},
                )],
            ),
            LLMResponse(content="Done!", stop_reason="complete"),
        ])
        app = build_app(config_manager, credential_manager, default_tools, mock)

        with TestClient(app).websocket_connect("/ws/session") as ws:
            ws.send_json({"type": "task.submit", "content": "Run a test"})

            # Collect all events
            event_types = []
            for _ in range(20):
                try:
                    evt = ws.receive_json()
                    event_types.append(evt["type"])
                    if evt["type"] == "session.complete":
                        break
                except Exception:
                    break

            assert "state.change" in event_types, f"Got events: {event_types}"
            assert "llm.response" in event_types, f"Got events: {event_types}"
            assert "tool.invoke" in event_types, f"Got events: {event_types}"
            assert "tool.result" in event_types, f"Got events: {event_types}"
            assert "session.complete" in event_types, f"Got events: {event_types}"

    def test_guardrail_pending_requires_approval(self, config_manager, credential_manager, default_tools):
        """When a guardrail blocks a command, guardrail.pending is emitted."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="",
                stop_reason="tool_use",
                tool_calls=[ToolCall(
                    id="bad1",
                    name="execute_shell",
                    arguments={"command": "rm -rf /"},
                )],
            ),
        ])
        app = build_app(config_manager, credential_manager, default_tools, mock)

        with TestClient(app).websocket_connect("/ws/session") as ws:
            ws.send_json({"type": "task.submit", "content": "Clean up"})

            # Receive events until guardrail.pending
            saw_pending = False
            for _ in range(15):
                try:
                    evt = ws.receive_json()
                    if evt["type"] == "guardrail.pending":
                        saw_pending = True
                        # Cancel to unblock the session
                        ws.send_json({"type": "session.cancel"})
                        break
                except Exception:
                    break

            assert saw_pending, "Expected guardrail.pending event"

    def test_cancel_during_execution(self, config_manager, credential_manager, default_tools):
        """Cancel sent during execution is processed gracefully."""
        mock = MockLLMAdapter([
            LLMResponse(
                content="Starting tool...",
                stop_reason="tool_use",
                tool_calls=[ToolCall(
                    id="slow1",
                    name="execute_shell",
                    arguments={"command": "echo hello"},
                )],
            ),
        ])
        app = build_app(config_manager, credential_manager, default_tools, mock)

        with TestClient(app).websocket_connect("/ws/session") as ws:
            ws.send_json({"type": "task.submit", "content": "Do something"})
            # Send cancel (might or might not be processed depending on timing)
            ws.send_json({"type": "session.cancel"})

            # Drain events — either the session completes normally or errors
            events = []
            for _ in range(10):
                try:
                    evt = ws.receive_json()
                    events.append(evt["type"])
                    if evt["type"] in ("session.complete", "session.error"):
                        break
                except Exception:
                    break

            # The session must end somehow
            assert events, "No events received"


# ---------------------------------------------------------------------------
# REST API tests
# ---------------------------------------------------------------------------

class TestConfigAPI:
    """Tests for the /api/config REST endpoints."""

    def test_get_config_returns_200(self, config_manager, credential_manager):
        """GET /api/config returns 200 with a JSON body (local mode, no auth)."""
        import os, uuid
        from server.api.auth_routes import get_current_user
        from harness.db.models import User
        from harness.db.database import get_db

        app = build_app(config_manager, credential_manager)
        mock_user = User(id=uuid.uuid4(), github_id=1, login="test")
        app.dependency_overrides[get_current_user] = lambda: mock_user
        # Prevent DB dependency from raising in local mode
        app.dependency_overrides[get_db] = lambda: None

        resp = TestClient(app).get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "model_provider" in data
        assert "model_id" in data


class TestCredentialAPI:
    """Tests for the /api/credentials REST endpoints."""

    def test_get_credentials_status_returns_json(self, config_manager, credential_manager):
        """GET /api/credentials/status returns 200 with provider status."""
        import os, uuid
        from server.api.auth_routes import get_current_user
        from harness.db.models import User
        from harness.db.database import get_db

        app = build_app(config_manager, credential_manager)
        mock_user = User(id=uuid.uuid4(), github_id=1, login="test")
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: None

        resp = TestClient(app).get("/api/credentials/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data


class TestSessionAPI:
    """Tests for the /api/session REST endpoints."""

    def test_get_session_history_returns_empty(self, config_manager, credential_manager):
        """GET /api/sessions returns empty list in local mode."""
        import os, uuid
        from server.api.auth_routes import get_current_user
        from harness.db.models import User
        from harness.db.database import get_db

        app = build_app(config_manager, credential_manager)
        mock_user = User(id=uuid.uuid4(), github_id=1, login="test")
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: None

        resp = TestClient(app).get("/api/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert data["sessions"] == []
