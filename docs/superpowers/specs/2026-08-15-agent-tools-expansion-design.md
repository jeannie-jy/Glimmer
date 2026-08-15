# Agent 工具扩展设计：list_files / 快照回滚 / git 只读 / web_fetch / 安全护栏

日期：2026-08-15
状态：已确认（用户批准全部推荐选项）

## 背景

当前 agent 工具集仅 5 个：`read_file`、`write_file`、`execute_shell`、`run_tests`、`search_code`。主要盲区：agent 无法浏览项目结构（盲操作）、文件被覆盖后无回滚手段、无法查看 git 状态与 diff、无法联网查文档。本次按推荐顺序新增：

1. **A1 `list_files`** — 目录浏览
2. **B1 快照回滚 + `restore_file`** — 覆盖写保护
3. **A2 `git`** — 只读三件套（status / diff / log）
4. **A5 `web_fetch`** — 联网查文档（SSRF 护栏）
5. **B2 secret scan** — 护栏第四层（敏感信息检测）
6. **B3 egress 护栏** — execute_shell 联网出口检查

全部完成后更新 `README.md` 与前端宣传页 About / Guide / Learn。

## 架构事实（决定实现形态）

三种运行形态，新工具必须全部兼容：

| 形态 | 工具运行位置 | 网络 | workspace |
|---|---|---|---|
| 本地开发（LOCAL_MODE） | 进程内 | 有 | 项目 cwd 或 WORKSPACE_ROOT |
| Render 生产 | 进程内（无 docker socket 回退） | 有 | /workspace（主机文件系统） |
| 自托管多用户 | Docker 沙箱容器 | **无**（network_mode=none，512MB 限额） | 绑定挂载 /workspace |

推论：
- `web_fetch` 必须**主机侧**执行（沙箱容器无网络）→ 在所有形态下统一走进程内 httpx，SSRF 护栏是关键安全面。
- B3 egress 护栏对进程内形态（本地/Render）是刚需；沙箱形态无网络，检查无害（防御纵深）。
- 沙箱镜像（Dockerfile.sandbox）已含 git/ripgrep/pytest；**app 镜像（Dockerfile）缺 git**，需加 apt-get 安装（Render 进程内模式依赖）。

已确认的用户决策：
- B1 范围：仅 write_file 覆盖写快照；execute_shell 的 rm/mv/重定向不拦（git 兜底）
- B2 动作：ASK_HUMAN（复用现有 guardrail.pending approve/reject 模态框）
- A5/B3 策略：公网开放 + 硬封锁内网/回环/云元数据地址
- A2 范围：只读三件套，写操作继续走 execute_shell

## A1 `list_files`

**协议**（JSON Schema）：

```json
{
  "type": "object",
  "properties": {
    "path": {"type": "string", "description": "Directory to list (default: workspace root)"},
    "max_depth": {"type": "integer", "description": "Max recursion depth (default: 3, max: 6)"}
  },
  "required": []
}
```

**输出**：`ToolResult.structured = {"files": [{"name": "相对路径", "size": int, "modified": "YYYY-MM-DDTHH:MM"}]}`，stdout 输出摘要（N files）。目录本身不下发（LLM 从路径推断结构即可，控制 token 消耗）。

**实现**：
- 本地/Render：基于 `_list_local_files()` 的逻辑改造为 `harness/tools/list_files.py`——相对 workspace 根、深度限制、跳过 `_LOCAL_SKIP_DIRS`/`_LOCAL_SKIP_FILES`/`_LOCAL_SKIP_SUFFIXES`。
- Docker：`find /workspace -maxdepth N -type f -printf ...` 经 docker_mgr.exec。
- 护栏：`GuardrailEngine.check` 对 `list_files` 的 `path` 参数做 PathSandbox read 校验。
- 注册：`_build_default_tool_registry` 增加；`config_routes.py` 的 `enabled_tools` 默认列表增加 `"list_files"`。

**测试**：单元（深度限制、跳过名单、路径穿越拒绝、空目录）+ 集成（ws 流 MockLLMAdapter tool_use 触发）。

## B1 快照回滚 + `restore_file`

**设计**：`write_file` 覆盖**已存在**文件前，把原内容存入快照店；新增 `restore_file(path)` 取最新快照写回。快照店位于 **agent 可达范围之外**（防篡改）：

- 本地/Render：`~/.harness/snapshots/{session_id}/`（保持相对路径结构）
- Docker：主机侧 `WORKSPACE_ROOT/{user_id}/.harness-snapshots/{session_id}/`（容器仅挂载 user_workspace，看不到该目录；恢复经 docker_mgr.exec 写回容器）

**实现点**：
- 快照 key = 相对路径（posix 规范化，防 `../` 穿越）。每会话目录隔离，session 结束时保留（会话内可多次回滚）。
- 快照为**栈式**：每次覆盖写追加一个新快照，`restore_file` 取该路径**最新**快照写回（回滚后再覆盖写会再次快照，可继续回滚）。
- `write_file` 覆盖前快照——在工具内部完成（文件工具已拿到绝对/沙箱路径）；Docker 路径先 `cat` 原文件到主机快照目录，再写新内容。
- `restore_file` 协议：`{"path": string}`；无快照 → exit_code 1 + stderr 说明；快照店由工具内部按 session_id 定位，session_id 经构造函数注入（不暴露给 LLM 参数）。
- Render 免费层主机文件系统临时：跨部署快照丢失，会话内回滚不受影响（README 注明）。
- 护栏：PathSandbox write 校验 path；快照目录本身永不出现在工具参数中。

**测试**：单元（覆盖→restore 还原、二次覆盖回滚到第一版、不存在的文件 restore 报错、快照 per-session 隔离、路径穿越拒绝）+ 集成。

## A2 `git`（只读三件套）

**协议**：

```json
{
  "type": "object",
  "properties": {
    "subcommand": {"type": "string", "enum": ["status", "diff", "log"]},
    "path": {"type": "string", "description": "Repo path (default: workspace root)"}
  },
  "required": ["subcommand"]
}
```

**输出**：
- `status`：structured `{"branch": str, "changes": [{"path": str, "status": "M|A|D|R|??"}]}`（解析 `--porcelain`）
- `diff`：stdout 文本（`git diff HEAD`，同时含未暂存与已暂存变更）
- `log`：stdout 文本（`git log --oneline -n 20`）

**实现**：
- 本地/Render：subprocess `git -C <root> <cmd>`；**app Dockerfile 加 `apt-get install -y --no-install-recommends git`**。
- Docker：docker_mgr.exec `git -C /workspace ...`（沙箱镜像已有 git）。
- 非 git 仓库：exit_code 1 + stderr `"Not a git repository: <path>"`（不抛异常）。
- 护栏：PathSandbox read 校验 path；代码层只允许三个只读子命令（不依赖 LLM 自觉）。
- `enabled_tools` 默认列表增加 `"git"`。

**测试**：单元（mock subprocess 输出解析 porcelain、非仓库错误路径、非法 subcommand 拒绝）+ 集成。

## A5 `web_fetch`

**协议**：

```json
{
  "type": "object",
  "properties": {
    "url": {"type": "string", "description": "HTTP(S) URL to fetch"}
  },
  "required": ["url"]
}
```

**输出**：structured `{"final_url", "status_code", "content_type", "content"}`；content 截断至 512KB（stdout 同时给摘要）。重定向：最多跟随 5 跳，每跳重新校验 URL。

**SSRF 校验器**（新模块 `harness/tools/web/netguard.py`，工具与护栏引擎共用）：

1. scheme 仅 http/https；端口仅 80/443。
2. 域名解析后逐 IP 校验，拒绝：`127.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`169.254.0.0/16`（含云元数据）、`0.0.0.0`、`::1`、`fc00::/7`、`fe80::/10`。
3. 可选环境变量 `WEB_FETCH_DENY`（逗号分隔域名）追加黑名单；v1 不加 Settings UI。
4. 超时 15s；Content-Type 白名单（`text/*`、`application/json`、`application/xml` 等文本类；其余拒绝）；User-Agent 标识 `GlimmerAgent/1.0`。

**执行**：进程内 httpx（已依赖）。**所有形态统一主机侧**——沙箱容器无网络，此工具不尝试容器内执行。

**护栏引擎层**：`web_fetch` 的 url 参数同样过 netguard（防御工具实现失误的纵深）。

**测试**：SSRF 用例矩阵（127.0.0.1、169.254.169.254、10.x、192.168.x、localhost 域名、重定向到内网、非 80/443 端口、file:// 协议）+ 正常抓取（httpx mock）+ 超时 + Content-Type 拒绝 + 集成流。

## B2 secret scan（护栏第四层）

**位置**：`GuardrailEngine.check` 增加一层 `SecretScanner`（新模块 `harness/guardrails/secrets.py`，零依赖正则库）。

**检查对象**：`write_file` 的 `content` 参数、`execute_shell` 的 `command` 参数。

**模式库（仅高置信，控制误报）**：
- 私钥头：`-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----`
- AWS：`AKIA[0-9A-Z]{16}`
- GitHub：`ghp_[A-Za-z0-9]{36}`
- Anthropic：`sk-ant-[A-Za-z0-9_-]{20,}`
- OpenAI：`sk-[A-Za-z0-9]{20,}`
- JWT：三段 base64url + 点分隔且第三段为 HMAC 长度（≥32 字符）的高置信形态

**动作**：命中 → `GuardAction.ASK_HUMAN`（复用现有 `guardrail.pending` approve/reject 模态框与 approve_pending/reject_pending 流程）。原因字符串给出模式名与脱敏片段（如 `sk-ant-***`）。

**误报控制**：仅高置信模式；测试夹具中的示例 key 会触发确认框，用户一次点击即可放行（这正是 ASK_HUMAN 优于 BLOCK 的原因）。

**测试**：单元（每种模式命中/不命中、脱敏输出）+ 集成（write_file 假 key 触发 guardrail.pending → approve 放行完成；reject 拒绝）。

## B3 egress 护栏

**位置**：`GuardrailEngine.check` 在 execute_shell 的 whitelist/pattern 检查之后增加：从 command 字符串提取 URL（`https?://[^\s"'`]+`），逐 URL 过 netguard。

**规则**：与 A5 相同（公网开放 + 内网/元数据硬封锁）。沙箱形态无网络，检查结果通常全放行，无害。

**动作**：命中内网地址 → `GuardAction.BLOCK`（原因说明）——命令里带内网地址几乎必是 SSRF 尝试或误用，无需人工放行；比 ASK_HUMAN 更合理（用户批准一条恶意 curl 的风险大于收益）。web_fetch 的 URL 校验失败同样 BLOCK。

**测试**：单元（curl 169.254.169.254 → BLOCK；curl pypi.org → 放行；无 URL 命令 → 放行）+ 集成。

## 文档更新（代码完成后）

- `README.md`：工具清单表格加 5 个新工具（含协议摘要）；安全章节补 SSRF/secret scan/快照回滚说明；部署章节注明 Render 免费层快照跨部署丢失、web_fetch 主机侧执行。
- `web/src/pages/AboutPage.tsx`：功能亮点/安全架构小节。
- `web/src/pages/GuidePage.tsx`：工具使用指南（新工具用法示例）。
- `web/src/pages/LearnPage.tsx`：概念说明（护栏分层、SSRF、快照回滚原理）。
- 位置在实现时定位现有对应小节，做增量编辑而非重写。

## 实施顺序与测试策略

1. A1 list_files（TDD：RED → GREEN）
2. B1 快照 + restore_file
3. A2 git（含 Dockerfile git）
4. A5 web_fetch + netguard
5. B2 secret scan + B3 egress（共享 netguard，一起做）
6. 文档更新 + 前端 build（server/static 产物一并提交）
7. 全量验证：pytest（基线 192）+ vitest（基线 9）+ `npm run build`，提交推送 main

**TDD 纪律**：每个工具先写失败测试再实现；集成测试经 ws 流用 MockLLMAdapter 的 tool_use 触发真实工具执行；所有新工具注册进默认 tool registry 与 enabled_tools。

## 不做的事（YAGNI）

- web_search（需额外 API key，v2 再议）
- 语义/embedding 搜索、浏览器自动化、交互式调试器
- 包管理器封装（execute_shell 兜底）
- Settings UI 工具开关（现有 enabled_tools 默认列表即可，Settings 页当前不渲染工具勾选）
- git commit/push 工具（写操作走 execute_shell + 护栏）
- 长期记忆工具（需 DB 设计，独立立项）
