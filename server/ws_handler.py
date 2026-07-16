"""WebSocket handler for session lifecycle management."""
import asyncio
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from harness.auth.jwt import get_user_id_from_token
from harness.config import ConfigManager
from harness.credentials import CredentialManager
from harness.loop import AgentLoop
from harness.tools.registry import ToolRegistry
from harness.tools.file_ops import ReadFileTool, WriteFileTool
from harness.tools.shell import ExecuteShellTool, RunTestsTool
from harness.tools.code_search import SearchCodeTool
from harness.guardrails.engine import GuardrailEngine
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.feedback.retry_policy import RetryPolicy
from harness.llm import AnthropicAdapter, OpenAIAdapter, MockLLMAdapter
from harness.models import ConfigData
from harness.db.database import get_db
from harness.db.models import User, Session as DBSession, Message as DBMessage
from harness.sandbox.docker_manager import DockerManager
from server.api.config_routes import get_user_api_key, get_user_config

router = APIRouter()


def configure(
    app,
    config_manager: ConfigManager | None = None,
    credential_manager: CredentialManager | None = None,
    tool_registry: ToolRegistry | None = None,
    llm_override: object | None = None,
) -> None:
    """Inject shared dependencies into app.state.

    Parameters
    ----------
    app:
        The FastAPI application to store state on.
    config_manager:
        Resolves project/global config.
    credential_manager:
        Manages API key storage.
    tool_registry:
        Shared tool registry (created once if not provided).
    llm_override:
        If set, every session uses this LLM adapter (useful for tests).
    """
    if config_manager is not None:
        app.state.ws_config_manager = config_manager
    if credential_manager is not None:
        app.state.ws_credential_manager = credential_manager
    if tool_registry is not None:
        app.state.ws_tool_registry = tool_registry
    if llm_override is not None:
        app.state.ws_llm_override = llm_override


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/session")
async def websocket_session(websocket: WebSocket) -> None:
    """Main WebSocket session handler.

    Protocol — *client* sends JSON messages:
        ``{"type": "task.submit", "content": "..."}``
        ``{"type": "guardrail.approve"}``
        ``{"type": "guardrail.reject"}``
        ``{"type": "session.cancel"}``

    *Server* sends JSON messages:
        ``{"type": "state.change", "from": "...", "to": "..."}``
        ``{"type": "llm.response", "content": "...", "tool_calls": [...]}``
        ``{"type": "tool.invoke", "tool": "...", "args": {...}}``
        ``{"type": "tool.result", "tool_name": "...", "exit_code": 0, ...}``
        ``{"type": "guardrail.pending", "action": "...", "reason": "...", ...}``
        ``{"type": "feedback.analysis", "verdict": "...", ...}``
        ``{"type": "session.complete"}``
        ``{"type": "session.error", "message": "..."}``
    """
    await websocket.accept()

    # ---- Mode detection and JWT extraction ----
    token = websocket.query_params.get("token", "")
    user_id_from_jwt = get_user_id_from_token(token)
    LOCAL_MODE = not os.environ.get("DATABASE_URL")

    if not LOCAL_MODE and not user_id_from_jwt:
        await websocket.send_json({"type": "session.error", "message": "Authentication required"})
        await websocket.close(code=4001)
        return

    # Resolve shared components from app.state
    app_state = websocket.app.state
    config_manager: ConfigManager | None = getattr(app_state, 'ws_config_manager', None)
    credential_manager: CredentialManager | None = getattr(app_state, 'ws_credential_manager', None)

    # ---- Wait for task.submit ----
    try:
        raw = await websocket.receive_json()
    except WebSocketDisconnect:
        return

    if raw.get("type") != "task.submit":
        await websocket.send_json({"type": "session.error", "message": "Expected task.submit"})
        await websocket.close()
        return

    task: str = raw.get("content", "")

    # ---- Resolve config & credentials ----
    if LOCAL_MODE:
        project_root = Path.cwd()
        if config_manager is None:
            config_manager = ConfigManager(project_root)
        if credential_manager is None:
            credential_manager = CredentialManager(project_root)

        config: ConfigData = config_manager.load()
        api_key: str | None = credential_manager.load(config.model_provider)
        docker_mgr = None
        container_id = None
    else:
        async for db_session in get_db():
            result = await db_session.execute(select(User).where(User.id == user_id_from_jwt))
            user = result.scalar_one_or_none()
            if not user:
                await websocket.send_json({"type": "session.error", "message": "User not found"})
                await websocket.close(code=4001)
                return

            config = await get_user_config(user, db_session)
            api_key = await get_user_api_key(user, db_session)
            break

        if config is None:
            config = ConfigData()

        # Create Docker sandbox container for this session
        session_id = str(uuid.uuid4())
        docker_mgr = DockerManager()
        container_id = await docker_mgr.create(str(user.id), session_id)

    # ---- Create per-session components ----
    if LOCAL_MODE:
        tools = getattr(app_state, 'ws_tool_registry', None)
        if tools is None:
            tools = _build_default_tool_registry()
    else:
        tools = _build_default_tool_registry(docker_mgr=docker_mgr, container_id=container_id)
    guardrails = GuardrailEngine(
        sandbox_root=config.sandbox_root,
        whitelist_extra=config.command_whitelist_extra,
    )
    analyzer = FeedbackAnalyzer()
    policy = RetryPolicy(max_retries=config.max_retries)
    loop = AgentLoop(tools, guardrails, analyzer, policy)

    # ---- Create LLM adapter ----
    llm_override = getattr(app_state, 'ws_llm_override', None)
    if llm_override is not None:
        llm = llm_override  # type: ignore[assignment]
    elif api_key:
        llm = _create_llm_from_config(config, api_key)
    else:
        llm = MockLLMAdapter([])

    # ---- Wire event handler -> WebSocket ----
    async def emit_to_ws(event: str, **data: object) -> None:
        try:
            await websocket.send_json({"type": event, **data})
        except Exception:
            pass  # WebSocket likely closed

    loop.on_event(emit_to_ws)

    # ---- Run in background ----
    cancel_event = asyncio.Event()
    harness_session = None

    async def run_task() -> None:
        nonlocal harness_session
        try:
            harness_session = await loop.run(task, llm)
            # If the loop paused for human approval, wait for client response
            while harness_session.state.value == "awaiting_human":
                cancel_or_approve = asyncio.create_task(
                    _wait_for_human_response(websocket, cancel_event)
                )
                try:
                    msg = await cancel_or_approve
                except (WebSocketDisconnect, asyncio.CancelledError):
                    cancel_event.set()
                    break

                if msg is None:  # cancellation or disconnect
                    break

                if msg.get("type") == "guardrail.approve":
                    loop.approve_pending(harness_session)
                elif msg.get("type") == "guardrail.reject":
                    loop.reject_pending(harness_session)
                elif msg.get("type") == "session.cancel":
                    cancel_event.set()
                    await emit_to_ws("session.error", message="Cancelled by user")
                    return

                # Continue the loop
                harness_session = await loop.resume(harness_session, llm)

        except Exception as exc:
            try:
                await emit_to_ws("session.error", message=str(exc))
            except Exception:
                pass
        finally:
            # Multi-user: save session + messages to DB
            if not LOCAL_MODE and harness_session is not None:
                try:
                    async for db_s in get_db():
                        status = "completed" if harness_session.state.value == "completed" else "error"
                        db_sess = DBSession(
                            id=uuid.UUID(harness_session.id),
                            user_id=user.id,
                            task=harness_session.task,
                            status=status,
                            container_id=container_id,
                            retry_count=harness_session.retry_count,
                        )
                        db_s.add(db_sess)
                        for msg in harness_session.messages:
                            payload: dict = {"content": msg.content}
                            if msg.tool_call_id:
                                payload["tool_call_id"] = msg.tool_call_id
                            db_s.add(DBMessage(
                                session_id=uuid.UUID(harness_session.id),
                                type=msg.role,
                                payload=payload,
                            ))
                        await db_s.flush()
                        break
                except Exception:
                    pass

    runner = asyncio.create_task(run_task())

    # ---- Message pump for cancel / misc signals ----
    try:
        while not runner.done():
            done, _ = await asyncio.wait(
                [runner],
                timeout=1.0,
            )
            if done:
                break
            # Check for incoming messages (cancel etc.) during loop pauses
            try:
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                if msg.get("type") == "session.cancel":
                    cancel_event.set()
                    runner.cancel()
                    await emit_to_ws("session.error", message="Cancelled by user")
                    break
            except (asyncio.TimeoutError, WebSocketDisconnect):
                continue
    except WebSocketDisconnect:
        cancel_event.set()
        runner.cancel()
    except Exception:
        cancel_event.set()
        runner.cancel()
    finally:
        if not runner.done():
            runner.cancel()
        try:
            await runner
        except (asyncio.CancelledError, Exception):
            pass

        # Multi-user: destroy Docker container
        if not LOCAL_MODE and docker_mgr is not None and container_id is not None:
            try:
                await docker_mgr.destroy(container_id)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_default_tool_registry(docker_mgr=None, container_id=None) -> ToolRegistry:
    """Build and return the default set of tools."""
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ExecuteShellTool(docker_mgr=docker_mgr, container_id=container_id))
    registry.register(RunTestsTool(docker_mgr=docker_mgr, container_id=container_id))
    registry.register(SearchCodeTool())
    return registry


def _create_llm_from_config(config: ConfigData, api_key: str) -> object:
    """Create the appropriate LLM adapter based on configuration."""
    provider = config.model_provider.lower()
    base_url = (config.base_url or "").strip()

    if provider == "anthropic":
        return AnthropicAdapter(api_key=api_key, model=config.model_id)
    elif base_url:
        return OpenAIAdapter(api_key=api_key, model=config.model_id, base_url=base_url)
    elif provider == "openai":
        return OpenAIAdapter(api_key=api_key, model=config.model_id)
    else:
        return MockLLMAdapter([])


async def _wait_for_human_response(
    websocket: WebSocket,
    cancel_event: asyncio.Event,
) -> dict | None:
    """Wait for a guardrail.approve / guardrail.reject / session.cancel message.

    Returns ``None`` if cancelled or the WebSocket disconnects.
    """
    try:
        while not cancel_event.is_set():
            msg = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
            if msg.get("type") in ("guardrail.approve", "guardrail.reject", "session.cancel"):
                return msg
        return None
    except (asyncio.TimeoutError, WebSocketDisconnect, Exception):
        return None
