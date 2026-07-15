# SPEC: Lite Agent Harness

> 一个轻量级、模型无关的 Coding Agent Harness，从零构建，具备确定性护栏与 mock 驱动测试能力。

**日期**: 2026-07-15
**状态**: 已确认
**下一步**: writing-plans

---

## 1. 问题陈述

### 1.1 要解决的问题

当 LLM 能完成大部分编码工作时，工程的价值落在 **harness 层**：决策封装、工具分发、治理护栏、反馈闭环、上下文记忆、声明式配置。核心等式是 **Agent = LLM + Harness**——LLM 负责"下一步做什么"的决策，harness 负责把一个只会产生文字的模型封装成一台能稳定、可靠工作的系统。

现有 agent 框架（LangChain AgentExecutor、AutoGen、CrewAI 等）将核心循环、治理、反馈作为框架黑盒提供。开发者调用的是 `agent.run()`，而非理解并编码这些机制。本项目反其道而行：**从零构建 harness 内核**，每个机制都是自己编写的确定性代码，剥离真实 LLM 后仍可通过 mock LLM 进行单元测试验证。

### 1.2 目标用户

独立开发者——在自己的机器上运行，用自己的 API key，借助 agent 完成编码任务（修 bug、写测试、重构代码、分析代码库）。

### 1.3 为什么值得做

- **教育价值**：只有亲手造过 harness，才能理解 agent 系统的工程边界在哪里，区分"写了一个机制"和"写了一句提示词"
- **实用价值**：一个轻量、可单测、可 mock 的 harness 是 agentic SE 研究的基础设施——可以在可控条件下实验不同的护栏策略、反馈信号、自我修正算法
- **工程价值**：展示"确定性机制 + 模拟 LLM"这一测试范式如何应用于 agent 系统

---

## 2. 用户故事

| ID | 用户故事 | INVEST 验证 |
|----|---------|------------|
| US-01 | 作为开发者，我希望通过 Web 界面输入编码任务（如"修复 test_login 的 bug"），让 agent 自主规划并执行，实时看到 LLM 的思考过程和工具调用结果 | I-独立, V-可评估 |
| US-02 | 作为开发者，当 agent 运行测试失败时，我希望它自动分析失败原因并修正代码，而不是让我手动检查日志告诉它哪里错了 | I-独立, N-可协商 |
| US-03 | 作为开发者，当 agent 尝试执行危险操作（如 `rm -rf /` 或强制推送主分支）时，我希望系统能拦截该操作并等待我明确批准 | I-独立, E-可估算 |
| US-04 | 作为开发者，我希望在设置页面安全录入我的 API key（Anthropic/OpenAI），key 不会明文出现在日志、配置文件或 Git 历史中，查看状态时仅显示掩码（如 `sk-...ab12`） | I-独立, T-可测试 |
| US-05 | 作为开发者，我希望 agent 的操作被限制在项目目录内——读写系统文件（如 `/etc/passwd`）或越界写入应被自动拒绝 | I-独立, S-小粒度 |
| US-06 | 作为开发者，我希望通过配置文件声明 agent 的行为约束（用哪个模型、沙箱根目录、最大重试次数），而不是在代码中硬编码 | I-独立, S-小粒度 |
| US-07 | 作为开发者，当 agent 反复修正超过 3 次仍未通过测试时，我希望它停止并让我介入，避免死循环浪费 token | I-独立, V-可评估 |
| US-08 | 作为开发者，我希望通过 Docker 一键部署或在本地直接运行，并能安全地配置自己的 API key | I-独立, T-可测试 |

---

## 3. 功能规约

### 3.1 Agent 主循环（状态机引擎）

**状态**：`IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → PLANNING → ... → COMPLETED`，另有 `AWAITING_HUMAN` 和 `ERROR` 分支。

**输入**：用户任务描述（文本字符串）

**行为**：
- `IDLE`：等待用户输入，收到任务 → `PLANNING`
- `PLANNING`：组装上下文（系统提示 + 记忆 + 工具列表 + 对话历史）→ 调用 LLM → 流式返回文本给前端
  - 若 LLM 返回 `stop_reason == "complete"` → `COMPLETED`
  - 若 LLM 返回 `stop_reason == "tool_use"` → `EXECUTING`
- `EXECUTING`：提取工具调用 → 过护栏 → 若拦截 → `AWAITING_HUMAN`；若通过 → 分发执行 → `OBSERVING`
- `AWAITING_HUMAN`：等待用户 WebSocket 消息（approve/reject）→ approve → 执行 → `OBSERVING`；reject → `PLANNING`
- `OBSERVING`：调用反馈分析器 → PASS → `PLANNING`（继续）；FAIL → `CORRECTING`（若重试次数 < 上限）；UNKNOWN → `PLANNING`
- `CORRECTING`：组装失败上下文 → 回灌 LLM → 回 PLANNING；若超过 3 次重试 → `COMPLETED`（附带失败摘要）
- `COMPLETED`：汇总执行统计（token 用量、工具调用次数、最终状态）→ 等待下一次任务

**边界条件**：
- 最大迭代步数：50 步（防止 LLM 无限规划）
- 每次 LLM 调用超时：60 秒
- 每次工具调用超时：30 秒
- 最大重试修正：3 次

**错误处理**：
- LLM API 错误（限流、鉴权失败、网络超时）→ 状态转为 `ERROR`，通知前端显示错误信息
- 工具执行异常（进程崩溃、超时）→ `OBSERVING` 判定为 FAIL，进入正常修正循环
- 凭据未配置 → `IDLE` 状态即检测，引导用户前往设置页面

### 3.2 LLM 抽象层

**输入**：消息列表（system/user/assistant/tool）、可用工具定义列表、是否流式

**行为**：将统一格式转换为各供应商原生 API 格式，发起调用，将响应统一为 `LLMResponse`

**输出**：`LLMResponse(content, tool_calls, stop_reason, usage)`

**支持的供应商**：
- Anthropic Messages API（Claude Sonnet 5 / Opus 4 / Haiku 4.5）
- OpenAI Chat Completions API（GPT-4o / GPT-4.1）
- MockLLM（返回预编程的响应序列，供单测使用）

**切换方式**：通过配置文件 `model.provider` 字段指定

**错误处理**：API 错误封装为 `LLMError` 异常，包含状态码和原始消息，由主循环统一处理

### 3.3 工具分发

**工具注册**：通过 `ToolRegistry.register(tool)` 注册，tool 实现 `Tool` 接口（`name`, `description`, `parameters_schema`, `execute`）

**内置工具**：

| 工具 | 功能 | 参数 |
|------|------|------|
| `read_file` | 读取文件内容 | `path: str`, `offset?: int`, `limit?: int` |
| `write_file` | 创建/覆写文件 | `path: str`, `content: str` |
| `execute_shell` | 在沙箱中执行命令 | `command: str`, `cwd?: str` |
| `run_tests` | 运行 pytest 并收集结果 | `path?: str`（默认 `tests/`） |
| `search_code` | 在代码库中搜索（ripgrep） | `pattern: str`, `path?: str`, `glob?: str` |

**扩展**：新增工具实现 `Tool` 接口并注册即可，无需改动核心代码

**工具执行结果**：返回统一的 `ToolResult(tool_name, exit_code, stdout, stderr, duration_ms, structured)`，其中 `structured` 为反馈分析器提供解析后的结构化数据

### 3.4 治理护栏（治理维度重点）

三层沙箱架构，按序执行：

**Layer 1 — 路径沙箱**：
- 所有 `read_file` 和 `write_file` 调用先过路径沙箱
- 将目标路径 `resolve()` 后检查是否在允许目录内
- `write_file` 限制在项目根目录内
- `read_file` 限制在项目根目录 + 系统 include/lib 目录（白名单）
- 越界操作直接 `BLOCK`，不进入后续层

**Layer 2 — 命令白名单**：
- 所有 `execute_shell` 调用的命令提取第一个 token（可执行文件名）
- 对照白名单（`ls`, `git`, `python`, `pytest`, `pip`, `npm`, `node`, `docker`, `make`, `grep`, `find`, `cat`, `echo` 等）
- 不在白名单 → `ASK_HUMAN`，弹到前端等审批
- 用户可在配置中的 `command_whitelist_extra` 扩展白名单

**Layer 3 — 正则黑名单**：
- 对白名单内命令的**参数**做危险模式匹配
- 规则：`(pattern, action, reason)` 三元组，如 `(r"rm\s+-rf\s+/", BLOCK, "递归删除根目录")`
- 匹配 → `BLOCK` 或 `ASK_HUMAN`

**进程隔离**：
- 所有命令通过 `subprocess.run(shell=False, timeout=30)` 执行
- `shell=False` 防止 shell 注入和命令链
- `timeout` 防止死循环或资源耗尽

**HITL 审批流**：
- 当护栏返回 `ASK_HUMAN` 时，状态机转入 `AWAITING_HUMAN`
- 前端弹出 GuardrailModal，显示具体命令、参数、风险原因
- 用户 approve → 继续执行；reject → 回到 PLANNING

### 3.5 反馈分析器（反馈闭环重点）

**核心职责**：将工具执行结果解析为客观的 `Feedback` 信号，驱动状态机转换。这是一个确定性解析器，不是提示词——移除 LLM 后仍可独立测试。

**策略分发**：

| 工具 | 判定逻辑 | 结构化提取 |
|------|---------|-----------|
| `run_tests` | `exit_code == 0` 且 pytest JSON 报告中 `failed == 0` | 提取失败用例的 file/function/line/message |
| `execute_shell` | `exit_code` | `exit_code == 0` → PASS，否则 → FAIL（附 stderr）|
| `write_file` | 文件存在性 + 语法编译检查 | 对 `.py` 文件额外跑 `compile()`，提取 SyntaxError |
| `read_file` | 无客观判定 | → UNKNOWN（交 LLM 自行判断）|
| `search_code` | 无客观判定 | → UNKNOWN |

**反馈结构**：

```python
Feedback:
    verdict: "pass" | "fail" | "warning" | "unknown"
    failures: [ {file, line, function, message} ]
    summary: str          # 人类可读的摘要
    suggested_fix: str    # 供 LLM 消费的修正提示
    retry_count: int
```

**多轮修正策略**：
- 首次 FAIL → 组装修正上下文（失败详情 + diff）→ 回灌 LLM → 重新执行
- 二次 FAIL → 同上，但额外注入"这是第 2 次重试，请更加谨慎"的提示
- 三次 FAIL → 强制终止，`COMPLETED` 附带失败摘要，通知用户介入
- 同一失败反复出现（连续 3 次相同错误信息）→ 提前终止，判断为"LLM 无法解决此问题"

### 3.6 记忆管理

**三层记忆模型**：

| 层 | 内容 | 存储 | 加载策略 |
|----|------|------|---------|
| 项目约定 | `CLAUDE.md`、`.editorconfig`、`.gitignore` 等 | 项目根目录（已有文件）| 启动时全量加载（< 2KB）|
| 决策记录 | 历史架构决策、为什么选 A 不选 B | `.harness/memory/decisions/*.json` | 按文件名关键词匹配，最多 5 条 |
| 学习记录 | 过去的错误与修正、成功的修正策略 | `.harness/memory/learnings/*.json` | 最近 20 条 + 按标签检索 |

检索方式：文件名 + 标签匹配 + 最近修改时间排序。不引入向量数据库。

### 3.7 配置管理

**配置文件**：`.harness/config.yaml`（项目级）、`~/.harness/config.yaml`（全局级）

**加载优先级**：项目级 > 全局级 > 内置默认值。列表字段追加，标量字段覆盖。

**可配置项**：
- `model.provider` / `model.model_id` / `model.max_tokens`
- `guardrails.max_retries` / `guardrails.sandbox_root` / `guardrails.command_whitelist_extra` / `guardrails.timeout_seconds`
- `tools.enabled`
- `memory.max_context_tokens` / `memory.learnings_limit`

### 3.8 凭据管理

**存储方案**：
- 桌面环境（PyInstaller 二进制）：优先系统钥匙串（`keyring` 库 → Windows Credential Manager / macOS Keychain / Linux Secret Service）
- Docker 环境：AES-GCM 加密文件存储，主密码通过环境变量 `HARNESS_KEY_PASSWORD` 传入

**管理流程**：
- **录入**：前端密码框输入，后端加密存储，不在日志中记录
- **查看状态**：返回掩码 `sk-...ab12`（前 3 后 4 字符），绝不回显明文
- **更新**：覆盖旧值
- **清除**：删除存储条目

**威胁模型**：
- API key 绝不硬编码在源码中
- API key 绝不进入 Git 历史（`.harness/` 和加密文件在 `.gitignore` 中）
- API key 绝不出现在日志或终端输出中
- 进程环境变量对同用户的其他进程可见——这是 Docker 环境的已知风险
- 若攻击者获得主密码 + 加密文件，可解密所有 key——这是静态存储的固有风险

### 3.9 Web API

**WebSocket** (`/ws/session`)：

双向 JSON 消息流。客户端发送：`task.submit`, `guardrail.approve`, `guardrail.reject`, `session.cancel`。服务端发送：`llm.stream`, `tool.invoke`, `tool.result`, `guardrail.pending`, `state.change`, `feedback.analysis`, `session.complete`, `session.error`。

**REST**：
- `GET /api/config` — 获取当前配置
- `PUT /api/config` — 更新配置
- `GET /api/credentials/status` — 所有 provider 的 key 掩码状态
- `POST /api/credentials` — 录入/更新 key
- `DELETE /api/credentials/{provider}` — 删除 key
- `GET /api/session/history` — 历史会话列表

---

## 4. 非功能性需求

### 4.1 性能

- WebSocket 连接建立 < 500ms
- LLM 流式首个 token 延迟取决于供应商（自身不增加 > 100ms 开销）
- 工具执行结果返回 < 30 秒（超时强制终止）
- 前端渲染 1000 条消息无明显卡顿（虚拟列表）

### 4.2 安全（含凭据威胁模型）

见 §3.8 凭据管理威胁模型。补充：
- WebSocket 连接仅限本地（`localhost:8000`）——单用户工具不需对外暴露
- 护栏三层设计确保危险操作均有代码级拦截
- `subprocess.run(shell=False)` 防止 shell 注入
- 无用户认证系统（单用户本地工具，不暴露到公网）

### 4.3 可用性

- 首次启动引导用户完成凭据配置（设置页面高亮未配置的 provider）
- 错误消息应具体且有可操作性（如"Anthropic API key 未配置，请在设置页面录入"）
- 护栏审批弹窗清晰展示：具体命令、参数、风险原因、批准/拒绝按钮

### 4.4 可观测性

- 状态机每次转换在前端实时展示（StateIndicator 小圆点 + 颜色）
- 每次 LLM 调用的 token 用量累计显示
- 每次工具调用的耗时、exit code 在 ToolCard 中展示
- 服务端日志记录：状态转换、LLM 调用、护栏拦截、工具执行（不含 API key）

---

## 5. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (React + Open Design)           │
│   ChatView │ ToolPanel │ Settings │ GuardrailModal        │
└──────────────────────┬──────────────────────────────────┘
                       │ WebSocket + REST
┌──────────────────────┴──────────────────────────────────┐
│                 FastAPI Server                           │
│   WS Handler │ Credential API │ Config API               │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                 Agent Core (State Machine)               │
│                                                          │
│   ┌─────────┐    ┌──────────┐    ┌───────────────┐      │
│   │  Loop   │───▶│ Guardrail│───▶│ Tool Dispatch │      │
│   │ Engine  │    │ Engine   │    │   Registry    │      │
│   └─────────┘    └──────────┘    └───────────────┘      │
│        │                               │                │
│   ┌────┴────┐                   ┌──────┴──────┐         │
│   │  LLM    │                   │  Feedback   │         │
│   │Adapter  │                   │  Analyzer   │         │
│   └─────────┘                   └─────────────┘         │
│                                                          │
│   ┌─────────┐    ┌──────────┐    ┌───────────────┐      │
│   │ Memory  │    │  Config  │    │  Credential   │      │
│   │ Manager │    │  Manager │    │  Manager      │      │
│   └─────────┘    └──────────┘    └───────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 5.1 状态机转换图

```
         用户输入
    IDLE ──────────▶ PLANNING ──(LLM 决定完成)──▶ COMPLETED
                      │    ▲
                      │    │ (继续)
             工具调用 │    │
                      ▼    │
                  EXECUTING─┘
                      │
          ┌──(危险)──┴──(安全)──┐
          ▼                      ▼
   AWAITING_HUMAN           OBSERVING
          │                      │
    批准  │  │拒绝     ┌──失败──┴──成功──┐
          ▼  ▼        ▼                 ▼
      EXECUTING  PLANNING    CORRECTING ──▶ PLANNING
                                   │
                              COMPLETED (超过重试次数)
```

### 5.2 外部依赖

- **LLM 供应商**：Anthropic Messages API、OpenAI Chat Completions API（通过 HTTP，使用官方 SDK）
- **ripgrep**：`search_code` 工具依赖（系统须安装 `rg`），若无则回退到 Python `glob` + 内置 `grep`
- **pytest**：`run_tests` 工具依赖项目内安装的 pytest（通过 `--json-report` 输出结构化结果）
- **keyring** 库：系统钥匙串访问（PyInstaller 分发时绑定；Docker 中降级）
- **Node.js / npm**：前端构建（仅开发期；分发时前端已构建为静态文件）

---

## 6. 数据模型

### 6.1 核心实体

**Session**：一次完整的任务执行会话
```
Session:
    id: str (UUID)
    task: str                      # 用户原始任务
    state: State                   # 当前状态
    messages: list[Message]        # 完整对话历史
    tool_calls: list[ToolCall]     # 所有工具调用记录
    retry_count: int               # 当前修正重试次数
    total_tokens: TokenUsage       # 累计 token 用量
    created_at: datetime
    completed_at: datetime | None
```

**Message**：
```
Message:
    role: "system" | "user" | "assistant" | "tool"
    content: str | list[ContentBlock]
    tool_call_id: str | None       # tool role 时关联
    tool_result: ToolResult | None # tool role 时附带
```

**ToolCall**：
```
ToolCall:
    id: str
    name: str
    arguments: dict
    result: ToolResult | None
    guardrail_result: GuardResult | None
```

**ToolResult**：
```
ToolResult:
    tool_name: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    structured: dict | None
```

**Feedback**：
```
Feedback:
    verdict: "pass" | "fail" | "warning" | "unknown"
    failures: list[{file, line, function, message}]
    summary: str
    suggested_fix: str
    retry_count: int
```

**GuardResult**：
```
GuardResult:
    action: "allow" | "block" | "ask_human"
    layer: int                    # 1/2/3 表示哪一层的判定
    reason: str
```

---

## 7. 凭据与分发设计

### 7.1 凭据方案

见 §3.8 凭据管理。总结：
- 桌面端：系统钥匙串（keyring）
- Docker 端：AES-GCM 加密文件 + 环境变量传入主密码
- 首次运行引导录入，查看只显示掩码，支持更新/清除
- `.gitignore` 排除 `.harness/`、`.env`、加密密钥文件

### 7.2 分发

| 形态 | 构建方式 | 运行命令 | 凭据 | 已知限制 |
|------|---------|---------|------|---------|
| Docker | `docker build -t harness .` | `docker run -p 8000:8000 -e HARNESS_KEY_PASSWORD=<pw> -v $(pwd):/workspace harness` | AES + env 主密码 | 需 Docker 运行时；若系统无 ripgrep，search_code 回退至 Python grep |
| PyInstaller | `pyinstaller harness.spec` | `./harness`（双击或终端）| 系统钥匙串 | 仅 Windows/macOS/Linux x86_64；需在目标平台构建；首次运行可能触发 SmartScreen/ Gatekeeper 警告 |

CI（GitHub Actions）：
- `make test` → 运行全部单元测试和集成测试
- `make docker-build` → 构建并推送 Docker 镜像至 GitHub Container Registry
- `make binary` → 构建 PyInstaller 产物，上传为 Release Artifact

---

## 8. 技术选型与理由

| 选择 | 技术 | 理由 |
|------|------|------|
| 语言 | Python 3.12+ | Anthropic/OpenAI SDK 均 Python 优先；pytest + mock 生态成熟；开发速度快；asyncio 原生支持 WebSocket |
| 架构 | 状态机 | 确定性最强，每个转换可独立单测；符合"移除 LLM 后仍可验证"的核心判准 |
| Web 框架 | FastAPI | 原生 async/await；WebSocket 支持；自动 OpenAPI 文档 |
| 前端 | React + Open Design | 生态最大，Open Design 提供设计系统和 skill；流式更新 UI 成熟 |
| LLM SDK | 官方 anthropic + openai 包 | 直接使用供应商 SDK 而非第三方封装，API 更新最及时 |
| 测试 | pytest + pytest-asyncio | 标准选择；mock LLM 适配器注入 |
| 前端构建 | Vite | 快速、现代、React 默认 |
| 分发 | Docker + PyInstaller | 两选覆盖面广——Docker 屏蔽环境差异，PyInstaller 提供原生体验 |

不引入数据库：单用户工具不需要持久化层——会话历史存内存（刷新即清），配置和记忆存文件系统（JSON/YAML），凭据存钥匙串/加密文件。

---

## 9. 领域与机制设计

### 9.1 领域（Coding）的特征

- **反馈信号**：测试通过/失败（exit code）、lint 警告、类型检查结果、编译错误。这些信号是客观、确定、可机器解析的
- **危险动作**：删除文件（`rm -rf`）、强制推送（`git push --force`）、数据库破坏（`DROP TABLE`）、管道执行远程脚本（`curl | sh`）、写入系统目录
- **所需工具**：文件读写、shell 执行、测试运行、代码搜索
- **记忆需求**：项目编码规范、历史架构决策、成功/失败的修正模式

### 9.2 重点维度：反馈闭环 + 治理护栏

选择双重点基于以下权衡：

- **反馈闭环（主贡献）**：这是 harness 的"灵魂"——没有它 agent 就是"LLM 说啥我做啥"的执行器。确定性解析器 + 分类器 + 多轮修正策略的组合天生由代码构成，完美符合"移除 LLM 后仍可单测"的判准。演示效果最直观：注入失败 → 检测 → 修正 → 通过
- **治理护栏（次要主贡献）**：三层沙箱（路径 + 白名单 + 黑名单）是确定性代码的范本——每一层都可以独立单测。正则黑名单在真实攻防中存在绕过风险（编码、base64 间接执行等），但本项目将这一局限性明确记录，并在 SPEC 中讨论更深层治理方案（命令 AST 解析、系统级 seccomp/AppArmor）的适用场景

### 9.3 机制编码方式

| 机制 | 编码方式（非提示词）| 如何单测 |
|------|-------------------|---------|
| 反馈判定 | `FeedbackAnalyzer.analyze(ToolResult)` 纯函数 | 构造 `ToolResult(exit_code=1, stdout="...")`，断言 `verdict == FAIL` |
| 失败提取 | `PytestParser.parse(json_report)` → 结构化 `list[Failure]` | 构造 pytest JSON 报告字符串，断言提取的 file/line/function 正确 |
| 护栏 Layer 1 | `PathSandbox.validate(path, mode)` → allow/block | `validate("/etc/passwd", "read")` 断言 block |
| 护栏 Layer 2 | `Whitelist.check(command)` → allow/ask_human | `check("curl")` 断言 ask_human |
| 护栏 Layer 3 | 正则表逐条匹配 | 每个三元组构造输入，断言预期 action |
| 重试策略 | `RetryPolicy.should_retry(count, last_failure)` → bool | `should_retry(3, ...)` 断言 False |
| 记忆检索 | 文件名 + 标签匹配 + 排序 | 构造文件集，断言检索结果 |
| 配置合并 | 深度合并 + 优先级覆盖 | 三组 YAML 输入，断言最终值 |

---

## 10. 验收标准

| 编号 | 标准 | 验证方式 |
|------|------|---------|
| AC-01 | 用户通过 Web 界面提交编码任务，agent 自主规划执行，流式输出可见 | 手动端到端测试 |
| AC-02 | 注入一次测试失败，agent 自动分析、修正、重跑至通过 | 机制演示脚本 `demo_feedback_loop.py` |
| AC-03 | `rm -rf /`、`DROP TABLE` 等危险操作被护栏拦截 | 机制演示脚本 `demo_guardrail.py` |
| AC-04 | 路径越界（读写 `/etc/passwd`）被 Layer 1 拦截 | 单测 `test_guardrail_sandbox.py` |
| AC-05 | 不在白名单的命令被 Layer 2 拦截，弹到前端等审批 | 集成测试 + 手动 |
| AC-06 | API key 录入后只显示掩码，不出现明文于日志/Git/终端 | 单测 `test_credential_mask.py` |
| AC-07 | 连续 3 次修正失败后 agent 停止并通知用户 | 单测 `test_feedback_retry.py` |
| AC-08 | `make test` 一键运行全部单元测试（0 网络依赖）和集成测试 | CI 执行通过 |
| AC-09 | Docker `docker run` 一键启动，浏览器可访问 Web 界面 | 手动端到端 |
| AC-10 | PyInstaller 二进制可运行，凭据通过系统钥匙串管理 | 手动端到端 |
| AC-11 | 切换 `model.provider` 配置可在 Anthropic / OpenAI / Mock 间切换 | 单测验证 Mock 注入正确 |
| AC-12 | 所有核心机制（护栏、反馈、重试、工具分发）在 mock LLM 下确定性可测 | CI 全绿 |

---

## 11. 风险与未决问题

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| LLM API 不稳定（限流、超时、格式变更）| agent 任务中断 | 重试 + 指数退避；状态机保留上下文可恢复 |
| 正则护栏被编码/间接执行绕过 | 危险命令漏过 Layer 3 | Layer 1（路径）+ Layer 2（白名单）提供纵深防御；文档记录局限 |
| 反馈分析器误判（false positive/negative）| agent 做无意义修正或漏掉错误 | 解析器以 exit code + 结构化报告为权威来源，不做启发式猜测 |
| LLM 上下文窗口超限 | 长对话/大文件导致 API 错误 | 配置 `max_context_tokens`，MemoryManager 控制注入内容长度；工具返回内容截断 |
| 前端流式渲染性能 | 长时间流式输出导致浏览器卡顿 | 虚拟列表 + requestAnimationFrame 批量更新 |
| subprocess 超时后僵尸进程 | 资源泄漏 | `subprocess.run(timeout=...)` 自动 kill；额外 `psutil` 兜底 |
| PyInstaller 首次运行系统拦截 | Windows SmartScreen / macOS Gatekeeper | README 写清处理步骤 |

---

*本文档由 brainstorming 流程产出，确认后进入 writing-plans 阶段。*
