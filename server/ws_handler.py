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
from harness.models import State, Message as PydanticMessage, Session as PydanticSession, ConfigData
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
from server.api.config_routes import get_user_api_key, get_user_config
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


def _build_default_tool_registry(docker_mgr=None, container_id=None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ExecuteShellTool(docker_mgr=docker_mgr, container_id=container_id))
    registry.register(RunTestsTool(docker_mgr=docker_mgr, container_id=container_id))
    registry.register(SearchCodeTool())
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
                payload: dict = {"content": msg.content}
                if msg.tool_call_id:
                    payload["tool_call_id"] = msg.tool_call_id
                db_s.add(DBMessage(
                    session_id=uuid.UUID(harness_session.id),
                    type=msg.role,
                    payload=payload,
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
            select(DBSession).where(
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
            content = db_msg.payload.get("content", "") if db_msg.payload else ""
            pydantic_session.messages.append(PydanticMessage(
                role=db_msg.type,
                content=content,
                tool_call_id=db_msg.payload.get("tool_call_id") if db_msg.payload else None,
            ))
    return pydantic_session


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

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

    # ---- Wait for first message (task.submit or session.load) ----
    try:
        raw = await websocket.receive_json()
    except WebSocketDisconnect:
        return

    msg_type = raw.get("type", "")
    if msg_type not in ("task.submit", "session.load"):
        await websocket.send_json({"type": "session.error", "message": "Expected task.submit or session.load"})
        await websocket.close()
        return

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
        user_id = "local"
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
        # task.submit as first message — create fresh session
        task_content = raw.get("content", "")
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
            tools = _build_default_tool_registry(docker_mgr=docker_mgr, container_id=container_id)
        guardrails = GuardrailEngine(
            sandbox_root=config.sandbox_root,
            whitelist_extra=config.command_whitelist_extra,
        )
        analyzer = FeedbackAnalyzer()
        policy = RetryPolicy(max_retries=config.max_retries)
        loop = AgentLoop(tools, guardrails, analyzer, policy)
        return tools, guardrails, analyzer, policy, loop

    # Create Docker container for the initial session
    container_id = await _create_docker_container()
    if not LOCAL_MODE and container_id:
        register_session(harness_session.id, docker_mgr, container_id, user_id)
    tools, guardrails, analyzer, policy, loop = _build_components()

    async def _create_llm():
        llm_override = getattr(app_state, 'ws_llm_override', None)
        if llm_override is not None:
            return llm_override
        elif api_key:
            return _create_llm_from_config(config, api_key)
        else:
            return MockLLMAdapter([])

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
                    _wait_for_human_response(websocket, cancel_event)
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
                    cancel_event.set()
                    await emit_to_ws("session.error", message="Cancelled by user")
                    return None
                harness_session = await loop.resume(harness_session, await _create_llm())

            return harness_session
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

    # ---- First task (from bootstrap) ----
    if task_content:
        harness_session = await run_one_turn(task_content)
        if harness_session is None:
            try: await websocket.close()
            except Exception: pass
            return
        await _save_and_notify()
    else:
        # No initial task (loaded session without submit) — send created event
        if harness_session.state == State.IDLE:
            await emit_to_ws("session.created", session_id=harness_session.id)
        elif len(harness_session.messages) > 0:
            await emit_to_ws("session.created", session_id=harness_session.id)

    # ---- Main message loop ----
    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            except asyncio.TimeoutError:
                continue

            msg_type = raw.get("type", "")
            print(f"[WS] Received: {msg_type}")

            if msg_type == "session.new":
                # Save current session, then start a fresh one
                await _save_and_notify()
                harness_session = PydanticSession(id=str(uuid.uuid4()), task="", state=State.IDLE)
                await _destroy_docker_container()
                container_id = await _create_docker_container()
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
                    continue
                # If a session_id is provided, load that session first (continue history)
                load_id = raw.get("session_id", "")
                if load_id and not LOCAL_MODE:
                    loaded = await _load_session_from_db(load_id, user_id, get_db)
                    if loaded is not None:
                        harness_session = loaded
                        await emit_to_ws("session.created", session_id=harness_session.id)
                cancel_event.clear()
                harness_session = await run_one_turn(task_text)
                if harness_session is None:
                    continue
                await _save_and_notify()

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
                if runner and not runner.done():
                    cancel_event.set()
                    runner.cancel()
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

            elif msg_type == "files.download":
                filepath = raw.get("path", "")
                if not filepath:
                    continue
                safe_path = os.path.normpath(os.path.join("/workspace", filepath.lstrip("/")))
                if not safe_path.startswith("/workspace/"):
                    continue
                if not LOCAL_MODE and docker_mgr is not None and container_id is not None:
                    try:
                        result = await docker_mgr.exec(container_id, f"cat {safe_path}", timeout=10)
                        if result.exit_code == 0:
                            content = result.stdout
                            await emit_to_ws("files.content", path=filepath, content=content)
                        else:
                            await emit_to_ws("files.content", path=filepath, content="", error="File not found")
                    except Exception:
                        await emit_to_ws("files.content", path=filepath, content="", error="Read failed")

            elif msg_type in ("guardrail.approve", "guardrail.reject"):
                # Handled inside run_one_turn's AWAITING_HUMAN sub-loop;
                # if received here (outside that sub-loop), ignore silently
                pass

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
    websocket: WebSocket,
    cancel_event: asyncio.Event,
) -> dict | None:
    """Wait for guardrail approval/rejection or cancellation."""
    try:
        while not cancel_event.is_set():
            msg = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
            if msg.get("type") in ("guardrail.approve", "guardrail.reject", "session.cancel"):
                return msg
        return None
    except (asyncio.TimeoutError, WebSocketDisconnect, Exception):
        return None
