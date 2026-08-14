"""WebSocket handler for session lifecycle management."""
import asyncio
import base64
import os
import posixpath
import shlex
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from harness.auth.jwt import get_user_id_from_token
from harness.config import ConfigManager
from harness.credentials import CredentialManager
from harness.loop import AgentLoop
from harness.models import State, Message as PydanticMessage, Session as PydanticSession, ConfigData, ToolCall
from harness.tools.registry import ToolRegistry
from harness.tools.file_ops import ReadFileTool, WriteFileTool
from harness.tools.shell import ExecuteShellTool, RunTestsTool
from harness.tools.code_search import SearchCodeTool
from harness.guardrails.engine import GuardrailEngine
from harness.feedback.analyzer import FeedbackAnalyzer
from harness.feedback.retry_policy import RetryPolicy
from harness.llm import AnthropicAdapter, OpenAIAdapter, MockLLMAdapter
from harness.db.database import get_db
from harness.db.models import User, Session as DBSession, Message as DBMessage
from harness.sandbox.docker_manager import DockerManager
from server.api.auth_routes import LOCAL_USER_ID
from server.api.config_routes import get_user_api_key, get_user_config
from server.paths import container_path
from server.session_registry import register as register_session, unregister as unregister_session

router = APIRouter()


def configure(
    app,
    config_manager: ConfigManager | None = None,
    credential_manager: CredentialManager | None = None,
    tool_registry: ToolRegistry | None = None,
    llm_override: object | None = None,
) -> None:
    """Inject shared dependencies into app.state."""
    if config_manager is not None:
        app.state.ws_config_manager = config_manager
    if credential_manager is not None:
        app.state.ws_credential_manager = credential_manager
    if tool_registry is not None:
        app.state.ws_tool_registry = tool_registry
    if llm_override is not None:
        app.state.ws_llm_override = llm_override


def _build_default_tool_registry(docker_mgr=None, container_id=None, workspace_root: Path | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ReadFileTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root))
    registry.register(WriteFileTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root))
    registry.register(ExecuteShellTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
    registry.register(RunTestsTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
    registry.register(SearchCodeTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
    return registry


def _create_llm_from_config(config: ConfigData, api_key: str) -> object:
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


def _resolve_local_api_key(credential_manager, config: ConfigData) -> str | None:
    """Resolve the API key for local-mode chat.

    The Settings page stores the key under provider "local" — prefer that so
    newly saved keys take effect. Fall back to the provider-named file for
    pre-existing installs that only have ``{model_provider}.key``.
    """
    key = credential_manager.load("local")
    if key:
        return key
    provider = getattr(config, "model_provider", None)
    if provider:
        return credential_manager.load(provider)
    return None


def _message_to_db_payload(msg: PydanticMessage) -> dict:
    """Convert a pydantic Message to the JSON payload stored on a DBMessage."""
    payload: dict = {"content": msg.content}
    if msg.tool_call_id:
        payload["tool_call_id"] = msg.tool_call_id
    if msg.tool_calls:
        payload["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
    return payload


def _db_payload_to_message(role: str, payload: dict | None) -> PydanticMessage:
    """Reconstruct a pydantic Message from a DBMessage row's payload."""
    payload = payload or {}
    return PydanticMessage(
        role=role,
        content=payload.get("content", ""),
        tool_call_id=payload.get("tool_call_id"),
        tool_calls=[ToolCall(**d) for d in payload.get("tool_calls", [])],
    )


async def _save_session_to_db(
    harness_session: PydanticSession,
    user_id: str,
    container_id: str | None,
    db_session_factory,
) -> None:
    """Persist the harness session and its messages to the database."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from harness.db.database import _get_engine

    engine = _get_engine()
    if engine is None:
        return
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db_s:
        try:
            status = "completed" if harness_session.state.value in ("completed", "awaiting_human") else "error"
            result = await db_s.execute(
                select(DBSession).where(DBSession.id == uuid.UUID(harness_session.id))
            )
            db_sess = result.scalar_one_or_none()
            if db_sess is None:
                db_sess = DBSession(
                    id=uuid.UUID(harness_session.id),
                    user_id=uuid.UUID(user_id),
                    task=harness_session.task,
                    status=status,
                    container_id=container_id,
                    retry_count=harness_session.retry_count,
                )
                db_s.add(db_sess)
            else:
                db_sess.task = harness_session.task
                db_sess.status = status
                db_sess.retry_count = harness_session.retry_count
            from datetime import datetime, timezone
            db_sess.finished_at = datetime.now(timezone.utc)

            # Delete old messages and re-insert to avoid duplicates
            existing = (await db_s.execute(
                select(DBMessage).where(DBMessage.session_id == uuid.UUID(harness_session.id))
            )).scalars().all()
            for m in existing:
                await db_s.delete(m)

            for msg in harness_session.messages:
                # Skip system prompts — not user-facing
                if msg.role == "system":
                    continue
                db_s.add(DBMessage(
                    session_id=uuid.UUID(harness_session.id),
                    type=msg.role,
                    payload=_message_to_db_payload(msg),
                ))
            await db_s.commit()
        except Exception:
            await db_s.rollback()
            raise


async def _load_session_from_db(
    session_id: str,
    user_id: str,
    db_session_factory,
) -> PydanticSession | None:
    """Reconstruct a pydantic Session from the database."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from harness.db.database import _get_engine

    engine = _get_engine()
    if engine is None:
        return None
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db_s:
        result = await db_s.execute(
            select(DBSession)
            .options(selectinload(DBSession.messages))
            .where(
                DBSession.id == uuid.UUID(session_id),
                DBSession.user_id == uuid.UUID(user_id),
            )
        )
        db_sess = result.scalar_one_or_none()
        if db_sess is None:
            return None

        pydantic_session = PydanticSession(
            id=str(db_sess.id),
            task=db_sess.task,
            state=State.COMPLETED,
            retry_count=db_sess.retry_count or 0,
        )
        for db_msg in db_sess.messages or []:
            pydantic_session.messages.append(
                _db_payload_to_message(db_msg.type, db_msg.payload)
            )
    return pydantic_session


# ---------------------------------------------------------------------------
# File operation helpers (used by the WebSocket endpoint)
# ---------------------------------------------------------------------------

# Directories excluded from local-mode file listings: harness internals and
# dependency trees, not agent workspace files.
_LOCAL_SKIP_DIRS = {
    ".git", ".harness", ".claude", "node_modules", "__pycache__", ".venv", "venv",
    # The application's own source tree — when the workspace root falls back
    # to the server cwd (no WORKSPACE_ROOT set), these are server internals,
    # not agent workspace files.
    "harness", "server", "web", "tests", "docs",
    ".github", ".agents", ".superpowers", ".pytest_cache", "dist", "build",
}

# Sensitive files that must never appear in file listings regardless of
# workspace root (defense in depth).
_LOCAL_SKIP_FILES = {".env", ".env.example"}
_LOCAL_SKIP_SUFFIXES = (".key", ".pem")


def _workspace_root() -> Path:
    """Root directory for local-mode agent file operations.

    WORKSPACE_ROOT (when set) points agent file operations at a dedicated
    workspace directory — e.g. ``/workspace`` on deployed servers without a
    Docker socket, where the server cwd is the application source tree and
    must not be exposed as the agent's workspace. Falls back to the server
    cwd for local development.
    """
    env_root = os.environ.get("WORKSPACE_ROOT")
    if env_root:
        root = Path(env_root)
        root.mkdir(parents=True, exist_ok=True)
        return root.resolve()
    return Path.cwd().resolve()


def _safe_local_path(rel: str) -> Path | None:
    """Resolve a client-supplied relative path under the local workspace.

    Returns None when the path escapes the workspace (traversal or absolute).
    The workspace is the WORKSPACE_ROOT directory (or the server's cwd when
    unset) — the same root the local-mode tools operate on.
    """
    root = _workspace_root()
    # Absolute-looking paths (posix "/x", windows "C:\\x", UNC "\\\\x") are
    # never valid workspace-relative paths — reject before resolving.
    if rel.startswith(("/", "\\")) or Path(rel).is_absolute() or (len(rel) > 1 and rel[1] == ":"):
        return None
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root):
        return None
    return candidate


def _list_local_files() -> list[dict]:
    """List agent workspace files in local mode (same shape as files.list)."""
    root = _workspace_root()
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(root)
        if any(part in _LOCAL_SKIP_DIRS for part in rel.parts):
            continue
        if rel.name in _LOCAL_SKIP_FILES or rel.name.endswith(_LOCAL_SKIP_SUFFIXES):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        files.append({
            "name": rel.as_posix(),
            "size": st.st_size,
            "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M"),
        })
    return files


def _upload_local(path: str, content_b64: str) -> str | None:
    """Write base64 content into the local workspace. Returns error text or None."""
    safe = _safe_local_path(path)
    if safe is None:
        return f"Path not allowed: {path}"
    try:
        data = base64.b64decode(content_b64)
        safe.parent.mkdir(parents=True, exist_ok=True)
        safe.write_bytes(data)
        return None
    except Exception as e:
        return str(e)


def _read_local(path: str) -> tuple[str | None, str | None]:
    """Read a file from the local workspace. Returns (content, error)."""
    safe = _safe_local_path(path)
    if safe is None:
        return None, "Path not allowed"
    try:
        return safe.read_text(encoding="utf-8"), None
    except Exception as e:
        return None, str(e)


def _delete_local(path: str) -> str | None:
    """Delete a file from the local workspace. Returns error text or None."""
    safe = _safe_local_path(path)
    if safe is None:
        return f"Path not allowed: {path}"
    try:
        safe.unlink(missing_ok=True)
        return None
    except Exception as e:
        return str(e)


async def _upload_to_container(docker_mgr, container_id, path: str, content_b64: str) -> str | None:
    """Upload base64 content into the container workspace. Returns error or None."""
    safe = container_path(path)
    if safe is None:
        return f"Path not allowed: {path}"
    try:
        parent = posixpath.dirname(safe)
        r = await docker_mgr.exec(container_id, f"mkdir -p {shlex.quote(parent)}", timeout=5)
        if r.exit_code != 0:
            return r.stderr or "Upload failed"
        r = await docker_mgr.exec(
            container_id,
            f"echo {shlex.quote(content_b64)} | base64 -d > {shlex.quote(safe)}",
            timeout=15,
        )
        if r.exit_code != 0:
            return r.stderr or "Upload failed"
        return None
    except Exception as e:
        return str(e)


async def _delete_from_container(docker_mgr, container_id, path: str) -> str | None:
    """Delete a file from the container workspace. Returns error or None."""
    safe = container_path(path)
    if safe is None:
        return f"Path not allowed: {path}"
    try:
        r = await docker_mgr.exec(container_id, f"rm -f {shlex.quote(safe)}", timeout=10)
        if r.exit_code != 0:
            return r.stderr or "Delete failed"
        return None
    except Exception as e:
        return str(e)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

async def _send_file_list(websocket, docker_mgr, container_id, LOCAL_MODE):
    """Send file list from workspace to frontend."""
    if LOCAL_MODE or docker_mgr is None or container_id is None:
        await websocket.send_json({"type": "files.list", "files": _list_local_files()})
        return
    try:
        result = await docker_mgr.exec(
            container_id,
            "find /workspace -type f -printf '%p\\t%s\\t%TY-%Tm-%TdT%TH:%TM\\n' 2>/dev/null",
            timeout=10,
        )
        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                p = parts[0].replace("/workspace/", "", 1)
                if p == "/workspace" or not p:
                    continue
                files.append({"name": p, "size": int(parts[1]), "modified": parts[2]})
        files.sort(key=lambda f: (("/" in f["name"]), f["name"]))
        await websocket.send_json({"type": "files.list", "files": files})
    except Exception:
        await websocket.send_json({"type": "files.list", "files": []})


@router.websocket("/ws/session")
async def websocket_session(websocket: WebSocket) -> None:
    """Main WebSocket session handler with multi-turn support.

    Protocol — *client* sends:
        ``{"type": "task.submit", "content": "..."}``  — submit a task (multi-turn)
        ``{"type": "session.new"}``                      — start a brand-new session
        ``{"type": "session.load", "session_id": "..."}`` — load a past session
        ``{"type": "guardrail.approve"}``                — approve pending tool
        ``{"type": "guardrail.reject"}``                 — reject pending tool
        ``{"type": "session.cancel"}``                   — cancel current task
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

    app_state = websocket.app.state
    config_manager: ConfigManager | None = getattr(app_state, 'ws_config_manager', None)
    credential_manager: CredentialManager | None = getattr(app_state, 'ws_credential_manager', None)

    # ---- Declare outer scope variables for later initialization ----
    docker_mgr = None
    container_id = None
    user_id = user_id_from_jwt or LOCAL_USER_ID
    harness_session: PydanticSession | None = None

    # ---- Create Docker container eagerly (before first message) ----
    async def _create_docker_container() -> str | None:
        if LOCAL_MODE: return None
        nonlocal docker_mgr
        if docker_mgr is None: docker_mgr = DockerManager()
        return await docker_mgr.create(user_id, f"user-{user_id[:12]}")

    async def _destroy_docker_container():
        nonlocal docker_mgr, container_id
        if harness_session is not None: unregister_session(harness_session.id)
        if not LOCAL_MODE and docker_mgr is not None and container_id is not None:
            try: await docker_mgr.destroy(container_id)
            except Exception: pass
            container_id = None

    try:
        container_id = await _create_docker_container()
    except Exception as e:
        print(f"[WS] Docker unavailable, falling back to local execution: {e}")
        docker_mgr = None
        container_id = None
    if not LOCAL_MODE and container_id:
        register_session("pending", docker_mgr, container_id, user_id)

    # ---- Wait for first message (task.submit or session.load) ----
    # Loop until we get a valid first message; handle files.list immediately,
    # defer files.upload/filedownload/etc. for replay after bootstrap.
    msg_type = ""
    raw = {}
    deferred: list[dict] = []
    while msg_type not in ("task.submit", "session.load"):
        try:
            raw = await websocket.receive_json()
            msg_type = raw.get("type", "")
            if msg_type not in ("task.submit", "session.load"):
                if msg_type == "files.list":
                    await _send_file_list(websocket, docker_mgr, container_id, LOCAL_MODE)
                elif msg_type in ("files.upload", "files.download", "files.delete"):
                    deferred.append(raw)
        except WebSocketDisconnect:
            return

    # ---- Resolve config & credentials ----
    if LOCAL_MODE:
        project_root = Path.cwd()
        if config_manager is None:
            config_manager = ConfigManager(project_root)
        if credential_manager is None:
            credential_manager = CredentialManager(project_root)
        config: ConfigData = config_manager.load()
        api_key: str | None = _resolve_local_api_key(credential_manager, config)
        user_id = LOCAL_USER_ID
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
        user_id = str(user.id)
        docker_mgr = None
        container_id = None

    # ---- Session bootstrap ----
    if msg_type == "session.load":
        load_id = raw.get("session_id", "")
        if LOCAL_MODE:
            harness_session = PydanticSession(id=str(uuid.uuid4()), task="Loaded session", state=State.COMPLETED)
        else:
            loaded = await _load_session_from_db(load_id, user_id, get_db)
            if loaded is None:
                await websocket.send_json({"type": "session.error", "message": "Session not found"})
                await websocket.close(code=4004)
                return
            harness_session = loaded
            # Send loaded messages to frontend for display
            for msg in harness_session.messages:
                if msg.role == "user":
                    # Will be echoed as display items
                    pass
            await websocket.send_json({
                "type": "session.loaded",
                "session_id": harness_session.id,
                "task": harness_session.task,
                "message_count": len(harness_session.messages),
            })
        # Wait for next message (task.submit to continue, or session.new to start fresh)
        try:
            raw = await websocket.receive_json()
        except WebSocketDisconnect:
            return
        if raw.get("type") == "task.submit":
            task_content = raw.get("content", "")
        elif raw.get("type") == "session.new":
            harness_session = PydanticSession(id=str(uuid.uuid4()), task="", state=State.IDLE)
            task_content = ""
        else:
            await websocket.send_json({"type": "session.error", "message": "Expected task.submit after session.load"})
            return
    else:
        # task.submit as first message — may continue an existing session
        task_content = raw.get("content", "")
        load_id = raw.get("session_id", "")
        is_resuming = False
        if load_id and not LOCAL_MODE:
            try:
                loaded = await _load_session_from_db(load_id, user_id, get_db)
                if loaded is not None:
                    harness_session = loaded
                    is_resuming = True
                    print(f"[WS] Bootstrap: continuing session {harness_session.id}")
                else:
                    harness_session = PydanticSession(id=str(uuid.uuid4()), task=task_content, state=State.IDLE)
            except Exception as e:
                print(f"[WS] Bootstrap: failed to load session {load_id}: {e}")
                await websocket.send_json({"type": "session.error", "message": f"Failed to load session: {e}"})
                await websocket.close(code=4000)
                return
        if not is_resuming:
            harness_session = PydanticSession(id=str(uuid.uuid4()), task=task_content, state=State.IDLE)

    # ---- Create per-session components (Docker container once per session) ----
    async def _create_docker_container() -> str | None:
        """Create a Docker sandbox container for multi-user mode."""
        if LOCAL_MODE:
            return None
        nonlocal docker_mgr
        if docker_mgr is None:
            docker_mgr = DockerManager()
        return await docker_mgr.create(user_id, harness_session.id)

    async def _destroy_docker_container():
        """Destroy the current Docker container if it exists."""
        nonlocal docker_mgr, container_id
        if harness_session is not None:
            unregister_session(harness_session.id)
        if not LOCAL_MODE and docker_mgr is not None and container_id is not None:
            try:
                await docker_mgr.destroy(container_id)
            except Exception:
                pass
            container_id = None

    def _build_components():
        tools = getattr(app_state, 'ws_tool_registry', None)
        if tools is None:
            tools = _build_default_tool_registry(docker_mgr=docker_mgr, container_id=container_id,
                                                 workspace_root=_workspace_root())
        # WORKSPACE_ROOT (when set) pins the agent's file operations to the
        # dedicated workspace directory instead of the server cwd — without
        # it, deployed servers without a Docker socket would expose their
        # source tree as the agent workspace.
        sandbox_root = str(_workspace_root()) if os.environ.get("WORKSPACE_ROOT") else config.sandbox_root
        guardrails = GuardrailEngine(
            sandbox_root=sandbox_root,
            whitelist_extra=config.command_whitelist_extra,
        )
        analyzer = FeedbackAnalyzer()
        policy = RetryPolicy(max_retries=config.max_retries)
        loop = AgentLoop(tools, guardrails, analyzer, policy)
        return tools, guardrails, analyzer, policy, loop

    # Create Docker container for the initial session
    try:
        container_id = await _create_docker_container()
    except Exception as e:
        print(f"[WS] Docker unavailable for session, falling back to local execution: {e}")
        docker_mgr = None
        container_id = None
    if not LOCAL_MODE and container_id:
        register_session(harness_session.id, docker_mgr, container_id, user_id)
        # The bootstrap registered a provisional "pending" entry before the
        # session id existed — drop it so it cannot be looked up by clients.
        unregister_session("pending")
    tools, guardrails, analyzer, policy, loop = _build_components()

    async def _create_llm():
        llm_override = getattr(app_state, 'ws_llm_override', None)
        if llm_override is not None:
            return llm_override
        elif api_key:
            return _create_llm_from_config(config, api_key)
        else:
            raise RuntimeError(
                "API Key 未配置。请在 Settings 面板中录入你的 API Key（Anthropic 或 OpenAI 兼容均可）。"
            )

    # ---- Track known files for created vs modified events ----
    _known_files: set[str] = set()

    # ---- Wire event handler → WebSocket ----
    async def emit_to_ws(event: str, **data: object) -> None:
        try:
            await websocket.send_json({"type": event, **data})
            # After a successful write_file, emit file.created or file.modified
            if event == "tool.result" and data.get("tool_name") == "write_file" and data.get("exit_code") == 0:
                # Extract path from the write_file stdout: "Wrote N bytes to <path>"
                stdout = str(data.get("stdout", ""))
                import re
                match = re.search(r"to\s+(.+)$", stdout)
                if match:
                    filepath = match.group(1).strip()
                    if filepath not in _known_files:
                        _known_files.add(filepath)
                        await websocket.send_json({"type": "file.created", "path": filepath})
                    else:
                        await websocket.send_json({"type": "file.modified", "path": filepath})
        except Exception:
            pass

    loop.on_event(emit_to_ws)

    # ---- Multi-turn message loop ----
    cancel_event = asyncio.Event()
    # Single-reader protocol: while a turn runs as a task, the main loop keeps
    # reading the websocket and forwards control messages (cancel / guardrail
    # decisions) here; _wait_for_human_response consumes from this queue.
    human_queue: asyncio.Queue = asyncio.Queue()
    runner: asyncio.Task | None = None

    async def run_one_turn(task_text: str) -> PydanticSession | None:
        """Execute a single task turn. Returns the updated session or None on error."""
        nonlocal harness_session
        try:
            if harness_session.state in (State.IDLE, State.COMPLETED, State.ERROR):
                if harness_session.state == State.IDLE:
                    # First turn: use run()
                    llm = await _create_llm()
                    # Re-wire event handler (may have been cleared)
                    loop.on_event(emit_to_ws)
                    harness_session = await loop.run(task_text, llm)
                else:
                    # Subsequent turn: use continue_turn()
                    llm = await _create_llm()
                    loop.on_event(emit_to_ws)
                    harness_session = await loop.continue_turn(harness_session, task_text, llm)

            # Handle AWAITING_HUMAN sub-loop
            while harness_session.state.value == "awaiting_human":
                cancel_or_approve = asyncio.create_task(
                    _wait_for_human_response(human_queue, cancel_event)
                )
                try:
                    msg = await cancel_or_approve
                except (WebSocketDisconnect, asyncio.CancelledError):
                    cancel_event.set()
                    return None

                if msg is None:
                    return None
                if msg.get("type") == "guardrail.approve":
                    loop.approve_pending(harness_session)
                elif msg.get("type") == "guardrail.reject":
                    loop.reject_pending(harness_session)
                elif msg.get("type") == "session.cancel":
                    # The pump already emitted session.error and cancelled us
                    cancel_event.set()
                    return None
                harness_session = await loop.resume(harness_session, await _create_llm())

            return harness_session
        except asyncio.CancelledError:
            # runner.cancel() from the pump — the pump emits session.error
            cancel_event.set()
            return None
        except Exception as exc:
            try:
                await emit_to_ws("session.error", message=str(exc))
            except Exception:
                pass
            return None

    async def _save_and_notify():
        """Save session to DB and notify frontend."""
        if not LOCAL_MODE and harness_session is not None:
            try:
                await _save_session_to_db(harness_session, user_id, container_id, get_db)
                await emit_to_ws("session.saved", session_id=harness_session.id)
                print(f"[WS] Session saved: {harness_session.id}")
            except Exception as e:
                print(f"[WS] Failed to save session: {e}")

    async def _pump_until_turn_done() -> list[dict]:
        """Read the websocket while the runner task is in flight.

        Control messages (cancel / guardrail decisions) are forwarded to the
        turn via ``human_queue`` and cancel stops the turn immediately;
        everything else is buffered and dispatched after the turn completes.
        """
        buffered: list[dict] = []
        while not runner.done():
            try:
                raw = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            except asyncio.TimeoutError:
                continue
            t = raw.get("type", "")
            if t == "session.cancel":
                cancel_event.set()
                human_queue.put_nowait(raw)
                runner.cancel()
                await emit_to_ws("session.error", message="Cancelled by user")
            elif t in ("guardrail.approve", "guardrail.reject"):
                human_queue.put_nowait(raw)
            else:
                buffered.append(raw)
        # Drop control messages the turn never consumed
        while not human_queue.empty():
            human_queue.get_nowait()
        return buffered

    async def run_task_pumped(task_text: str):
        """Run a turn as a task, pumping websocket messages until it finishes.

        Returns ``(updated_session_or_None, buffered_messages)``. On success
        ``run_one_turn`` also updates the outer ``harness_session``; on
        failure/cancel it is left untouched (the pre-turn session survives).
        """
        nonlocal runner
        cancel_event.clear()
        runner = asyncio.create_task(run_one_turn(task_text))
        buffered: list[dict] = []
        try:
            buffered = await _pump_until_turn_done()
            result = await runner
        except WebSocketDisconnect:
            if runner is not None and not runner.done():
                runner.cancel()
            raise
        except asyncio.CancelledError:
            # The runner task ended cancelled without catching (rare race)
            result = None
            buffered = []
        finally:
            runner = None
        return result, buffered

    async def handle_message(raw: dict) -> None:
        """Dispatch a single client message (shared by main loop and replay)."""
        nonlocal harness_session, container_id, docker_mgr
        nonlocal tools, guardrails, analyzer, policy, loop
        msg_type = raw.get("type", "")
        if msg_type == "session.new":
            # Save current session, then start a fresh one
            await _save_and_notify()
            harness_session = PydanticSession(id=str(uuid.uuid4()), task="", state=State.IDLE)
            await _destroy_docker_container()
            try:
                container_id = await _create_docker_container()
            except Exception as e:
                print(f"[WS] Docker unavailable for new session, falling back to local execution: {e}")
                docker_mgr = None
                container_id = None
            if not LOCAL_MODE and container_id:
                register_session(harness_session.id, docker_mgr, container_id, user_id)
            # Rebuild components with new container
            tools, guardrails, analyzer, policy, loop = _build_components()
            loop.on_event(emit_to_ws)
            _known_files.clear()
            cancel_event.clear()
            await emit_to_ws("session.created", session_id=harness_session.id)

        elif msg_type == "task.submit":
            task_text = raw.get("content", "")
            if not task_text:
                return
            # If a session_id is provided, load that session first (continue history)
            load_id = raw.get("session_id", "")
            if load_id and not LOCAL_MODE:
                loaded = await _load_session_from_db(load_id, user_id, get_db)
                if loaded is not None:
                    harness_session = loaded
                    await emit_to_ws("session.created", session_id=harness_session.id)
            result, buffered = await run_task_pumped(task_text)
            if result is None:
                # Error or cancellation — the loop stays open for re-submit
                pass
            else:
                await _save_and_notify()
            for d in buffered:
                await handle_message(d)

        elif msg_type == "session.load":
            load_id = raw.get("session_id", "")
            if not LOCAL_MODE and load_id:
                await _save_and_notify()  # save current before switching
                loaded = await _load_session_from_db(load_id, user_id, get_db)
                if loaded is not None:
                    harness_session = loaded
                    await emit_to_ws("session.created", session_id=harness_session.id)
                    # Send loaded messages for display
                    for msg in harness_session.messages:
                        if msg.role in ("user", "assistant", "system", "tool"):
                            await emit_to_ws("llm.response",
                                content=f"[{msg.role}] {msg.content[:500]}",
                                tool_calls=[],
                            )
                    await emit_to_ws("session.complete", session_id=harness_session.id)

        elif msg_type == "session.cancel":
            # No turn in flight (a running turn is cancelled by the pump)
            cancel_event.set()
            await emit_to_ws("session.error", message="Cancelled by user")

        elif msg_type == "files.list":
            if not LOCAL_MODE and docker_mgr is not None and container_id is not None:
                try:
                    result = await docker_mgr.exec(
                        container_id,
                        "find /workspace -type f -printf '%p\t%s\t%TY-%Tm-%TdT%TH:%TM\n' 2>/dev/null",
                        timeout=10,
                    )
                    files = []
                    for line in result.stdout.strip().split("\n"):
                        if not line:
                            continue
                        parts = line.split("\t")
                        if len(parts) >= 3:
                            p = parts[0].replace("/workspace/", "", 1)
                            if p == "/workspace" or not p:
                                continue
                            files.append({"name": p, "size": int(parts[1]), "modified": parts[2]})
                    files.sort(key=lambda f: (("/" in f["name"]), f["name"]))
                    await emit_to_ws("files.list", files=files)
                except Exception:
                    await emit_to_ws("files.list", files=[])
            else:
                await emit_to_ws("files.list", files=_list_local_files())

        elif msg_type == "files.upload":
            filepath = raw.get("path", "")
            fb64 = raw.get("content", "")
            if not filepath or not fb64:
                return
            if LOCAL_MODE or docker_mgr is None or container_id is None:
                err = _upload_local(filepath, fb64)
            else:
                err = await _upload_to_container(docker_mgr, container_id, filepath, fb64)
            if err:
                print(f"[WS] Upload failed: {err}")
            else:
                await emit_to_ws("file.created", path=filepath)

        elif msg_type == "files.delete":
            filepath = raw.get("path", "")
            if not filepath:
                return
            if LOCAL_MODE or docker_mgr is None or container_id is None:
                err = _delete_local(filepath)
            else:
                err = await _delete_from_container(docker_mgr, container_id, filepath)
            if err:
                print(f"[WS] Delete failed: {err}")
            else:
                await emit_to_ws("files.deleted", path=filepath)

        elif msg_type == "files.download":
            filepath = raw.get("path", "")
            if not filepath:
                return
            if LOCAL_MODE or docker_mgr is None or container_id is None:
                content, err = _read_local(filepath)
                if err:
                    await emit_to_ws("files.content", path=filepath, content="", error=err)
                else:
                    await emit_to_ws("files.content", path=filepath, content=content)
                return
            safe_path = container_path(filepath)
            if safe_path is None:
                await emit_to_ws("files.content", path=filepath, content="", error="Path not allowed")
                return
            try:
                result = await docker_mgr.exec(container_id, f"cat {shlex.quote(safe_path)}", timeout=10)
                if result.exit_code == 0:
                    content = result.stdout
                    await emit_to_ws("files.content", path=filepath, content=content)
                else:
                    await emit_to_ws("files.content", path=filepath, content="", error="File not found")
            except Exception:
                await emit_to_ws("files.content", path=filepath, content="", error="Read failed")

        elif msg_type in ("guardrail.approve", "guardrail.reject"):
            # Handled inside run_one_turn's AWAITING_HUMAN sub-loop via the
            # pump; if received here (outside a turn), ignore silently
            pass

    # ---- Replay messages deferred during bootstrap (files.upload etc.) ----
    # The frontend sends attachment uploads before task.submit; they must land
    # in the workspace before the first turn runs, or the agent's read of the
    # just-uploaded file fails with "No such file or directory".
    for d in deferred:
        print(f"[WS] Replaying deferred: {d.get('type', '')}")
        await handle_message(d)

    buffered: list[dict] = []
    # ---- First task (from bootstrap) ----
    if task_content:
        if is_resuming:
            await emit_to_ws("session.created", session_id=harness_session.id)
        try:
            result, buffered = await run_task_pumped(task_content)
        except WebSocketDisconnect:
            await _destroy_docker_container()
            return
        if result is None:
            if not cancel_event.is_set():
                # Unrecoverable first-turn failure — close the session
                try: await websocket.close()
                except Exception: pass
                return
            # Cancelled first turn — keep the session open for re-submit
        else:
            await _save_and_notify()
    else:
        # No initial task (loaded session without submit) — send created event
        if harness_session.state == State.IDLE:
            await emit_to_ws("session.created", session_id=harness_session.id)
        elif len(harness_session.messages) > 0:
            await emit_to_ws("session.created", session_id=harness_session.id)

    # ---- Replay messages buffered during the first turn ----
    for d in buffered:
        print(f"[WS] Replaying buffered: {d.get('type', '')}")
        await handle_message(d)

    # ---- Main message loop ----

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            except asyncio.TimeoutError:
                continue

            msg_type = raw.get("type", "")
            print(f"[WS] Received: {msg_type}")
            await handle_message(raw)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # Save on disconnect
        await _save_and_notify()
        if runner is not None and not runner.done():
            runner.cancel()
            try:
                await runner
            except (asyncio.CancelledError, Exception):
                pass
        await _destroy_docker_container()


async def _wait_for_human_response(
    queue: asyncio.Queue,
    cancel_event: asyncio.Event,
) -> dict | None:
    """Wait for guardrail approval/rejection or cancellation.

    Messages arrive via ``queue`` — the pump in the main loop is the single
    websocket reader while a turn runs.
    """
    try:
        while not cancel_event.is_set():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if msg.get("type") in ("guardrail.approve", "guardrail.reject", "session.cancel"):
                return msg
        return None
    except Exception:
        return None
