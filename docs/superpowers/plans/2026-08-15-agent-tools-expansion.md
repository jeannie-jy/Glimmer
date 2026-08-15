# Agent 工具扩展 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Glimmer agent 新增 6 项能力：`list_files`、快照回滚（`restore_file`）、`git` 只读三件套、`web_fetch`（SSRF 防护）、secret scan 与 egress 护栏，并同步更新 README 与 About/Guide/Learn。

**Architecture:** 所有新工具实现 `harness.tools.registry.Tool` 接口（name/description/parameters/async execute → ToolResult），与现有工具一样支持本地/Render 进程内 + Docker 沙箱双路径；`web_fetch` 恒为主机侧（沙箱容器 network_mode=none）；共享 SSRF 校验器放 `harness/netguard.py`（工具与护栏引擎共用）；secret scan 为护栏引擎第四层（命中 ASK_HUMAN），egress 检查拦 execute_shell 命令中的内网 URL（BLOCK，先于 whitelist）。

**Tech Stack:** Python 3.12 + FastAPI（后端，无新依赖——httpx 已在 requirements.txt；git 经 apt 装入 app 镜像）；React 18 + TS 前端仅改宣传页文案。

**Spec:** `docs/superpowers/specs/2026-08-15-agent-tools-expansion-design.md`

## Global Constraints

- Python ≥3.12；`ToolResult(tool_name, exit_code=0, stdout="", stderr="", duration_ms, structured: dict | None = None)`；`ToolCall(id, name, arguments)`；`GuardResult(action, layer, reason)`；`GuardAction ∈ ALLOW/BLOCK/ASK_HUMAN`。
- 工具双路径纪律：`docker_mgr and container_id` 为真走沙箱（docker_mgr.exec 返回 `ExecResult(exit_code, stdout, stderr)`，命令经 `shlex.quote`）；否则进程内（workspace 根为 `_workspace_root()` 或 cwd）。
- 护栏引擎统一在 `GuardrailEngine.check(tool_call)` 接线（loop.py EXECUTING 分支已处理三路：BLOCK → guardrail.pending(action="blocked") → AWAITING_HUMAN；ASK_HUMAN → guardrail.pending(action="ask_human")；ALLOW → dispatch）。
- 关键事实：LLM 消息上下文只含 stdout/stderr 截断（loop.py:339），**工具的实质输出必须进 stdout**；`tool.result` 事件原本不带 structured——Task 1 给它加上（`structured=result.structured`），否则新工具 structured 数据到不了前端。
- 测试纪律（TDD）：每个新模块先写失败测试（`asyncio.run(...)` 模式，FakeDocker = 带 `async exec` 返回 `SimpleNamespace(exit_code, stdout, stderr)` 的类），验证 RED 后实现，验证 GREEN，全量回归后提交；**单测不得触真实网络**——DNS 一律 monkeypatch `socket.getaddrinfo`，httpx 一律替换 `AsyncClient`；前端改源码后必须 `cd web && npm run build` 并提交 server/static 产物。
- 基线：pytest 192 通过、vitest 9 通过；任何提交不得降低此基线。
- 提交信息用中文，结尾加 `Co-Authored-By: Claude <noreply@anthropic.com>`；直接在 main 提交推送（Render 自动部署）。

---

### Task 1: `list_files` 工具

**Files:**
- Create: `harness/tools/list_files.py`
- Create: `tests/unit/test_list_files.py`
- Create: `tests/integration/test_ws_new_tools.py`（本任务含测试 1；后续任务追加）
- Modify: `server/ws_handler.py`（import + `_build_default_tool_registry` 注册）
- Modify: `harness/loop.py`（tool.result emit 加 structured）
- Modify: `harness/guardrails/engine.py`（list_files path 校验）
- Modify: `harness/models.py`（enabled_tools 默认值加 `"list_files"`）
- Modify: `server/api/config_routes.py`（enabled_tools 默认值加 `"list_files"`）

**Interfaces:**
- Consumes: `Tool` ABC（`harness/tools/registry.py`）、`ToolResult`、`GuardResult/GuardAction`（`harness/models.py`）、`_workspace_root()`（`server/ws_handler.py:261`）。
- Produces: `ListFilesTool(workspace_root: Path | None = None, docker_mgr=None, container_id=None)`，`execute(arguments) -> ToolResult`，`structured = {"files": [{"name", "size", "modified"}]}`，stdout 为文件相对路径列表（每行一个，超 300 条截断注明）；`tool.result` 事件从本任务起带 `structured` 字段（后续任务依赖）。

- [ ] **Step 1: 写失败测试**

Create `tests/unit/test_list_files.py`:

```python
"""Unit tests for the ListFilesTool."""
import asyncio
from types import SimpleNamespace

from harness.tools.list_files import ListFilesTool


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


def test_lists_files_with_depth_and_skip_dirs(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("y")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("z")

    tool = ListFilesTool(workspace_root=tmp_path)
    result = asyncio.run(tool.execute({}))

    assert result.exit_code == 0
    names = [f["name"] for f in result.structured["files"]]
    assert "a.py" in names
    assert "sub/b.py" in names
    assert "node_modules/junk.js" not in names
    assert "sub/b.py" in result.stdout  # LLM sees stdout, not structured


def test_max_depth_bounds_recursion(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "c.txt").write_text("deep")

    tool = ListFilesTool(workspace_root=tmp_path)
    result = asyncio.run(tool.execute({"max_depth": 1}))

    assert result.exit_code == 0
    assert result.structured["files"] == []


def test_path_traversal_rejected(tmp_path):
    (tmp_path / "ws").mkdir()
    (tmp_path / "secret.txt").write_text("s")
    tool = ListFilesTool(workspace_root=tmp_path / "ws")
    result = asyncio.run(tool.execute({"path": ".."}))

    assert result.exit_code == 1
    assert "outside" in (result.stderr or "").lower()


def test_docker_mode_runs_find(tmp_path):
    docker = FakeDocker()
    tool = ListFilesTool(docker_mgr=docker, container_id="c1", workspace_root=tmp_path)
    result = asyncio.run(tool.execute({"max_depth": 2}))

    assert "find" in docker.calls[0]
    assert "maxdepth" in docker.calls[0]
    assert result.exit_code == 0
```

- [ ] **Step 2: 运行测试验证 RED**

Run: `python -m pytest tests/unit/test_list_files.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.tools.list_files'`

- [ ] **Step 3: 实现 `harness/tools/list_files.py`**

```python
"""Directory listing tool — local or sandbox-container aware."""
import shlex
import time
from datetime import datetime
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult

# Directories never listed: dependency trees and harness internals. Mirrors
# the server's local file-list skip set so agent-visible structure is clean.
SKIP_DIRS = {
    ".git", ".harness", ".claude", "node_modules", "__pycache__", ".venv", "venv",
    "harness", "server", "web", "tests", "docs",
    ".github", ".agents", ".superpowers", ".pytest_cache", "dist", "build",
}

MAX_FILES_IN_STDOUT = 300


class ListFilesTool(Tool):
    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._workspace_root = workspace_root

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files in a directory of the workspace (bounded depth; excludes dependency/tooling directories). Use before reading files to learn the project structure."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to list (default: workspace root)"},
                "max_depth": {"type": "integer", "description": "Maximum recursion depth (default: 3, max: 6)"},
            },
            "required": [],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        raw_path = arguments.get("path", "")
        max_depth = min(int(arguments.get("max_depth", 3)), 6)

        if self._docker_mgr and self._container_id:
            return await self._execute_docker(raw_path, max_depth, start)

        root = (self._workspace_root or Path.cwd()).resolve()
        target = (root / raw_path).resolve() if raw_path else root
        if not (target == root or target.is_relative_to(root)):
            return ToolResult(tool_name="list_files", exit_code=1, stdout="",
                stderr=f"Path outside workspace: {raw_path}",
                duration_ms=int((time.time() - start) * 1000))
        if not target.is_dir():
            return ToolResult(tool_name="list_files", exit_code=1, stdout="",
                stderr=f"Not a directory: {raw_path}",
                duration_ms=int((time.time() - start) * 1000))

        base_depth = len(target.relative_to(root).parts)
        files = []
        for p in sorted(target.rglob("*")):
            if not p.is_file() or p.is_symlink():
                continue
            rel = p.relative_to(root)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if len(rel.parts) - base_depth > max_depth:
                continue
            st = p.stat()
            files.append({
                "name": rel.as_posix(),
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M"),
            })
        return self._render(files, start)

    def _render(self, files, start) -> ToolResult:
        stdout = "\n".join(f["name"] for f in files[:MAX_FILES_IN_STDOUT])
        if len(files) > MAX_FILES_IN_STDOUT:
            stdout += f"\n... ({len(files) - MAX_FILES_IN_STDOUT} more files)"
        if not stdout:
            stdout = "(empty directory)"
        return ToolResult(tool_name="list_files", exit_code=0,
            stdout=stdout, structured={"files": files},
            duration_ms=int((time.time() - start) * 1000))

    async def _execute_docker(self, raw_path, max_depth, start) -> ToolResult:
        clean = (raw_path or "").replace("\\", "/").lstrip("/")
        safe = "/workspace" + (f"/{clean}" if clean else "")
        cmd = f"find {shlex.quote(safe)} -maxdepth {max_depth} -type f -printf '%P\\t%s\\t%TY-%Tm-%TdT%TH:%TM\\n' 2>/dev/null"
        result = await self._docker_mgr.exec(self._container_id, cmd, timeout=10)
        if result.exit_code not in (0, 1):
            return ToolResult(tool_name="list_files", exit_code=1, stdout="",
                stderr=result.stderr or f"find failed on {safe}",
                duration_ms=int((time.time() - start) * 1000))
        files = []
        for line in (result.stdout or "").splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            name = f"{clean}/{parts[0]}" if clean else parts[0]
            try:
                size = int(parts[1])
            except ValueError:
                continue
            files.append({"name": name, "size": size, "modified": parts[2]})
        files.sort(key=lambda f: f["name"])
        return self._render(files, start)
```

- [ ] **Step 4: 运行测试验证 GREEN**

Run: `python -m pytest tests/unit/test_list_files.py -q`
Expected: 4 passed

- [ ] **Step 5: 接线（registry + 护栏 + enabled_tools + tool.result structured）**

1. `server/ws_handler.py` 顶部 import 区（`from harness.tools.shell import ...` 之后）加：

```python
from harness.tools.list_files import ListFilesTool
```

2. `server/ws_handler.py` `_build_default_tool_registry`（57-64 行）加一行（SearchCodeTool 之后）：

```python
    registry.register(ListFilesTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root))
```

3. `harness/loop.py` 的 `tool.result` emit（346-351 行）加 structured：

```python
                    await self._emit(
                        "tool.result",
                        tool_name=result.tool_name, exit_code=result.exit_code,
                        stdout=result.stdout[:2000], stderr=result.stderr[:1000],
                        duration_ms=result.duration_ms,
                        structured=result.structured,
                    )
```

4. `harness/guardrails/engine.py`，`check()` 内 run_tests 检查之后（33-34 行之后）加：

```python
        # Layer 1 also: Path sandbox for list_files path
        if tool_call.name == "list_files":
            raw_path = tool_call.arguments.get("path") or ""
            if raw_path:
                result = self._path_sandbox.validate(raw_path, "read")
                if result.action != GuardAction.ALLOW:
                    return result
```

5. `harness/models.py` 的 `enabled_tools` 默认列表（约 138 行）与 `server/api/config_routes.py`（约 60 行）各加 `"list_files"`（保持既有顺序，加在 `search_code` 之后）。

- [ ] **Step 6: 集成测试（ws 流触发真实工具）**

Create `tests/integration/test_ws_new_tools.py`:

```python
"""Integration tests: new tools reachable through the WebSocket agent loop."""
from pathlib import Path

from fastapi.testclient import TestClient

from harness.llm.mock import MockLLMAdapter
from harness.models import LLMResponse, ToolCall
from server.main import create_app
from server.ws_handler import configure


def _ok(text: str = "") -> LLMResponse:
    return LLMResponse(content=text, tool_calls=[], stop_reason="complete")


def _tool_use(name: str, arguments: dict) -> LLMResponse:
    return LLMResponse(
        content="", tool_calls=[ToolCall(id=f"tc-{name}", name=name, arguments=arguments)],
        stop_reason="tool_use",
    )


def _make_client(workspace: Path, monkeypatch, responses: list[LLMResponse]) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)
    monkeypatch.chdir(workspace)
    app = create_app(project_root=workspace)
    configure(app, llm_override=MockLLMAdapter(responses))
    return TestClient(app)


def _receive_until(ws, msg_type: str, max_msgs=60) -> dict:
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("type") == msg_type:
            return msg
    raise AssertionError(f"Never received {msg_type!r}")


def test_list_files_via_agent_loop(tmp_path, monkeypatch):
    (tmp_path / "hello.txt").write_text("hi")
    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("list_files", {}),
        _ok("Listed."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "List the workspace"})
        result = _receive_until(ws, "tool.result")
        assert result["tool_name"] == "list_files"
        assert result["exit_code"] == 0
        assert "hello.txt" in result["stdout"]
        assert any(f["name"] == "hello.txt" for f in (result.get("structured") or {}).get("files", []))
        _receive_until(ws, "session.complete")
```

Run: `python -m pytest tests/integration/test_ws_new_tools.py -q`
Expected: 1 passed

- [ ] **Step 7: 全量回归 + 提交**

Run: `python -m pytest -q`
Expected: 197 passed（192 基线 + 4 单元 + 1 集成），无回归

```bash
git add harness/tools/list_files.py tests/unit/test_list_files.py tests/integration/test_ws_new_tools.py server/ws_handler.py harness/loop.py harness/guardrails/engine.py harness/models.py server/api/config_routes.py
git commit -m "feat: 新增 list_files 工具（目录浏览，深度限制+跳过名单，双沙箱路径）

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

---

### Task 2: 快照回滚（`SnapshotStore` + `restore_file`）

**Files:**
- Create: `harness/tools/snapshots.py`（SnapshotStore + RestoreFileTool）
- Create: `tests/unit/test_snapshots.py`
- Modify: `harness/tools/file_ops.py`（WriteFileTool 覆盖前快照）
- Modify: `server/ws_handler.py`（快照目录创建 + 传入 WriteFileTool/RestoreFileTool + enabled_tools）
- Modify: `harness/guardrails/engine.py`（restore_file path 校验）
- Modify: `harness/models.py` + `server/api/config_routes.py`（加 `"restore_file"`）
- Modify: `tests/integration/test_ws_new_tools.py`（追加测试 2）

**Interfaces:**
- Consumes: `WriteFileTool(docker_mgr, container_id, workspace_root)` 现有构造；`_sandbox_path(path)`（`harness/tools/file_ops.py:10`）。
- Produces:
  - `SnapshotStore(base_dir: Path)` — `save(path: str, content: str) -> None`（栈式，key=规范化相对路径）、`load(path: str) -> str | None`（取最新；无快照返回 None）。
  - `RestoreFileTool(docker_mgr=None, container_id=None, workspace_root=None, snapshots=None)`。
  - `WriteFileTool` 新可选参数 `snapshots: SnapshotStore | None = None`（默认 None 保持向后兼容）。
  - `SNAPSHOT_DIR` 环境变量：覆盖快照店基目录（测试专用逃生口，README 不宣传）。

- [ ] **Step 1: 写失败测试**

Create `tests/unit/test_snapshots.py`:

```python
"""Unit tests for the snapshot store and restore_file tool."""
import asyncio
from types import SimpleNamespace

from harness.tools.snapshots import SnapshotStore, RestoreFileTool, snapshot_key


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


def test_snapshot_key_rejects_traversal():
    assert snapshot_key("../etc/passwd") is None
    assert snapshot_key("a/../../b") is None
    assert snapshot_key("..") is None
    assert snapshot_key("src/app.py") == "src/app.py"
    assert snapshot_key("/abs/path") == "abs/path"


def test_store_is_a_stack_latest_wins(tmp_path):
    store = SnapshotStore(tmp_path)
    store.save("a.txt", "v1")
    store.save("a.txt", "v2")
    assert store.load("a.txt") == "v2"
    assert store.load("missing.txt") is None


def test_restore_file_local(tmp_path):
    store = SnapshotStore(tmp_path / "snaps")
    store.save("a.txt", "original")
    (tmp_path / "a.txt").write_text("broken")

    tool = RestoreFileTool(workspace_root=tmp_path, snapshots=store)
    result = asyncio.run(tool.execute({"path": "a.txt"}))

    assert result.exit_code == 0
    assert (tmp_path / "a.txt").read_text() == "original"


def test_restore_file_no_snapshot_errors(tmp_path):
    tool = RestoreFileTool(workspace_root=tmp_path, snapshots=SnapshotStore(tmp_path / "s"))
    result = asyncio.run(tool.execute({"path": "a.txt"}))
    assert result.exit_code == 1
    assert "No snapshot" in result.stderr


def test_restore_file_docker_uses_base64_write(tmp_path):
    store = SnapshotStore(tmp_path / "snaps")
    store.save("a.txt", "original")
    docker = FakeDocker()

    tool = RestoreFileTool(docker_mgr=docker, container_id="c1", workspace_root=tmp_path, snapshots=store)
    result = asyncio.run(tool.execute({"path": "a.txt"}))

    assert result.exit_code == 0
    assert any("base64 -d" in c for c in docker.calls)


def test_write_file_snapshots_then_restore(tmp_path):
    from harness.tools.file_ops import WriteFileTool

    (tmp_path / "a.txt").write_text("v1")
    store = SnapshotStore(tmp_path / "snaps")
    writer = WriteFileTool(workspace_root=tmp_path, snapshots=store)
    assert asyncio.run(writer.execute({"path": "a.txt", "content": "v2"})).exit_code == 0
    assert (tmp_path / "a.txt").read_text() == "v2"

    restorer = RestoreFileTool(workspace_root=tmp_path, snapshots=store)
    assert asyncio.run(restorer.execute({"path": "a.txt"})).exit_code == 0
    assert (tmp_path / "a.txt").read_text() == "v1"
```

- [ ] **Step 2: 运行测试验证 RED**

Run: `python -m pytest tests/unit/test_snapshots.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.tools.snapshots'`

- [ ] **Step 3: 实现 `harness/tools/snapshots.py`**

```python
"""Snapshot store + restore tool for write_file overwrite protection.

Snapshots live OUTSIDE the agent-accessible workspace (base dir injected by
the server): ~/.harness/snapshots/{session_id} in-process, or the host-side
WORKSPACE_ROOT/.harness-snapshots/{session_id} in Docker mode (the container
only mounts the user workspace, so it cannot see or tamper with the store).
"""
import base64
import posixpath
import shlex
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult


def snapshot_key(path: str) -> str | None:
    """Normalize a tool-supplied path into a safe snapshot-store key.

    Returns None for paths escaping via '..' (the path guardrails reject
    those anyway; the store never trusts them).
    """
    clean = path.replace("\\", "/").lstrip("/")
    if not clean or clean == ".." or clean.startswith("../") or "/../" in clean:
        return None
    return clean


class SnapshotStore:
    """Per-session stack of pre-overwrite file contents."""

    def __init__(self, base_dir: Path):
        self._base = base_dir

    def save(self, path: str, content: str) -> None:
        key = snapshot_key(path)
        if key is None:
            return
        d = self._base / key
        d.mkdir(parents=True, exist_ok=True)
        seq = sum(1 for _ in d.iterdir())
        (d / f"{seq:04d}").write_text(content, encoding="utf-8")

    def load(self, path: str) -> str | None:
        key = snapshot_key(path)
        if key is None:
            return None
        d = self._base / key
        if not d.is_dir():
            return None
        snaps = sorted(d.iterdir())
        if not snaps:
            return None
        return snaps[-1].read_text(encoding="utf-8")


class RestoreFileTool(Tool):
    """Restore a file to its content before the most recent write_file
    overwrite. The snapshot store location is injected by the server and is
    never exposed as a tool parameter."""

    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None,
                 snapshots: SnapshotStore | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._workspace_root = workspace_root
        self._snapshots = snapshots

    @property
    def name(self) -> str:
        return "restore_file"

    @property
    def description(self) -> str:
        return "Restore a file to its content before the most recent write_file overwrite. Use after an unwanted edit."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path of the file to restore"},
            },
            "required": ["path"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        path = arguments["path"]
        if self._snapshots is None:
            return ToolResult(tool_name="restore_file", exit_code=1, stdout="",
                stderr="Snapshots are not enabled for this session",
                duration_ms=int((time.time() - start) * 1000))
        content = self._snapshots.load(path)
        if content is None:
            return ToolResult(tool_name="restore_file", exit_code=1, stdout="",
                stderr=f"No snapshot for: {path}",
                duration_ms=int((time.time() - start) * 1000))

        try:
            if self._docker_mgr and self._container_id:
                from harness.tools.file_ops import _sandbox_path
                spath = _sandbox_path(path)
                parent = posixpath.dirname(spath)
                await self._docker_mgr.exec(self._container_id, f"mkdir -p {shlex.quote(parent)}", timeout=5)
                encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
                result = await self._docker_mgr.exec(self._container_id,
                    f"echo {shlex.quote(encoded)} | base64 -d > {shlex.quote(spath)}", timeout=10)
                if result.exit_code != 0:
                    return ToolResult(tool_name="restore_file", exit_code=1, stdout="",
                        stderr=result.stderr or "Restore failed",
                        duration_ms=int((time.time() - start) * 1000))
            else:
                p = self._workspace_root / path if self._workspace_root else Path(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
        except Exception as e:
            return ToolResult(tool_name="restore_file", exit_code=1, stdout="", stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
        return ToolResult(tool_name="restore_file", exit_code=0,
            stdout=f"Restored {len(content)} bytes to {path}",
            duration_ms=int((time.time() - start) * 1000))
```

- [ ] **Step 4: 运行测试验证 GREEN**

Run: `python -m pytest tests/unit/test_snapshots.py -q`
Expected: 6 passed

- [ ] **Step 5: WriteFileTool 覆盖前快照**

In `harness/tools/file_ops.py`：
1. `WriteFileTool.__init__`（89-94 行）改为：

```python
    def __init__(self, docker_mgr=None, container_id=None, workspace_root: Path | None = None,
                 snapshots=None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        # Local mode: resolve relative paths under the workspace root
        # (WORKSPACE_ROOT) when set; otherwise relative to the process cwd.
        self._workspace_root = workspace_root
        # Pre-overwrite snapshot store (harness.tools.snapshots.SnapshotStore).
        # Duck-typed reference to avoid a circular import.
        self._snapshots = snapshots
```

2. Docker 写路径（121-128 行 `spath = _sandbox_path(path)` 之后、`import base64` 之前）加：

```python
                # Snapshot the current content before overwriting.
                if self._snapshots is not None:
                    prev = await self._docker_mgr.exec(self._container_id, f"cat {shlex.quote(spath)}", timeout=5)
                    if prev.exit_code == 0:
                        self._snapshots.save(path, prev.stdout)
```

3. 本地写路径（141-142 行 `p = ...` 之后、`p.parent.mkdir` 之前）加：

```python
            # Snapshot before overwriting an existing file so restore_file
            # can roll the change back.
            if self._snapshots is not None and p.exists():
                self._snapshots.save(path, p.read_text(encoding="utf-8", errors="replace"))
```

- [ ] **Step 6: 运行测试验证 GREEN（含联动测试）**

Run: `python -m pytest tests/unit/test_snapshots.py tests/unit/test_file_ops.py -q`
Expected: 6 passed + 既有 file_ops 测试全绿

- [ ] **Step 7: ws_handler 接线（快照目录注入 + 注册）**

In `server/ws_handler.py`：
1. import 加：

```python
from harness.tools.snapshots import SnapshotStore, RestoreFileTool
```

2. `_build_default_tool_registry` 签名加 `snapshots` 参数，WriteFileTool 传 snapshots，SearchCodeTool 之后注册 RestoreFileTool：

```python
def _build_default_tool_registry(docker_mgr=None, container_id=None, workspace_root: Path | None = None, snapshots=None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ReadFileTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root))
    registry.register(WriteFileTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root, snapshots=snapshots))
    registry.register(ExecuteShellTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
    registry.register(RunTestsTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
    registry.register(SearchCodeTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
    registry.register(ListFilesTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root))
    registry.register(RestoreFileTool(docker_mgr=docker_mgr, container_id=container_id, workspace_root=workspace_root, snapshots=snapshots))
    return registry
```

3. `_build_components`（638-655 行）改为（自定义 `ws_tool_registry` 注入路径不受影响——仅默认构建路径使用 snapshots）：

```python
    def _build_components():
        # Snapshot store lives OUTSIDE the agent-accessible workspace:
        # in-process modes default to ~/.harness/snapshots (Render's
        # /workspace IS the workspace, so it must not host the store);
        # Docker mode uses a host-side WORKSPACE_ROOT sibling the container
        # never mounts. SNAPSHOT_DIR overrides for tests.
        env_snap = os.environ.get("SNAPSHOT_DIR")
        if env_snap:
            snap_base = Path(env_snap) / harness_session.id
        elif container_id:
            snap_base = Path(os.environ.get("WORKSPACE_ROOT", "/workspace")) / ".harness-snapshots" / harness_session.id
        else:
            snap_base = Path.home() / ".harness" / "snapshots" / harness_session.id
        snapshots = SnapshotStore(snap_base)
        tools = getattr(app_state, 'ws_tool_registry', None)
        if tools is None:
            tools = _build_default_tool_registry(docker_mgr=docker_mgr, container_id=container_id,
                                                 workspace_root=_workspace_root(), snapshots=snapshots)
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
```

4. `harness/models.py` + `server/api/config_routes.py` 各加 `"restore_file"`（`"list_files"` 之后）。

- [ ] **Step 8: 护栏接线**

In `harness/guardrails/engine.py`，list_files 检查之后加：

```python
        # Layer 1 also: Path sandbox for restore_file path
        if tool_call.name == "restore_file":
            result = self._path_sandbox.validate(tool_call.arguments.get("path", ""), "write")
            if result.action != GuardAction.ALLOW:
                return result
```

- [ ] **Step 9: 集成测试（写入→覆盖→回滚经 agent 循环）**

Append to `tests/integration/test_ws_new_tools.py`:

```python
def test_snapshot_and_restore_via_agent_loop(tmp_path, monkeypatch):
    (tmp_path / "x.txt").write_text("v1")
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / ".snaps"))
    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("write_file", {"path": "x.txt", "content": "v2"}),
        _tool_use("restore_file", {"path": "x.txt"}),
        _ok("Restored."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "Overwrite then restore x.txt"})
        _receive_until(ws, "tool.result")  # write_file
        _receive_until(ws, "tool.result")  # restore_file
        _receive_until(ws, "session.complete")
    assert (tmp_path / "x.txt").read_text() == "v1"
    assert list((tmp_path / ".snaps").glob("*"))  # per-session snapshot dir exists
```

Run: `python -m pytest tests/integration/test_ws_new_tools.py -q`
Expected: 2 passed

- [ ] **Step 10: 全量回归 + 提交**

Run: `python -m pytest -q`
Expected: 204 passed（197 + 6 单元 + 1 集成），无回归

```bash
git add harness/tools/snapshots.py harness/tools/file_ops.py tests/unit/test_snapshots.py tests/integration/test_ws_new_tools.py server/ws_handler.py harness/guardrails/engine.py harness/models.py server/api/config_routes.py
git commit -m "feat: write_file 覆盖前快照 + restore_file 回滚工具（快照店在工作区之外防篡改）

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

---

### Task 3: `git` 只读工具

**Files:**
- Create: `harness/tools/git_ops.py`
- Create: `tests/unit/test_git_ops.py`
- Modify: `Dockerfile`（app 镜像装 git——Render 进程内模式需要）
- Modify: `server/ws_handler.py`（import + 注册 GitTool）
- Modify: `harness/guardrails/engine.py`（git path 校验）
- Modify: `harness/models.py` + `server/api/config_routes.py`（加 `"git"`）
- Modify: `tests/integration/test_ws_new_tools.py`（追加测试 3）

**Interfaces:**
- Consumes: 任务 1/2 的注册模式；沙箱镜像已含 git（Dockerfile.sandbox）。
- Produces: `GitTool(docker_mgr=None, container_id=None, cwd: Path | None = None)`；`structured = {"branch": str, "changes": [{"status", "path"}]}`（status 子命令）；任务 6 文档依赖其协议描述。

- [ ] **Step 1: 写失败测试**

Create `tests/unit/test_git_ops.py`:

```python
"""Unit tests for the read-only git tool."""
import asyncio
import subprocess
from types import SimpleNamespace

from harness.tools.git_ops import GitTool


class FakeDocker:
    def __init__(self):
        self.calls: list[str] = []

    async def exec(self, container_id, cmd, timeout=10):
        self.calls.append(cmd)
        return SimpleNamespace(exit_code=0, stdout="", stderr="")


def test_unknown_subcommand_rejected():
    tool = GitTool()
    result = asyncio.run(tool.execute({"subcommand": "push"}))
    assert result.exit_code == 1
    assert "Unsupported" in result.stderr


def test_status_parses_porcelain(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("x")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("changed")

    tool = GitTool(cwd=tmp_path)
    result = asyncio.run(tool.execute({"subcommand": "status"}))

    assert result.exit_code == 0
    assert result.structured["branch"] in ("main", "master")
    assert any(c["status"] == "M" and c["path"] == "a.txt" for c in result.structured["changes"])


def test_not_a_repo_returns_clear_error(tmp_path):
    tool = GitTool(cwd=tmp_path)
    result = asyncio.run(tool.execute({"subcommand": "status"}))
    assert result.exit_code == 1
    assert "Not a git repository" in result.stderr


def test_docker_mode_uses_container_git():
    docker = FakeDocker()
    tool = GitTool(docker_mgr=docker, container_id="c1")
    result = asyncio.run(tool.execute({"subcommand": "diff"}))
    assert any(call.startswith("git -C /workspace") for call in docker.calls)
    assert result.exit_code == 0
```

- [ ] **Step 2: 运行测试验证 RED**

Run: `python -m pytest tests/unit/test_git_ops.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.tools.git_ops'`

- [ ] **Step 3: 实现 `harness/tools/git_ops.py`**

```python
"""Read-only git tool — status / diff / log, sandbox-aware."""
import shlex
import subprocess
import time
from pathlib import Path
from harness.tools.registry import Tool
from harness.models import ToolResult

_READ_ONLY: dict[str, list[str]] = {
    "status": ["status", "--porcelain"],
    "diff": ["diff", "HEAD"],
    "log": ["log", "--oneline", "-n", "20"],
}


class GitTool(Tool):
    """Inspect the workspace git repository (read-only subcommands only)."""

    def __init__(self, docker_mgr=None, container_id=None, cwd: Path | None = None):
        self._docker_mgr = docker_mgr
        self._container_id = container_id
        self._cwd = cwd

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return "Inspect the git repository: status (porcelain), diff (HEAD), or recent log. Read-only — committing stays with execute_shell."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "subcommand": {"type": "string", "enum": ["status", "diff", "log"],
                               "description": "Which read-only git view to produce"},
                "path": {"type": "string", "description": "Repo path (default: workspace root)"},
            },
            "required": ["subcommand"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        sub = arguments.get("subcommand", "")
        if sub not in _READ_ONLY:
            return ToolResult(tool_name="git", exit_code=1, stdout="",
                stderr=f"Unsupported subcommand: {sub}",
                duration_ms=int((time.time() - start) * 1000))
        path = arguments.get("path", "")

        if self._docker_mgr and self._container_id:
            clean = (path or "").replace("\\", "/").lstrip("/")
            repo = "/workspace" + (f"/{clean}" if clean else "")
            cmd = f"git -C {shlex.quote(repo)} {' '.join(_READ_ONLY[sub])}"
            result = await self._docker_mgr.exec(self._container_id, cmd, timeout=30)
            return await self._build_result(sub, result.exit_code, result.stdout, result.stderr, repo, start)

        cwd = (self._cwd or Path.cwd()).resolve()
        repo = str(cwd / path) if path else str(cwd)
        try:
            proc = subprocess.run(
                ["git", "-C", repo] + _READ_ONLY[sub],
                shell=False, timeout=30, capture_output=True, text=True,
            )
        except Exception as e:
            return ToolResult(tool_name="git", exit_code=1, stdout="", stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
        return await self._build_result(sub, proc.returncode, proc.stdout, proc.stderr, repo, start)

    async def _build_result(self, sub, code, stdout, stderr, repo, start) -> ToolResult:
        if code == 128 and "not a git repository" in stderr:
            return ToolResult(tool_name="git", exit_code=1, stdout="",
                stderr=f"Not a git repository: {repo}",
                duration_ms=int((time.time() - start) * 1000))
        if code not in (0, 1):
            return ToolResult(tool_name="git", exit_code=code, stdout=stdout, stderr=stderr,
                duration_ms=int((time.time() - start) * 1000))

        structured = None
        if sub == "status":
            branch = ""
            try:
                if self._docker_mgr and self._container_id:
                    br = await self._docker_mgr.exec(self._container_id,
                        f"git -C {shlex.quote(repo)} rev-parse --abbrev-ref HEAD", timeout=10)
                    branch = br.stdout.strip() if br.exit_code == 0 else ""
                else:
                    br = subprocess.run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"],
                                        shell=False, timeout=10, capture_output=True, text=True)
                    branch = br.stdout.strip() if br.returncode == 0 else ""
            except Exception:
                pass
            changes = []
            for line in (stdout or "").splitlines():
                if len(line) < 4:
                    continue
                changes.append({"status": line[:2].strip() or "??", "path": line[3:]})
            structured = {"branch": branch, "changes": changes}

        return ToolResult(tool_name="git", exit_code=0, stdout=stdout, stderr=stderr,
            structured=structured, duration_ms=int((time.time() - start) * 1000))
```

- [ ] **Step 4: 运行测试验证 GREEN**

Run: `python -m pytest tests/unit/test_git_ops.py -q`
Expected: 4 passed

- [ ] **Step 5: app 镜像装 git + 注册 + 护栏**

1. `Dockerfile` backend stage（第 11 行 `pip install` 之前）加：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
```

2. `server/ws_handler.py`：import `from harness.tools.git_ops import GitTool`；`_build_default_tool_registry` 加：

```python
    registry.register(GitTool(docker_mgr=docker_mgr, container_id=container_id, cwd=workspace_root))
```

3. `harness/guardrails/engine.py`，restore_file 检查之后加：

```python
        # Layer 1 also: Path sandbox for git repo path
        if tool_call.name == "git":
            raw_path = tool_call.arguments.get("path") or ""
            if raw_path:
                result = self._path_sandbox.validate(raw_path, "read")
                if result.action != GuardAction.ALLOW:
                    return result
```

4. `harness/models.py` + `server/api/config_routes.py` 各加 `"git"`。

- [ ] **Step 6: 集成测试**

Append to `tests/integration/test_ws_new_tools.py`:

```python
def test_git_status_via_agent_loop(tmp_path, monkeypatch):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text("x")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], cwd=tmp_path, check=True)

    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("git", {"subcommand": "status"}),
        _ok("Repo checked."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "Check git status"})
        result = _receive_until(ws, "tool.result")
        assert result["tool_name"] == "git"
        assert result["exit_code"] == 0
        _receive_until(ws, "session.complete")
```

Run: `python -m pytest tests/integration/test_ws_new_tools.py -q`
Expected: 3 passed

- [ ] **Step 7: 全量回归 + 提交**

Run: `python -m pytest -q`
Expected: 209 passed（204 + 4 单元 + 1 集成），无回归

```bash
git add harness/tools/git_ops.py tests/unit/test_git_ops.py tests/integration/test_ws_new_tools.py server/ws_handler.py harness/guardrails/engine.py harness/models.py server/api/config_routes.py Dockerfile
git commit -m "feat: 新增 git 只读工具（status/diff/log，app 镜像补装 git）

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

---

### Task 4: `netguard` + `web_fetch`

**Files:**
- Create: `harness/netguard.py`
- Create: `harness/tools/web_fetch.py`
- Create: `tests/unit/test_netguard.py`
- Create: `tests/unit/test_web_fetch.py`
- Modify: `server/ws_handler.py`（import + 注册 WebFetchTool）
- Modify: `harness/guardrails/engine.py`（web_fetch url 校验）
- Modify: `harness/models.py` + `server/api/config_routes.py`（加 `"web_fetch"`）
- Modify: `tests/integration/test_ws_new_tools.py`（追加测试 4）

**Interfaces:**
- Consumes: httpx（requirements.txt 已有）；任务 1 的 `tool.result` structured emit。
- Produces:
  - `harness.netguard.validate_url(url: str) -> str | None`（None=安全；否则返回原因字符串）。同步函数——护栏引擎 `check()` 是同步的；getaddrinfo 为纯本地解析。任务 5（egress 护栏）依赖。
  - `WebFetchTool()`（无构造依赖——恒主机侧）；`structured = {"final_url", "status_code", "content_type", "content"}`。
  - `WEB_FETCH_DENY` 环境变量（逗号分隔精确域名黑名单）。

- [ ] **Step 1: 写失败测试（netguard）**

Create `tests/unit/test_netguard.py`:

```python
"""Unit tests for the outbound-request guard (no real DNS/network)."""
import ipaddress
import socket

import pytest

from harness.netguard import validate_url


@pytest.fixture(autouse=True)
def _fake_dns(monkeypatch):
    """Deterministic DNS: literals resolve to themselves, known hosts mapped."""
    def fake(host, port):
        try:
            ipaddress.ip_address(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
        except ValueError:
            pass
        mapping = {
            "localhost": "127.0.0.1",
            "example.com": "93.184.216.34",
            "docs.python.org": "151.101.1.223",
            "ok.example.com": "93.184.216.34",
        }
        if host in mapping:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (mapping[host], 0))]
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fake)


def test_allows_public_https():
    assert validate_url("https://example.com/docs") is None
    assert validate_url("https://docs.python.org/3/") is None


def test_blocks_loopback_and_metadata():
    assert validate_url("http://127.0.0.1/") is not None
    assert validate_url("http://localhost/") is not None
    assert validate_url("http://169.254.169.254/latest/meta-data/") is not None
    assert validate_url("http://[::1]/") is not None


def test_blocks_private_ranges():
    assert validate_url("http://10.0.0.1/") is not None
    assert validate_url("http://172.16.0.5/") is not None
    assert validate_url("http://192.168.1.1/") is not None


def test_blocks_bad_schemes_and_ports():
    assert validate_url("file:///etc/passwd") is not None
    assert validate_url("ftp://example.com/") is not None
    assert validate_url("http://example.com:8080/") is not None
    assert validate_url("https://example.com:22/") is not None


def test_blocks_env_deny_list(monkeypatch):
    monkeypatch.setenv("WEB_FETCH_DENY", "evil.com")
    assert validate_url("https://evil.com/x") is not None
    assert validate_url("https://ok.example.com/") is None


def test_malformed_url():
    assert validate_url("not a url") is not None
    assert validate_url("") is not None
```

- [ ] **Step 2: 运行测试验证 RED**

Run: `python -m pytest tests/unit/test_netguard.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.netguard'`

- [ ] **Step 3: 实现 `harness/netguard.py`**

```python
"""Outbound-request guard: block private/loopback/link-local/metadata targets.

Shared by the web_fetch tool (always host-side — sandbox containers have no
network) and by the guardrail engine's egress check for execute_shell URLs.
Synchronous on purpose: the guardrail engine's check() is sync, and the
resolution below is a pure local getaddrinfo (no network round-trip).
"""
import ipaddress
import os
import socket
from urllib.parse import urlparse

BLOCKED_NETS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _env_deny() -> set[str]:
    return {d.strip().lower() for d in os.environ.get("WEB_FETCH_DENY", "").split(",") if d.strip()}


def validate_url(url: str) -> str | None:
    """Return None when the URL is safe to fetch, else a reason string."""
    if not url or not isinstance(url, str):
        return "Empty URL"
    try:
        parsed = urlparse(url)
    except ValueError:
        return f"Malformed URL: {url[:100]}"
    if parsed.scheme not in ("http", "https"):
        return f"Only http/https URLs are allowed (got: {parsed.scheme or 'no scheme'})"
    try:
        port = parsed.port
    except ValueError:
        return f"Invalid port in URL: {url[:100]}"
    if port not in (None, 80, 443):
        return f"Only ports 80/443 are allowed (got: {port})"
    host = (parsed.hostname or "").lower()
    if not host:
        return f"URL has no host: {url[:100]}"
    if host in _env_deny():
        return f"Domain is blocked: {host}"
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return f"Cannot resolve host: {host}"
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        for net in BLOCKED_NETS:
            if ip in net:
                return f"Target resolves to a blocked address ({ip} in {net}): {host}"
    return None
```

- [ ] **Step 4: 运行测试验证 GREEN**

Run: `python -m pytest tests/unit/test_netguard.py -q`
Expected: 6 passed

- [ ] **Step 5: 写失败测试（web_fetch）**

Create `tests/unit/test_web_fetch.py`:

```python
"""Unit tests for the web_fetch tool (fake transport, no real network)."""
import asyncio
import ipaddress
import socket

import pytest

from harness.tools import web_fetch


@pytest.fixture(autouse=True)
def _fake_dns(monkeypatch):
    """Deterministic DNS: literals resolve to themselves, example.com public."""
    def fake(host, port):
        try:
            ipaddress.ip_address(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
        except ValueError:
            pass
        if host == "example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fake)


class FakeResponse:
    def __init__(self, status_code=200, headers=None, text="ok", url="https://example.com/"):
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}
        self.text = text
        self.url = url


class FakeClient:
    def __init__(self, timeout=None, follow_redirects=False):
        self.gets: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, headers=None):
        self.gets.append(url)
        return FakeResponse()


def test_blocked_url_never_reaches_client():
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "http://169.254.169.254/latest/meta-data/"}))
    assert result.exit_code == 1
    assert "169.254.169.254" in result.stderr


def test_fetch_returns_structured_content(monkeypatch):
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", FakeClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/"}))
    assert result.exit_code == 0
    assert result.structured["status_code"] == 200
    assert result.structured["content"] == "ok"
    assert "ok" in result.stdout  # LLM sees stdout


def test_redirect_to_private_target_is_blocked(monkeypatch):
    class RedirectClient(FakeClient):
        async def get(self, url, headers=None):
            return FakeResponse(status_code=302,
                                headers={"content-type": "text/html", "location": "http://10.0.0.1/steal"})
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", RedirectClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/"}))
    assert result.exit_code == 1
    assert "10.0.0.1" in result.stderr


def test_non_text_content_type_rejected(monkeypatch):
    class ImageClient(FakeClient):
        async def get(self, url, headers=None):
            return FakeResponse(headers={"content-type": "image/png"})
    monkeypatch.setattr(web_fetch.httpx, "AsyncClient", ImageClient)
    tool = web_fetch.WebFetchTool()
    result = asyncio.run(tool.execute({"url": "https://example.com/x.png"}))
    assert result.exit_code == 1
    assert "Content type" in result.stderr
```

- [ ] **Step 6: 运行测试验证 RED**

Run: `python -m pytest tests/unit/test_web_fetch.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.tools.web_fetch'`

- [ ] **Step 7: 实现 `harness/tools/web_fetch.py`**

```python
"""Fetch a public web page over HTTP(S) — always host-side.

Sandbox containers run with network_mode=none, so this tool executes in the
server process in every deployment mode. SSRF is the primary threat: every
hop (including each redirect) passes netguard validation, which blocks
private/loopback/link-local/cloud-metadata targets and non-80/443 ports.
"""
import time

import httpx

from harness.tools.registry import Tool
from harness.models import ToolResult
from harness.netguard import validate_url

MAX_BYTES = 512 * 1024
MAX_REDIRECTS = 5
MAX_STDOUT_CHARS = 4096  # LLM context contains only stdout
ALLOWED_CONTENT_TYPES = ("text/", "application/json", "application/xml")


class WebFetchTool(Tool):
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch a public web page and return its text content (truncated). Only http(s) on ports 80/443; private-network and cloud-metadata targets are blocked."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "HTTP(S) URL to fetch"},
            },
            "required": ["url"],
        }

    async def execute(self, arguments: dict) -> ToolResult:
        start = time.time()
        url = str(arguments.get("url", ""))
        reason = validate_url(url)
        if reason:
            return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr=reason,
                duration_ms=int((time.time() - start) * 1000))

        current = url
        try:
            for _ in range(MAX_REDIRECTS + 1):
                reason = validate_url(current)
                if reason:
                    return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr=reason,
                        duration_ms=int((time.time() - start) * 1000))
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                    resp = await client.get(current, headers={"User-Agent": "GlimmerAgent/1.0"})
                if resp.status_code in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("location")
                    if not loc:
                        return ToolResult(tool_name="web_fetch", exit_code=1, stdout="",
                            stderr=f"Redirect without location: {current}",
                            duration_ms=int((time.time() - start) * 1000))
                    current = str(httpx.URL(resp.url).join(loc))
                    continue

                ct = resp.headers.get("content-type", "")
                if not any(ct.lower().startswith(a) for a in ALLOWED_CONTENT_TYPES):
                    return ToolResult(tool_name="web_fetch", exit_code=1, stdout="",
                        stderr=f"Content type not allowed: {ct or '(none)'}",
                        duration_ms=int((time.time() - start) * 1000))
                body = resp.text
                if len(body) > MAX_BYTES:
                    body = body[:MAX_BYTES]
                stdout_body = body[:MAX_STDOUT_CHARS]
                if len(body) > MAX_STDOUT_CHARS:
                    stdout_body += "\n...[truncated]"
                return ToolResult(tool_name="web_fetch", exit_code=0,
                    stdout=stdout_body,
                    structured={
                        "final_url": str(resp.url),
                        "status_code": resp.status_code,
                        "content_type": ct,
                        "content": body,
                    },
                    duration_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr=str(e),
                duration_ms=int((time.time() - start) * 1000))
        return ToolResult(tool_name="web_fetch", exit_code=1, stdout="", stderr="Too many redirects",
            duration_ms=int((time.time() - start) * 1000))
```

- [ ] **Step 8: 运行测试验证 GREEN**

Run: `python -m pytest tests/unit/test_web_fetch.py -q`
Expected: 4 passed

- [ ] **Step 9: 注册 + 护栏接线**

1. `server/ws_handler.py`：import `from harness.tools.web_fetch import WebFetchTool`；`_build_default_tool_registry` 加：

```python
    registry.register(WebFetchTool())
```

2. `harness/guardrails/engine.py` 顶部 import 加：

```python
from harness.netguard import validate_url
```

`check()` 内 git 检查之后加：

```python
        # Layer 4: web_fetch URL must pass the SSRF guard (defense in depth
        # behind the tool's own check)
        if tool_call.name == "web_fetch":
            reason = validate_url(tool_call.arguments.get("url", ""))
            if reason:
                return GuardResult(action=GuardAction.BLOCK, layer=4, reason=reason)
```

3. `harness/models.py` + `server/api/config_routes.py` 各加 `"web_fetch"`。

- [ ] **Step 10: 集成测试（内网目标被引擎拦，不触网）**

Append to `tests/integration/test_ws_new_tools.py`:

```python
def test_web_fetch_metadata_url_blocked_by_engine(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("web_fetch", {"url": "http://169.254.169.254/latest/meta-data/"}),
        _ok("Tried."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "Fetch instance metadata"})
        pending = _receive_until(ws, "guardrail.pending")
        assert pending["action"] == "blocked"
        assert "169.254.169.254" in pending["reason"]
    # BLOCK leaves the session AWAITING_HUMAN; disconnect without deciding.
```

Run: `python -m pytest tests/integration/test_ws_new_tools.py -q`
Expected: 4 passed

- [ ] **Step 11: 全量回归 + 提交**

Run: `python -m pytest -q`
Expected: 220 passed（209 + 6 netguard + 4 web_fetch + 1 集成），无回归

```bash
git add harness/netguard.py harness/tools/web_fetch.py tests/unit/test_netguard.py tests/unit/test_web_fetch.py tests/integration/test_ws_new_tools.py server/ws_handler.py harness/guardrails/engine.py harness/models.py server/api/config_routes.py
git commit -m "feat: 新增 web_fetch 工具 + netguard SSRF 校验（内网/元数据封锁，逐跳重定向重验）

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

---

### Task 5: secret scan + egress 护栏

**Files:**
- Create: `harness/guardrails/secrets.py`
- Create: `tests/unit/test_guardrail_secrets.py`
- Modify: `harness/guardrails/engine.py`（SecretScanner + egress URL 检查接线）
- Modify: `tests/integration/test_ws_new_tools.py`（追加测试 5）

**Interfaces:**
- Consumes: 任务 4 的 `harness.netguard.validate_url`；`GuardrailEngine(sandbox_root, whitelist_extra=None)` 现有构造；`ToolCall(id, name, arguments)`。
- Produces: `SecretScanner.check(text: str) -> GuardResult`（命中 ASK_HUMAN layer=4，原因含模式名与脱敏片段）；`GuardrailEngine` 新增第四层行为（write_file content / execute_shell command 检查 + egress）。
- 关键顺序（BLOCK 优先于 ASK_HUMAN）：egress URL 检查放在 whitelist **之前**——否则 curl 等非白名单命令先被 ASK_HUMAN 拦截，内网 URL 永远无法硬封锁。

- [ ] **Step 1: 写失败测试**

Create `tests/unit/test_guardrail_secrets.py`:

```python
"""Unit tests for secret scanning and egress guardrails."""
import ipaddress
import socket

import pytest

from harness.guardrails.engine import GuardrailEngine
from harness.guardrails.secrets import SecretScanner
from harness.models import ToolCall, GuardAction


@pytest.fixture(autouse=True)
def _fake_dns(monkeypatch):
    """Deterministic DNS: literals resolve to themselves (public IPs pass)."""
    def fake(host, port):
        try:
            ipaddress.ip_address(host)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
        except ValueError:
            pass
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", fake)


def test_scanner_hits_high_confidence_patterns():
    scanner = SecretScanner()
    samples = [
        "-----BEGIN RSA PRIVATE KEY-----",
        "AKIAIOSFODNN7EXAMPLE",
        "token ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        "sk-ant-api03-abcdefghijklmnopqrstuvwxyz012345",
        "sk-abcdefghijklmnopqrstuvwxyz0123456789",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0In0.abcdefghijklmnopqrstuvwxyz012345",
    ]
    for s in samples:
        result = scanner.check(s)
        assert result.action == GuardAction.ASK_HUMAN, s
        assert "***" in result.reason  # masked


def test_scanner_passes_ordinary_content():
    scanner = SecretScanner()
    assert scanner.check("def foo(): return 42").action == GuardAction.ALLOW
    assert scanner.check("echo hello world").action == GuardAction.ALLOW


def test_engine_asks_human_on_secret_in_write_file():
    engine = GuardrailEngine(sandbox_root=".")
    call = ToolCall(id="t1", name="write_file",
                    arguments={"path": "x.txt", "content": "key = 'sk-ant-abcdefghijklmnopqrstuvwxyz012345'"})
    result = engine.check(call)
    assert result.action == GuardAction.ASK_HUMAN
    assert result.layer == 4


def test_engine_blocks_internal_urls_in_shell_command():
    engine = GuardrailEngine(sandbox_root=".")
    call = ToolCall(id="t2", name="execute_shell",
                    arguments={"command": "pip install http://169.254.169.254/x"})
    result = engine.check(call)
    assert result.action == GuardAction.BLOCK
    assert "169.254.169.254" in result.reason


def test_engine_allows_public_urls_in_shell_command():
    engine = GuardrailEngine(sandbox_root=".")
    call = ToolCall(id="t3", name="execute_shell",
                    arguments={"command": "pip install https://8.8.8.8/simple/"})
    result = engine.check(call)
    assert result.action == GuardAction.ALLOW
```

- [ ] **Step 2: 运行测试验证 RED**

Run: `python -m pytest tests/unit/test_guardrail_secrets.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.guardrails.secrets'`

- [ ] **Step 3: 实现 `harness/guardrails/secrets.py`**

```python
"""Layer 4a: high-confidence secret-pattern detection (zero dependencies).

Only high-confidence patterns are matched — false positives must cost the
user nothing more than a single approve click (ASK_HUMAN), not a blocked
write. Test fixtures with example keys still flow through the guardrail
approve/reject modal, which is exactly the intended UX.
"""
import re

from harness.models import GuardResult, GuardAction

PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "GitHub token"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"), "Anthropic API key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "OpenAI-style API key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{32,}\b"), "JWT"),
]


def _mask(match_text: str) -> str:
    return match_text[:12] + "***" if len(match_text) > 15 else "***"


class SecretScanner:
    """Detect likely secrets in tool arguments."""

    def check(self, text: str) -> GuardResult:
        for pattern, label in PATTERNS:
            m = pattern.search(text or "")
            if m:
                return GuardResult(
                    action=GuardAction.ASK_HUMAN,
                    layer=4,
                    reason=f"Possible {label} in content: {_mask(m.group(0))}",
                )
        return GuardResult(action=GuardAction.ALLOW, layer=4)
```

- [ ] **Step 4: 引擎接线**

In `harness/guardrails/engine.py`：
1. 顶部 import 加：

```python
import re
from harness.guardrails.secrets import SecretScanner
from harness.netguard import validate_url
```

模块级（class 之前）加：

```python
_URL_RE = re.compile(r"https?://[^\s\"'`]+")
```

2. `__init__` 加 `self._secrets = SecretScanner()`。
3. `check()` 中 PathSandbox 段（restore_file 检查之后、execute_shell 段之前）加 secret 检查：

```python
        # Layer 4a: high-confidence secret patterns in written content or
        # shell commands (ASK_HUMAN — one approve click, not a blocked write).
        if tool_call.name == "write_file":
            result = self._secrets.check(str(tool_call.arguments.get("content", "")))
            if result.action != GuardAction.ALLOW:
                return result
        if tool_call.name == "execute_shell":
            result = self._secrets.check(str(tool_call.arguments.get("command", "")))
            if result.action != GuardAction.ALLOW:
                return result
```

4. `check()` 中 execute_shell/run_tests 段改为（egress 在 whitelist **之前**）：

```python
        # Layer 2 & 3: Command safety for shell execution
        if tool_call.name in ("execute_shell", "run_tests"):
            command = tool_call.arguments.get("command", "")
            if tool_call.name == "run_tests" and not command:
                path = tool_call.arguments.get("path", "tests/")
                command = f"python -m pytest {path} -q"
            if command:
                # Layer 4b: egress URLs in the command must pass netguard —
                # private/loopback/cloud-metadata targets are hard-blocked.
                # Checked BEFORE the whitelist: curl etc. are not whitelisted
                # and would otherwise surface as ASK_HUMAN first.
                for m in _URL_RE.finditer(command):
                    reason = validate_url(m.group(0))
                    if reason:
                        return GuardResult(action=GuardAction.BLOCK, layer=4, reason=reason)
                # Layer 2: Whitelist
                result = self._whitelist.check(command)
                if result.action != GuardAction.ALLOW:
                    return result
                # Layer 3: Pattern blacklist
                result = self._patterns.check(command)
                if result.action != GuardAction.ALLOW:
                    return result
```

- [ ] **Step 5: 运行测试验证 GREEN**

Run: `python -m pytest tests/unit/test_guardrail_secrets.py -q`
Expected: 5 passed

- [ ] **Step 6: 集成测试（secret 触发 guardrail.pending → reject）**

Append to `tests/integration/test_ws_new_tools.py`:

```python
def test_secret_in_write_triggers_guardrail_pending(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch, [
        _tool_use("write_file", {"path": "leak.txt", "content": "token = 'sk-ant-abcdefghijklmnopqrstuvwxyz012345'"}),
        _ok("Done."),
    ])
    with client.websocket_connect("/ws/session") as ws:
        ws.send_json({"type": "task.submit", "content": "Write a config with a token"})
        pending = _receive_until(ws, "guardrail.pending")
        assert pending["action"] == "ask_human"
        ws.send_json({"type": "guardrail.reject"})
        _receive_until(ws, "session.complete")
    assert not (tmp_path / "leak.txt").exists()
```

Run: `python -m pytest tests/integration/test_ws_new_tools.py -q`
Expected: 5 passed

- [ ] **Step 7: 全量回归 + 提交**

Run: `python -m pytest -q`
Expected: 226 passed（220 + 5 单元 + 1 集成），无回归

```bash
git add harness/guardrails/secrets.py harness/guardrails/engine.py tests/unit/test_guardrail_secrets.py tests/integration/test_ws_new_tools.py
git commit -m "feat: 护栏第四层——secret scan（ASK_HUMAN）+ execute_shell egress 内网 URL 封锁（BLOCK）

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

---

### Task 6: 文档更新 + 全量验证 + 推送

**Files:**
- Modify: `README.md`（工具参考 + 安全说明 + enabled_tools 示例）
- Modify: `web/src/pages/AboutPage.tsx`、`web/src/pages/GuidePage.tsx`、`web/src/pages/LearnPage.tsx`
- Rebuild: `server/static/`（`npm run build` 产物，必须提交）

**Interfaces:** 无新接口。依赖任务 1-5 全部完成。

- [ ] **Step 1: 定位 README 锚点**

Run:
```bash
grep -n "工具参考\|search_code\|execute_shell" README.md
grep -n "search_code\|execute_shell\|read_file" web/src/pages/AboutPage.tsx web/src/pages/GuidePage.tsx web/src/pages/LearnPage.tsx
```
记录各锚点行号，按 Step 2-5 在其后追加内容（增量编辑，不重写）。

- [ ] **Step 2: README 工具参考更新**

在「工具参考」章节现有工具表/列表之后追加：

```markdown
#### 2026-08 新增工具

| 工具 | 说明 | 关键参数 |
|---|---|---|
| `list_files` | 浏览工作区目录结构（有界深度，自动跳过 node_modules 等依赖目录） | `path`、`max_depth` |
| `restore_file` | 回滚文件到最近一次 `write_file` 覆盖前的内容（快照店在工作区之外，agent 不可见） | `path` |
| `git` | 只读 git 三件套：`status`（结构化）、`diff HEAD`、`log`（最近 20 条） | `subcommand`、`path` |
| `web_fetch` | 抓取公网网页文本（≤512KB，仅 http(s) 80/443；私网/云元数据地址硬封锁） | `url` |

安全说明：

- **secret scan（护栏第四层）**：`write_file` 内容与 `execute_shell` 命令中的高置信密钥模式（私钥、AWS/GitHub/Anthropic/OpenAI token、JWT）会触发人工确认弹窗（ASK_HUMAN），可放行或拒绝。
- **egress 护栏**：`execute_shell` 命令中的内网/回环/云元数据 URL 一律 BLOCK；`web_fetch` 每个重定向跳转均重新校验。
- **快照回滚**：Render 免费层主机文件系统是临时的——跨部署快照会丢失，会话内回滚不受影响。
```

同时把 `enabled_tools:` 示例配置段更新为：

```yaml
  enabled_tools:
    - read_file
    - write_file
    - execute_shell
    - run_tests
    - search_code
    - list_files
    - restore_file
    - git
    - web_fetch
```

- [ ] **Step 3: About 页更新**

在 AboutPage.tsx 的「功能亮点/安全架构」相关小节追加：

```tsx
        <li>新工具集：<code>list_files</code> 目录浏览、<code>restore_file</code> 快照回滚、<code>git</code> 只读检查、<code>web_fetch</code> 联网查文档（SSRF 防护）</li>
        <li>护栏第四层：secret scan 敏感信息拦截（人工确认）+ execute_shell 内网地址硬封锁</li>
```

（按页面现有 li 结构微调措辞，保持与现有条目风格一致。）

- [ ] **Step 4: Guide 页更新**

在 GuidePage.tsx 工具指南小节追加新工具用法示例：

```tsx
        <p>浏览项目结构：让 Agent 先 <code>list_files</code> 再读文件，避免盲猜路径。</p>
        <p>改坏了想回滚：直接说「用 restore_file 恢复 xxx」，快照在每次 write_file 覆盖前自动保存。</p>
        <p>查文档：Agent 可用 <code>web_fetch</code> 抓取公开文档页（内网地址与云元数据被硬封锁）。</p>
        <p>查看改动：让 Agent 运行 <code>git status</code> / <code>git diff</code> 汇报修改。</p>
```

- [ ] **Step 5: Learn 页更新**

在 LearnPage.tsx 概念章节追加：

```tsx
        <p><strong>SSRF 防护</strong>：web_fetch 与 execute_shell 的出口 URL 都要过 netguard——DNS 解析后封锁私网（10/8、172.16/12、192.168/16）、回环、链路本地与云元数据地址（169.254.169.254），且每个重定向跳转重新校验。</p>
        <p><strong>快照回滚</strong>：快照店位于 agent 可达范围之外（~/.harness/snapshots 或 Docker 主机侧目录），write_file 覆盖前自动保存原内容，restore_file 取最新快照写回。</p>
        <p><strong>secret scan</strong>：高置信密钥模式触发 ASK_HUMAN 确认，误报代价只是一次点击。</p>
```

- [ ] **Step 6: 前端构建 + 提交产物**

Run: `cd web && npm run build`
Expected: `✓ built in ...s`（server/static/ 更新新 hash 产物）
Run: `npx vitest run`
Expected: 9 passed（前端逻辑无改动，纯文案）

```bash
git add README.md web/src/pages/AboutPage.tsx web/src/pages/GuidePage.tsx web/src/pages/LearnPage.tsx server/static/
git commit -m "docs: 新增工具文档——README 工具参考与安全说明，About/Guide/Learn 宣传页同步

Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 7: 全量终验 + 推送**

Run: `python -m pytest -q`
Expected: 226 passed 全绿
Run: `cd web && npx vitest run`
Expected: 9 passed
Run: `cd web && npm run build`
Expected: 成功（若 Step 6 后无源码改动则产物无变化）

```bash
git status  # 确认无遗漏未提交文件
git push origin main
```

Render 自动部署后：在线上验证 list_files / restore_file / git status / web_fetch（公网 URL 成功、内网 URL 被拦）各一次。

---

## Self-Review 记录

- **Spec coverage**：spec 中 A1（Task 1）、B1（Task 2）、A2（Task 3）、A5（Task 4）、B2+B3（Task 5）、文档（Task 6）、enabled_tools 默认（各任务接线步）、Dockerfile git（Task 3）、tool.result structured（Task 1 Step 5）、快照 SNAPSHOT_DIR 测试覆盖（Task 2 Step 7）全部有对应任务。spec 的"不做的事"清单未实现 ✓。
- **Placeholder scan**：无 TBD/TODO/"Similar to Task N"；每个代码步骤均为完整代码。
- **Type consistency**：`SnapshotStore.save/load`、`validate_url`、`ListFilesTool/RestoreFileTool/GitTool/WebFetchTool` 构造签名在各任务间一致；`_build_default_tool_registry(docker_mgr, container_id, workspace_root, snapshots=None)` 自 Task 2 起签名固定；`WriteFileTool(..., snapshots=None)` 默认值保持向后兼容；测试文件追加顺序与任务顺序一致。
- **与真实代码核对**（写计划时逐一验证）：`guardrail.pending` 事件形状（loop.py:313-328，action ∈ blocked/ask_human，字段 reason/tool/args）；BLOCK 后状态 AWAITING_HUMAN 且 `_pending_approval` 未设置（Task 4 集成测试断开而不 approve/reject，避免踩现有 BLOCK-reject 路径）；`configure(app, llm_override=...)` 签名（ws_handler.py:39）；`create_app(project_root=...)`（test_ws_cancel.py 模式）；`GuardrailEngine(sandbox_root, whitelist_extra=None)`（engine.py:16）；`MockLLMAdapter` FIFO 耗尽抛 IndexError（各测试响应数精确匹配）；curl 不在 DEFAULT_WHITELIST（whitelist.py:12）→ egress 必须在 whitelist 之前（spec 已同步修正）；单测 DNS 全部 monkeypatch、httpx 全部替换 AsyncClient（不触真网）。
- **测试计数**：Task 1 后 197 → Task 2 后 204 → Task 3 后 209 → Task 4 后 220 → Task 5 后 226 → Task 6 不变。若实际执行时基线数字有偏差，以"新增测试数 + 无失败"为准。
