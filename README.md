# Glimmer

<p align="center">
  <strong>轻量级、模型无关的 AI 编程智能体 — 确定性护栏、Docker 沙箱隔离、生产就绪</strong>
</p>

<p align="center">
  <a href="https://github.com/jeannie-jy/Glimmer/actions"><img src="https://img.shields.io/github/actions/workflow/status/jeannie-jy/Glimmer/ci.yml?branch=main&style=flat-square" alt="CI"></a>
  <a href="https://glimmer-l5yr.onrender.com"><img src="https://img.shields.io/badge/live-demo-F8A4C8?style=flat-square" alt="Live Demo"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square" alt="Python"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-22%2B-green?style=flat-square" alt="Node"></a>
  <a href="https://hub.docker.com/"><img src="https://img.shields.io/badge/docker-ready-brightgreen?style=flat-square" alt="Docker"></a>
  <a href="#测试"><img src="https://img.shields.io/badge/tests-94%2B%20passing-brightgreen?style=flat-square" alt="Tests"></a>
</p>

<p align="center">
  <em>"每一次编码，都是一场施法" — SpellCraft your code with Glimmer.</em>
</p>

<p align="center">
  🌐 <strong>在线体验</strong>：<a href="https://glimmer-l5yr.onrender.com">https://glimmer-l5yr.onrender.com</a>
</p>

---

## 目录

- [概述](#概述)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [配置说明](#配置说明)
- [智能体循环](#智能体循环)
- [护栏系统](#护栏系统)
- [反馈与自修正](#反馈与自修正)
- [LLM 供应商](#llm-供应商)
- [工具参考](#工具参考)
- [API 参考](#api-参考)
- [WebSocket 协议](#websocket-协议)
- [前端架构](#前端架构)
- [测试](#测试)
- [安全设计](#安全设计)
- [性能指标](#性能指标)
- [项目结构](#项目结构)
- [贡献指南](#贡献指南)
- [常见问题](#常见问题)
- [设计系统](#设计系统)
- [许可证](#许可证)

---

## 概述

Glimmer 是一个**从零构建的生产级 AI 编程智能体 Harness**。与将智能体循环封装为黑盒的框架不同，Glimmer 将每个机制——状态转换、护栏检查、反馈分析、重试策略——都暴露为**确定性的、可测试的代码**。

### 核心哲学

> **Agent = LLM + Harness**
>
> LLM 决定「下一步做什么」，Harness 确保它**安全、可靠、可验证**地完成。

### 设计原则

| 原则 | 实现方式 |
|------|---------|
| **代码而非提示词** | 状态机、反馈分析器、护栏均为纯函数代码——不依赖 LLM 推断。可用 Mock LLM 单元测试 |
| **纵深防御** | 三层护栏系统：路径沙箱 → 命令白名单 → 正则黑名单 |
| **供应商无关** | 可插拔 LLM 适配器。Anthropic / OpenAI / DeepSeek / 通义千问 / Ollama 自由切换 |
| **默认可观测** | WebSocket 实时流式传输 Token、工具调用、状态转换、反馈判定 |
| **双模式部署** | 单用户本地模式（零基础设施）或多用户 Docker 部署（PostgreSQL） |

### 功能矩阵

| 功能 | 本地模式 | 部署模式 |
|------|---------|---------|
| 状态机驱动智能体循环 | ✅ | ✅ |
| 多供应商 LLM | ✅ | ✅ |
| WebSocket 实时流式 | ✅ | ✅ |
| 三层护栏 | ✅ | ✅ |
| 确定性反馈分析 | ✅ | ✅ |
| 自修正 + 重试策略 | ✅ | ✅ |
| 记忆持久化 | ✅ | ✅ |
| Docker 沙箱隔离 | — | ✅ |
| GitHub OAuth + JWT | — | ✅ |
| PostgreSQL 持久化 | — | ✅ |
| 多用户支持 | — | ✅ |
| API 限流 | — | ✅ (slowapi) |
| Nginx 反向代理 | — | ✅ |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                     Web UI (React + TypeScript)                   │
│   ChatView │ ToolPanel │ Settings │ GuardrailModal │ FilePanel   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ WebSocket + REST
┌────────────────────────────┴─────────────────────────────────────┐
│                      FastAPI Server                               │
│   WS Handler │ Auth Routes │ Config API │ Session API │ Files API│
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                 Agent Core (确定性状态机)                          │
│                                                                   │
│  ┌──────────┐   ┌─────────────┐   ┌───────────────┐             │
│  │  Loop    │──▶│  Guardrail  │──▶│ Tool Dispatch  │             │
│  │ Engine   │   │  Engine (3L)│   │   Registry     │             │
│  └──────────┘   └─────────────┘   └───────────────┘             │
│       │                                          │                │
│  ┌────┴─────┐                            ┌──────┴──────┐        │
│  │   LLM    │                            │  Feedback   │        │
│  │ Adapters │                            │  Analyzer   │        │
│  └──────────┘                            └─────────────┘        │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐                 │
│  │  Memory  │   │  Config  │   │  Credential   │                 │
│  │  Manager │   │  Manager │   │  Manager      │                 │
│  └──────────┘   └──────────┘   └──────────────┘                 │
└──────────────────────────────────────────────────────────────────┘
```

### 状态机

```
          提交任务
   IDLE ──────────────▶ PLANNING ────(llm决定完成)───▶ COMPLETED
                          │    ▲
                          │    │ (测试通过,继续)
               需要工具   │    │
                          ▼    │
                      EXECUTING─┘
                          │
              ┌──(拦截)─┴─(安全)──┐
              ▼                    ▼
       AWAITING_HUMAN          OBSERVING
              │                    │
    批准│  │拒绝   ┌──失败──┴──成功──┐
        ▼  ▼       ▼                ▼
   EXECUTING  PLANNING      CORRECTING ──▶ PLANNING
                                   │
                                   ▼
                             COMPLETED (超过重试上限)
```

状态机是一个**纯函数**（`harness/state_machine.py`，71 行），每次状态转换都是确定性计算——LLM 不参与路由决策。这意味着整个智能体控制流都可以用 Mock LLM 进行单元测试。

---

## 快速开始

### 前置条件

- **本地模式**：Python ≥ 3.12、pip
- **部署模式**：Docker & Docker Compose、[GitHub OAuth App](https://github.com/settings/developers)

### 本地模式（单用户，零基础设施）

```bash
# 克隆并安装
git clone https://github.com/jingyu-wang/lite-agent-harness.git
cd lite-agent-harness
pip install -r requirements.txt

# 启动开发服务器
make dev
# 浏览器打开 http://localhost:8000
```

打开右侧 Settings 面板，填入 LLM Provider 和 API Key，即可开始使用。

### 部署模式（多用户，需要 Docker）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env — 填入 GITHUB_CLIENT_ID、GITHUB_CLIENT_SECRET 和密码

# 2. 一键部署
make deploy
# 浏览器打开 http://localhost
```

`make deploy` 会自动完成：
1. 构建沙箱镜像（`Dockerfile.sandbox`）
2. 启动 nginx + API + PostgreSQL

---

## 部署指南

### 生产架构

```
互联网 ──▶ Nginx (80/443) ──▶ FastAPI (8000) ──▶ Docker 沙箱 (每会话)
                    │                    │
                    ▼                    ▼
             静态文件              PostgreSQL (5432)
```

### Docker Compose 服务

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| `nginx` | `nginx:alpine` | 80, 443 | 反向代理、静态文件、WebSocket 升级 |
| `api` | 自构建 | 8000 | FastAPI 应用服务 |
| `db` | `postgres:16-alpine` | 5432 | 用户数据、会话、消息 |

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `GLIMMER_SECRET_KEY` | 是 | — | JWT 签名 + AES 密钥派生的主密钥。生成：`openssl rand -hex 32` |
| `GITHUB_CLIENT_ID` | 是 | — | GitHub OAuth App 客户端 ID |
| `GITHUB_CLIENT_SECRET` | 是 | — | GitHub OAuth App 客户端密钥 |
| `DATABASE_URL` | 是 | — | PostgreSQL 连接串（格式：`postgresql+asyncpg://user:pass@host:5432/db`） |
| `DB_PASSWORD` | 是 | — | PostgreSQL 用户密码 |
| `OAUTH_REDIRECT_URI` | 否 | `http://localhost:8000/api/auth/callback` | OAuth 回调地址 |
| `DOCKER_HOST` | 否 | `unix:///var/run/docker.sock` | Docker 守护进程地址 |
| `SANDBOX_IMAGE` | 否 | `glimmer-sandbox:latest` | 沙箱容器镜像 |
| `WORKSPACE_ROOT` | 否 | `/workspace` | 共享工作区挂载点 |
| `FRONTEND_URL` | 否 | `http://localhost` | 前端 URL（用于 OAuth 重定向） |

### 手动 Docker 构建

```bash
# 构建沙箱镜像
docker build -f Dockerfile.sandbox -t glimmer-sandbox:latest .

# 构建应用镜像（多阶段：Node + Python）
docker build -t glimmer:latest .

# 运行
docker run -p 8000:8000 \
  -e GLIMMER_SECRET_KEY=$(openssl rand -hex 32) \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -v $(pwd)/workspace:/workspace \
  glimmer:latest
```

### PyInstaller 独立二进制

```bash
# 构建
pip install pyinstaller
pyinstaller pyinstaller.spec

# 运行
./dist/lite-agent-harness
```

### Render 云部署

在线体验地址：**[https://glimmer-l5yr.onrender.com](https://glimmer-l5yr.onrender.com)**

部署于 [Render](https://render.com) 平台，架构为 Web Service（FastAPI） + PostgreSQL（托管数据库）。

所需环境变量见[上表](#环境变量)，特别注意事项：
- `DATABASE_URL` 需将 Render 提供的 `postgres://` 改为 `postgresql+asyncpg://`
- `OAUTH_REDIRECT_URI` 设为 `https://glimmer-l5yr.onrender.com/api/auth/callback`
- `FRONTEND_URL` 设为 `https://glimmer-l5yr.onrender.com`

**已知限制**：Windows SmartScreen / macOS Gatekeeper 首次运行可能弹窗警告。若系统未安装 ripgrep，`search_code` 会回退到 Python grep。

---

## 配置说明

### 配置文件（`.harness/config.yaml`）

Glimmer 使用分层配置系统，优先级从高到低：

1. **项目配置**：`<项目根>/.harness/config.yaml`
2. **全局配置**：`~/.harness/config.yaml`
3. **内置默认值**

标量值覆盖，列表值追加。

```yaml
# .harness/config.yaml
model:
  provider: anthropic           # "anthropic" 或 "openai"
  model_id: claude-sonnet-5
  max_tokens: 4096

guardrails:
  max_retries: 3                # 最大自修正尝试次数
  sandbox_root: "."             # 路径沙箱根目录
  command_whitelist_extra: []   # 额外白名单命令
  timeout_seconds: 30           # 单次工具执行超时

tools:
  enabled:
    - read_file
    - write_file
    - execute_shell
    - run_tests
    - search_code

memory:
  max_context_tokens: 8000      # LLM 上下文窗口最大 Token 数
  learnings_limit: 20           # 最近注入的学习记录数
```

### Web UI Settings 面板

| 字段 | 说明 |
|------|------|
| **Provider** | `Anthropic`（内置）或 `OpenAI Compatible`（自定义 Base URL） |
| **Base URL** | OpenAI 兼容端点（DeepSeek / Qwen / Ollama / vLLM 等） |
| **Model Name** | 模型 ID（如 `claude-sonnet-5`、`deepseek-chat`、`qwen-plus`） |
| **API Key** | 你的 API 密钥（AES-256-GCM 加密存储） |

---

## 智能体循环

### 生命周期

```
1. IDLE           — 等待用户输入
2. PLANNING        — 组装上下文、调用 LLM、流式返回
3. EXECUTING       — 提取工具调用、过护栏、分发执行
4. OBSERVING       — 确定性分析工具执行结果
5. CORRECTING      — 将失败上下文回灌 LLM（最多 max_retries 次）
6. AWAITING_HUMAN  — 护栏拦截，等待用户批准
7. COMPLETED       — 任务结束（成功 / 失败 / 超重试次数）
8. ERROR           — 不可恢复错误（API 故障、鉴权失败、网络超时）
```

### 安全边界

| 限制 | 值 | 目的 |
|------|-----|------|
| 最大迭代次数 | 50 | 防止 LLM 无限规划 |
| LLM 调用超时 | 60 秒 | 单次 API 调用超时 |
| 工具执行超时 | 30 秒 | 单次工具调用超时 |
| 最大自修正次数 | 3 | 防止无限制重试 |
| 卡死检测 | 连续 3 次相同错误 | 提前终止不可恢复问题 |

---

## 护栏系统

Glimmer 采用**纵深防御**策略，三层串行检查：

### 第一层 — 路径沙箱

所有文件读写操作经过路径沙箱，使用 `pathlib.resolve()` 防止路径穿越（`../../../etc/passwd`）。

```python
# 权限检查
sandbox = PathSandbox(root="/safe/project")
result = sandbox.validate("/etc/passwd", "read")
# → GuardResult(action=BLOCK, layer=1, reason="Read outside sandbox")
```

### 第二层 — 命令白名单

提取可执行文件名，与可配置白名单比对。未知命令触发 `ASK_HUMAN`。

**默认白名单**：`ls`、`cat`、`git`、`python`、`pytest`、`pip`、`npm`、`node`、`docker`、`make`、`grep`、`find`、`echo`、`mkdir`、`cp`、`mv`、`rm`、`rmdir`、`chmod`、`cargo`、`cmake`、`npx` 等。

### 第三层 — 正则黑名单

对通过白名单的命令，检查其参数是否匹配危险模式。

| 模式 | 动作 | 示例 |
|------|------|------|
| `rm -rf /` | BLOCK | 递归删除根目录 |
| `DROP TABLE/DATABASE` | BLOCK | 数据库破坏操作 |
| `git push --force origin main` | ASK_HUMAN | 强制推送主分支 |
| `curl ... \| bash` | ASK_HUMAN | 远程脚本管道执行 |
| `chmod 777 /` | ASK_HUMAN | 根路径全局可写 |
| `dd if=` | ASK_HUMAN | 底层磁盘操作 |

> **⚠️ 已知局限**：正则匹配可被编码、base64 混淆、间接执行绕过。高安全需求场景请配合 seccomp/AppArmor 系统级沙箱。

---

## 反馈与自修正

### 确定性反馈分析器

`FeedbackAnalyzer` 是一个**纯函数**——不依赖 LLM 做判定。每种工具类型有专属的分析策略：

| 工具 | 判定逻辑 | 结构化提取 |
|------|---------|-----------|
| `run_tests` | `exit_code == 0` 且 pytest JSON 报告 `failed == 0` | 失败用例的 file/line/function/message |
| `execute_shell` | `exit_code` | 0 → PASS，非 0 → FAIL（附 stderr） |
| `write_file` | 写入成功 + Python `compile()` 语法检查 | SyntaxError 位置与信息 |
| `read_file` | 无客观判定 | → UNKNOWN（交 LLM 自行判断） |
| `search_code` | 无客观判定 | → UNKNOWN（交 LLM 自行判断） |

### 重试策略

```
第 1 次: "之前的尝试失败。请修复以下问题：..."
第 2 次: "第二次尝试仍然失败。请更加谨慎：..."
第 3 次: "最后一次尝试！如果再次失败，任务将终止：..."
→ 附带失败摘要终止，通知用户介入
```

**卡死检测**：连续 3 次失败签名完全一致（相同文件、函数、错误信息）→ 提前终止，节省 Token。

---

## LLM 供应商

### 支持的供应商

| 供应商 | 类型 | Base URL | 示例模型 | 备注 |
|--------|------|----------|---------|------|
| **Anthropic** | 原生 | 内置 | `claude-sonnet-5`、`claude-opus-4-8`、`claude-haiku-4-5` | Messages API，原生 tool-use |
| **OpenAI** | 原生 | 内置 | `gpt-4o`、`gpt-4.1` | Chat Completions API |
| **DeepSeek** | 兼容 | `https://api.deepseek.com` | `deepseek-chat`、`deepseek-reasoner` | OpenAI 兼容 |
| **Qwen（通义千问）** | 兼容 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus`、`qwen-max` | OpenAI 兼容 |
| **Ollama** | 兼容 | `http://localhost:11434/v1` | `llama3`、`mistral`、`codellama` | 本地自托管 |
| **vLLM** | 兼容 | 自定义 | 任意 | 自托管 |
| **任意 OpenAI 兼容** | 兼容 | 自定义 | 任意 | — |

### 配置示例

```yaml
# Anthropic
model:
  provider: anthropic
  model_id: claude-sonnet-5

# DeepSeek
model:
  provider: openai
  base_url: https://api.deepseek.com
  model_id: deepseek-chat

# 本地 Ollama
model:
  provider: openai
  base_url: http://localhost:11434/v1
  model_id: llama3
```

---

## 工具参考

### 内置工具

| 工具 | 描述 | 参数 | 超时 |
|------|------|------|------|
| `read_file` | 读取文件，支持 offset/limit | `path`、`offset?`、`limit?` | 10s |
| `write_file` | 创建或覆写文件 | `path`、`content` | 10s |
| `execute_shell` | 在沙箱中执行命令 | `command`、`cwd?` | 30s |
| `run_tests` | 运行 pytest 并收集结构化结果 | `path?`（默认 `tests/`） | 60s |
| `search_code` | ripgrep 搜索（Python 回退） | `pattern`、`path?`、`glob?` | 15s |

### 自定义工具

实现 `Tool` 抽象基类即可：

```python
from harness.tools.registry import Tool
from harness.models import ToolResult

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "LLM 可读的工具描述"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "arg1": {"type": "string", "description": "参数说明"}
            },
            "required": ["arg1"]
        }

    async def execute(self, arguments: dict) -> ToolResult:
        return ToolResult(tool_name="my_tool", exit_code=0, stdout="完成")
```

所有工具支持**双执行路径**：本地 subprocess 或 Docker 容器——由是否配置 Docker 管理器自动决定。

---

## API 参考

### WebSocket

**端点**：`ws://<host>/ws/session?token=<jwt>`

WebSocket 连接是 Agent 交互的主要通道，所有实时通信都通过此通道。

### REST 端点

#### 认证

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| `GET` | `/api/auth/login` | 无 | 重定向至 GitHub OAuth |
| `GET` | `/api/auth/callback?code=` | 无 | OAuth 回调，返回 JWT 重定向 |
| `GET` | `/api/auth/me` | Bearer | 当前用户信息 |

#### 配置

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| `GET` | `/api/config` | Bearer | 获取配置 |
| `PUT` | `/api/config` | Bearer | 更新配置（部分更新） |
| `POST` | `/api/config/credentials` | Bearer | 存储加密 API Key |
| `DELETE` | `/api/config/credentials` | Bearer | 删除 API Key |
| `GET` | `/api/credentials/status` | Bearer | 各 Provider 的 Key 状态 |
| `POST` | `/api/credentials` | Bearer | 存储 API Key（前端兼容） |
| `DELETE` | `/api/credentials/{provider}` | Bearer | 删除 Key（前端兼容） |

#### 会话

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| `GET` | `/api/sessions` | Bearer | 历史会话列表（最近 50） |
| `GET` | `/api/sessions/{id}` | Bearer | 会话详情（含消息） |
| `DELETE` | `/api/sessions/{id}` | Bearer | 删除会话及消息 |

#### 文件

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| `GET` | `/api/files?session_id=` | Bearer | 列出工作区文件 |
| `GET` | `/api/files/download?session_id=&path=` | Bearer | 下载工作区文件 |

---

## WebSocket 协议

### 客户端 → 服务端

| 消息类型 | 字段 | 说明 |
|---------|------|------|
| `task.submit` | `content`、`session_id?` | 提交编码任务 |
| `session.new` | — | 开始新会话 |
| `session.load` | `session_id` | 加载历史会话 |
| `session.cancel` | — | 取消当前任务 |
| `guardrail.approve` | — | 批准待定工具调用 |
| `guardrail.reject` | — | 拒绝待定工具调用 |
| `files.list` | — | 请求工作区文件列表 |
| `files.download` | `path` | 请求文件内容 |
| `files.upload` | `path`、`content` | 上传文件（base64 编码） |
| `files.delete` | `path` | 删除工作区文件 |

### 服务端 → 客户端

| 消息类型 | 字段 | 说明 |
|---------|------|------|
| `state.change` | `from`、`to` | 状态机转换通知 |
| `llm.response` | `content`、`tool_calls` | LLM 响应文本 + 工具调用 |
| `llm.stream` | `delta`、`index`、`done` | 流式 Token |
| `tool.invoke` | `tool`、`args` | 工具调用分发通知 |
| `tool.result` | `tool_name`、`exit_code`、`stdout`、`stderr`、`duration_ms` | 工具执行结果 |
| `guardrail.pending` | `action`、`reason`、`tool`、`args` | 护栏拦截通知 |
| `feedback.analysis` | `verdict`、`summary`、`failures`、`suggested_fix`、`retry_count` | 反馈分析结果 |
| `session.complete` | — | 任务完成 |
| `session.error` | `message` | 错误信息 |
| `session.created` | `session_id` | 新会话已创建 |
| `session.saved` | `session_id` | 会话已持久化 |
| `session.loaded` | `session_id`、`task`、`message_count` | 历史会话已加载 |
| `file.created` | `path` | 文件已创建 |
| `file.modified` | `path` | 文件已修改 |
| `files.list` | `files` | 工作区文件列表 |
| `files.content` | `path`、`content`、`error?` | 文件内容响应 |
| `files.deleted` | `path` | 文件已删除 |

---

## 前端架构

### 技术栈

| 层面 | 技术 | 说明 |
|------|------|------|
| 框架 | React 18 + TypeScript 5 | 组件化 SPA |
| 构建 | Vite 6 | 快速 HMR，优化构建 |
| 路由 | React Router v7 | 客户端路由，懒加载 |
| 动效 | Framer Motion v11 | 页面过渡、悬停效果、仙女运动 |
| 图标 | Lucide React | 1400+ 一致图标 |
| Markdown | react-markdown + remark-gfm | LLM 响应的 Markdown 渲染 |
| 代码高亮 | react-syntax-highlighter | 代码块高亮 |

### 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | `HomePage` | 首页：动画演示 + 功能卡片 + GitHub 统计 |
| `/about` | `AboutPage` | 项目哲学与架构概述 |
| `/guide` | `GuidePage` | 分步使用指南 |
| `/learn` | `LearnPage` | 学习资源与文档 |
| `/agent` | `AgentPage` | 智能体聊天（需认证） |
| `/login` | `LoginPage` | GitHub OAuth 登录 |

### Agent 页面布局

```
┌──────────────┬──────────────────────────┬──────────────┐
│   历史会话   │       聊天视图            │  设置/文件   │
│   侧边栏    │   ┌──────────────────┐    │   面板       │
│             │   │   消息列表       │    │              │
│             │   │   (可滚动)      │    │              │
│             │   └──────────────────┘    │              │
│             │   ┌──────────────────┐    │              │
│             │   │   输入栏         │    │              │
│             │   └──────────────────┘    │              │
└──────────────┴──────────────────────────┴──────────────┘
```

### 设计主题

Fairy-Tale Dream（西方梦幻童话）——粉白魔法美学：
- **Canvas 粒子系统**：55 颗背景闪粉 + 40 颗掠过粒子 + 15 颗爆发粒子
- **仙女精灵**：SVG 椭圆轨道环绕（framer-motion）
- **渐变主色调**：玫瑰粉 `#f8a4c8` 配米白 `#fefaf5` 背景
- **艺术字体**：Great Vibes（标题）、Noto Serif SC（中文）、Inter（UI）
- **无障碍**：尊重 `prefers-reduced-motion`，Tab 隐藏时暂停动画

详见 [DESIGN.md](DESIGN.md)。

---

## 测试

### 测试架构

Glimmer 为**确定性测试**而设计。每个核心机制——状态机、护栏、反馈分析器、重试策略——都是纯函数，无需真实 LLM 调用即可测试，通过 `MockLLMAdapter` 实现。

### 运行测试

```bash
# 全部测试（94+ 用例）
make test

# 单元测试（82 用例，零网络依赖）
make test-unit

# 集成测试（12 用例）
make test-integration

# 可执行演示脚本
python tests/demo/demo_guardrail.py
python tests/demo/demo_feedback_loop.py
python tests/demo/demo_sandbox.py
```

### 测试覆盖

| 模块 | 用例数 | 覆盖内容 |
|------|--------|---------|
| 状态机 | 12 | 全部转换、非法转换报错、ERROR 通配 |
| 路径沙箱 | 5 | 读写权限、路径穿越、符号链接攻击 |
| 正则黑名单 | 5 | `rm -rf /`、`DROP TABLE`、强制推送、curl 管道、安全命令 |
| 反馈分析器 | 6 | PASS/FAIL/UNKNOWN 判定、结构化失败提取、语法检查 |
| 重试策略 | 4 | 次数限制、卡死检测、不同失败不卡死 |
| Mock LLM | 4 | FIFO 响应、耗尽报错、调用历史、流式分块 |
| 工具注册表 | 4 | 注册分发、未知工具、重复注册 |
| 凭据管理器 | 10 | 掩码/状态/存储/删除周期、AES-GCM 加解密 |
| 配置管理器 | 9 | 深度合并、规范化、优先级、列表追加 |
| Agent 循环（集成） | 5 | 完整流程、工具使用、护栏拦截、批量调用、审批恢复 |
| WebSocket（集成） | 6 | 连接生命周期、多轮会话 |

### Mock 驱动的测试范式

```python
# 确定性测试：不需要真实 LLM
mock = MockLLMAdapter([
    LLMResponse(content="让我检查一下代码。", stop_reason="tool_use",
        tool_calls=[ToolCall(id="t1", name="read_file", arguments={"path": "src/main.py"})]),
    LLMResponse(content="代码看起来没问题。任务完成。", stop_reason="complete"),
])

loop = AgentLoop(tools, guardrails, analyzer, policy)
session = await loop.run("审查 src/main.py", mock)

assert session.state == State.COMPLETED
assert len(session.tool_calls) == 1
assert session.tool_calls[0].name == "read_file"
```

---

## 安全设计

### 凭据管理

| 存储方式 | 模式 | 加密 |
|---------|------|------|
| OS 钥匙串 | 桌面端（PyInstaller） | 平台原生（Windows Credential Manager / macOS Keychain / Linux Secret Service） |
| AES-256-GCM 文件 | Docker 端 | HKDF 从 `GLIMMER_SECRET_KEY` 派生密钥，每次加密使用随机 12 字节 nonce |

**API Key 绝不会出现在**：日志、终端输出、Git 历史、配置文件、API 响应（掩码为 `sk-...wxyz`）。

### 沙箱隔离

每个 Agent 会话在独立 Docker 容器中运行：
- `--network none`（无网络访问）
- `512MB` 内存限制
- `1` CPU 核心
- `100` 进程限制
- `--rm`（退出时自动清理）

### 防御层次

```
第一层（路径沙箱）       ← 最可靠 — 文件系统边界
第二层（命令白名单）      ← 中等 — 可执行文件名检查
第三层（正则黑名单）      ← 最弱 — 正则，可被绕过
         +
进程隔离（subprocess.run + shell=False + timeout）
```

### 已知局限

- 正则护栏（第三层）可被 base64 编码或间接执行绕过
- Docker 套接字访问是沙箱模式的必要条件——请确保 Docker 守护进程安全
- 高安全场景请补充 seccomp/AppArmor 系统级沙箱和命令 AST 解析

---

## 性能指标

| 指标 | 数值 | 备注 |
|------|------|------|
| WebSocket 连接建立 | < 500ms | 含 JWT 验证 |
| LLM 流式额外延迟 | < 100ms | 超出供应商延迟的部分 |
| 工具分发延迟 | < 50ms | 本地模式；Docker 增加 ~100ms |
| 前端渲染 | 60fps | 大消息列表使用原生滚动 |
| 粒子系统稳态 | 55 颗粒子 | Tab 隐藏时暂停，移动端减半 |

### 优化策略

- LLM 系统提示词 + 工具定义可缓存复用
- 数据库连接池（20 连接）
- Alembic 迁移支持不停机 Schema 演进
- Nginx 静态文件 gzip 压缩
- Vite 代码分割减少前端包体积
- Canvas `requestAnimationFrame` 循环 — `visibilitychange` 时暂停

---

## 项目结构

```
glimmer/
├── harness/                          # 核心智能体库
│   ├── auth/                         #   JWT 签发/验证、GitHub OAuth、AES-256-GCM 加密
│   ├── config/                       #   YAML 配置加载：默认→全局→项目（深度合并）
│   ├── credentials/                  #   API Key 存储：OS 钥匙串 + 加密文件回退
│   ├── db/                           #   PostgreSQL：异步会话、ORM 模型（User/Session/Message）
│   │   └── migrations/               #   Alembic 迁移
│   ├── feedback/                     #   确定性反馈：策略分发、pytest 解析器、重试策略
│   ├── guardrails/                   #   三层护栏：路径沙箱、命令白名单、正则黑名单
│   ├── llm/                          #   可插拔适配器：Anthropic、OpenAI、Mock（测试用）
│   ├── memory/                       #   JSON 文件决策与学习持久化
│   ├── sandbox/                      #   Docker 容器生命周期管理
│   ├── tools/                        #   Agent 工具：文件操作、Shell、代码搜索、测试运行
│   ├── loop.py                       #   AgentLoop — 状态机主协调器
│   ├── models.py                     #   Pydantic 模型：Session、Message、ToolCall、Feedback 等
│   └── state_machine.py              #   确定性状态转换表
├── server/                           # FastAPI 应用服务器
│   ├── api/                          #   REST 路由：认证、配置、会话、文件
│   ├── static/                       #   前端构建产物（Vite 输出）
│   ├── main.py                       #   FastAPI 应用工厂（CORS、限流、静态文件）
│   ├── ws_handler.py                 #   WebSocket 会话处理器（JWT 鉴权、Docker 生命周期）
│   └── session_registry.py           #   内存会话→容器映射表（TTL: 1h）
├── web/                              # React + TypeScript 前端
│   ├── src/
│   │   ├── components/               #   22 个 UI 组件
│   │   ├── contexts/                 #   AuthContext（JWT 状态管理）
│   │   ├── hooks/                    #   useWebSocket、useSession、useGitHubStars
│   │   ├── pages/                    #   6 个页面
│   │   ├── services/                 #   REST API 客户端
│   │   └── styles/                   #   CSS：设计令牌 + 各页面/组件样式
│   ├── package.json                  #   React、Framer Motion、Lucide、React Router
│   └── vite.config.ts                #   开发代理 + 构建输出
├── tests/                            # 测试套件（94+ 用例）
│   ├── conftest.py                   #   共享夹具
│   ├── demo/                         #   可执行演示脚本
│   ├── integration/                  #   集成测试
│   └── unit/                         #   隔离单元测试
├── .github/workflows/ci.yml          # GitHub Actions CI
├── DESIGN.md                         # 童话梦幻设计系统参考
├── SPEC.md                           # 完整技术规约
├── Dockerfile                        # 多阶段：Node（前端）→ Python（后端）
├── Dockerfile.sandbox                # Agent 沙箱：Python + pytest + ripgrep + git
├── docker-compose.yml                # 生产部署：nginx + api + postgres
├── nginx.conf                        # 反向代理（WebSocket 升级）
├── pyinstaller.spec                  # 独立二进制打包
├── requirements.txt                  # Python 依赖（17 个包）
├── Makefile                          # 构建、测试、部署命令
└── LICENSE                           # MIT
```

---

## 贡献指南

### 开发工作流

```bash
# 1. Fork 并克隆
git clone https://github.com/<你的用户名>/lite-agent-harness.git
cd lite-agent-harness

# 2. 安装依赖
pip install -r requirements.txt
cd web && npm install && cd ..

# 3. 创建特性分支
git checkout -b feature/my-feature

# 4. 修改前先跑测试
make test

# 5. 开发迭代
make dev              # 终端 1：后端
cd web && npm run dev # 终端 2：前端（Vite HMR）

# 6. 修改后跑测试
make test

# 7. 提交并推送
git commit -m "feat: 功能描述"
git push origin feature/my-feature
```

### 代码规范

- **Python**：必须包含类型标注。数据模型使用 Pydantic。全链路 async/await。
- **TypeScript**：严格模式。所有 Props 类型化 。使用 CSS 变量而非硬编码颜色。
- **测试**：新功能需要测试。使用 `MockLLMAdapter` 避免网络依赖。
- **提交**：Conventional Commits（`feat:`、`fix:`、`docs:`、`test:`、`refactor:`、`chore:`）。

### 添加工具

1. 实现 `harness.tools.registry.Tool` 抽象基类
2. 在 `_build_default_tool_registry()` 中注册
3. 如需要，添加护栏规则（路径 + 白名单 + 正则）
4. 如工具产生可验证的结果，添加反馈分析策略
5. 使用 `MockLLMAdapter` 编写测试
6. 更新本文档的[工具参考](#工具参考)

### 添加 LLM Provider

1. 实现 `harness.llm.adapter.LLMAdapter`
2. 在 `harness/llm/__init__.py` 中导出
3. 在 `_create_llm_from_config()` 中添加 Provider 检测逻辑
4. 更新前端 `SettingsPanel.tsx` Provider 下拉菜单
5. 更新本文档的 [LLM 供应商](#llm-供应商)

---

## 常见问题

### "API key not configured"

确认已在 Settings 面板中保存 API Key。本地模式下检查 `.harness/credentials/.key` 文件是否存在。部署模式下检查 `user_configs` 表中加密 Key。

### "Authentication required"（WebSocket 4001）

JWT 令牌过期或无效。退出后重新通过 GitHub OAuth 登录。本地模式不应出现此错误（无认证）。

### "Command not in whitelist"

Agent 尝试执行白名单外的命令。可选择：
- 在护栏弹窗中批准（单次有效）
- 在配置文件的 `command_whitelist_extra` 中永久添加该命令

### "No more mock responses"（测试错误）

使用 `MockLLMAdapter` 时，确保预编程的响应数量与实际 LLM 调用次数匹配。每次 `chat()` 调用消耗一个响应。

### "Database URL not configured"

部署模式下确保 `.env` 或环境中已设置 `DATABASE_URL`。本地模式下这是正常的——Glimmer 会自动检测并跳过数据库初始化。

### "Docker daemon not available"

确保 Docker 正在运行且套接字可访问。若使用非标准套接字路径，检查 `DOCKER_HOST` 环境变量。

### "Write outside sandbox"

Agent 尝试写入 `sandbox_root` 之外的文件。可选择：
- 调整 `sandbox_root` 以包含目标目录
- 通过 `PathSandbox.add_writable_dir()` 增加可写目录

### 调试

```bash
# 启用详细测试输出
pytest tests/ -v --tb=long

# 启用 uvicorn 调试日志
uvicorn server.main:app --host 127.0.0.1 --port 8000 --log-level debug

# 检查 WebSocket 消息（浏览器控制台）
# 开发模式下所有消息记录到控制台

# 检查 Docker 容器
docker ps -a --filter "name=agent-"
docker logs <container-id>
```

---

## 设计系统

Glimmer 使用 **Fairy-Tale Dream（西方梦幻童话）** 设计系统。完整参考见 [DESIGN.md](DESIGN.md)。

**速查**：

| 类别 | Token | 值 |
|------|-------|-----|
| 背景 | `--color-bg-primary` | `#fefaf5` |
| 主色调 | `--color-accent` | `#f8a4c8` |
| 标题字体 | `--font-display` | `'Great Vibes', cursive` |
| 正文字体 | `--font-body` | `'Inter', sans-serif` |
| 中文字体 | `--font-tagline` | `'Noto Serif SC', serif` |
| 光晕阴影 | `--shadow-glow` | `0 8px 30px rgba(248,164,200,0.2)` |

---

## 许可证

MIT License。详见 [LICENSE](LICENSE)。

Copyright © 2026 [Jingyu Wang](https://github.com/jingyu-wang)。

---

<p align="center">
  <sub>Built with ❤️ using Python, FastAPI, React, and a love for deterministic software.</sub>
</p>
