[English](README.md) | [中文](README.zh.md)

---

# Lite Agent Harness

一个轻量级、模型无关的编码智能体框架，具备确定性护栏和 mock 驱动测试能力。

本项目是 AI4SE 课程的期末项目，从零构建了一个完整的智能体循环：状态机驱动的执行引擎、多供应商 LLM 支持、三层护栏系统、确定性反馈分析与多轮自我修正，以及实时 Web 交互界面。

---

## 特性

- **状态机驱动的智能体循环** —— 纯函数状态转换（IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → COMPLETED），路由决策不依赖 LLM。
- **多供应商 LLM 支持** —— 可插拔适配器，支持 Anthropic（Messages API）和 OpenAI（Chat Completions API），以及用于零网络测试的 Mock 适配器。
- **三层护栏系统** —— 第一层：文件系统路径沙箱。第二层：命令白名单。第三层：基于正则的危险模式黑名单。每层可以放行、拦截或请求人工审批。
- **确定性反馈分析器** —— 基于 exit code 和结构化测试报告进行分析，而非提示词驱动。无论是否有 LLM，行为完全一致。通过重试策略实现多轮自我修正，并能检测死循环。
- **实时 Web 界面** —— React + TypeScript 前端，FastAPI + WebSocket 后端。支持流式输出、工具调用卡片、护栏审批弹窗、反馈横幅和设置面板。
- **Docker + PyInstaller 双分发** —— 可在容器中运行，也可作为独立可执行文件。
- **安全的凭据存储** —— 桌面端使用操作系统钥匙串，Docker 环境降级为 AES-GCM 加密文件。密钥绝不出现于日志、Git 历史或明文配置中。

---

## 快速开始

```bash
pip install -r requirements.txt
# .harness/config.yaml 已存在，编辑 provider/model 即可
make run
# 浏览器打开 http://localhost:8000
```

---

## 项目结构

```
lite-agent-harness/
├── docs/                          # 课程需求文档与设计规约
├── harness/                       # 核心库
│   ├── config/                    #   YAML 配置加载与合并
│   │   └── manager.py
│   ├── credentials/               #   安全 API 密钥存储
│   │   └── manager.py
│   ├── feedback/                  #   确定性反馈分析
│   │   ├── analyzer.py            #     按工具类型分发判定
│   │   ├── pytest_parser.py       #     Pytest JSON 报告解析器
│   │   └── retry_policy.py        #     重试限制与死循环检测
│   ├── guardrails/                #   三层安全系统
│   │   ├── engine.py              #     编排器
│   │   ├── path_sandbox.py        #     第一层：文件系统边界
│   │   ├── whitelist.py           #     第二层：命令白名单
│   │   └── patterns.py            #     第三层：正则黑名单
│   ├── llm/                       #   多供应商 LLM 抽象层
│   │   ├── adapter.py             #     所有供应商的抽象基类
│   │   ├── anthropic.py           #     Anthropic Messages API
│   │   ├── mock.py                #     预编程响应用于测试
│   │   └── openai.py              #     OpenAI Chat Completions API
│   ├── memory/                    #   决策与学习记录持久化
│   │   └── manager.py
│   ├── tools/                     #   智能体工具定义
│   │   ├── registry.py            #     注册与分发
│   │   ├── code_search.py         #     ripgrep / Python grep
│   │   ├── file_ops.py            #     read_file / write_file
│   │   └── shell.py               #     execute_shell / run_tests
│   ├── __init__.py
│   ├── loop.py                    #   主循环
│   ├── models.py                  #   共享 Pydantic 数据模型
│   └── state_machine.py           #   确定性状态转换表
├── server/                        # FastAPI Web 服务
│   ├── api/                       #   REST 路由
│   │   ├── config_routes.py       #     GET/PUT /api/config
│   │   ├── credential_routes.py   #     GET/POST/DELETE /api/credentials
│   │   └── session_routes.py      #     GET /api/session/history
│   ├── static/                    #   前端构建产物
│   ├── __init__.py
│   ├── main.py                    #   FastAPI 应用工厂
│   └── ws_handler.py              #   WebSocket 会话处理器
├── tests/                         # 测试套件
│   ├── demo/                      #   可运行的演示脚本
│   │   ├── demo_guardrail.py
│   │   ├── demo_feedback_loop.py
│   │   └── demo_sandbox.py
│   ├── integration/               #   集成测试（12 个）
│   │   ├── test_agent_loop.py
│   │   └── test_websocket.py
│   ├── unit/                      #   单元测试（82 个）
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
│   └── conftest.py                # 共享 fixtures
├── web/                           # React + TypeScript 前端
│   ├── src/
│   │   ├── components/            #   UI 组件
│   │   ├── hooks/                 #   React hooks（WebSocket, session）
│   │   ├── services/              #   API 客户端
│   │   └── ...
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .harness/
│   └── config.yaml                # 项目级配置
├── Dockerfile                     # Docker 多阶段构建
├── LICENSE                        # MIT
├── Makefile                       # 构建、测试、运行目标
├── pyinstaller.spec               # PyInstaller 单文件打包配置
├── pytest.ini                     # Pytest 配置
└── requirements.txt               # Python 依赖
```

---

## 安装

### 前置条件

- **Python 3.12+**（开发环境为 3.14）
- **Node.js 22+**（前端开发需要；预构建的静态文件已包含在仓库中）
- **ripgrep**（可选，推荐用于快速代码搜索；不可用时回退至 Python `re`）

### Python 依赖

```bash
pip install -r requirements.txt
```

主要包：`pydantic`、`pyyaml`、`anthropic`、`openai`、`fastapi`、`uvicorn`、`keyring`、`cryptography`、`pytest`、`httpx`。

### 前端构建（可选 —— 预构建文件已在 `server/static/` 中）

```bash
cd web
npm install
npm run build
# 输出到 server/static/
```

---

## 运行

| 命令 | 说明 |
|---|---|
| `make run` | 启动开发服务器（uvicorn 热重载，`localhost:8000`）|
| `make test` | 运行全部单元测试 + 集成测试 |
| `make test-unit` | 仅运行单元测试（82 个，零网络依赖）|
| `make test-integration` | 仅运行集成测试（12 个）|
| `make build-web` | 构建 React 前端 |
| `make build-docker` | 构建 Docker 镜像 |
| `make build-binary` | 通过 PyInstaller 构建独立可执行文件 |
| `make clean` | 清理构建产物 |

### 开发服务器

```bash
make run
# 或直接运行：
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
```

浏览器打开 `http://localhost:8000`。WebSocket 连接在你通过界面提交任务时自动建立。

### 独立可执行文件

```bash
make build-binary
# ./dist/lite-agent-harness（Windows 下为 lite-agent-harness.exe）
```

---

## 配置

配置由 `ConfigManager` 管理，合并三个层级（优先级从高到低）：

1. **项目级配置**：`.harness/config.yaml`
2. **全局配置**：`~/.harness/config.yaml`
3. **内置默认值**：`ConfigData()` 模型默认值

### `.harness/config.yaml` 配置项

```yaml
model:
  provider: anthropic        # "anthropic"、"openai"，或使用 Mock
  model_id: claude-sonnet-5  # 例如 "gpt-4o"、"claude-sonnet-5-20251001"
  max_tokens: 4096

guardrails:
  max_retries: 3             # 最大自我修正次数
  sandbox_root: .            # 限制文件访问范围
  command_whitelist_extra: [] # 额外允许的命令
  timeout_seconds: 30        # Shell 命令超时时间

tools:
  enabled: [read_file, write_file, execute_shell, run_tests, search_code]

memory:
  max_context_tokens: 8000
  learnings_limit: 20
```

REST API：`GET /api/config` 返回合并后的配置，`PUT /api/config` 更新项目级配置。

---

## 凭据管理

### 设置 API 密钥

**通过 Web 界面**：打开设置面板，为所选供应商（Anthropic 或 OpenAI）输入 API 密钥。

**通过环境变量**（适用于无头/Docker 环境）：若设置了环境变量，LLM 适配器会直接读取。

### 存储方式

- **桌面端（keyring 可用）**：密钥存储在操作系统钥匙串中（`keyring` 库）。
- **Docker / 无头环境（keyring 不可用）**：密钥以 AES-GCM 加密存储在 `.harness/credentials/{provider}.enc`。加密密钥通过 HKDF 从 `HARNESS_KEY_PASSWORD` 环境变量派生。

### 安全性

- 密钥**绝不**记录到日志、提交到 Git 或存储在明文配置文件中。
- `mask()` 方法返回安全的显示字符串：`sk-...ab12`。
- 凭据 REST API 从不返回完整密钥。
- 威胁模型：本地单用户工具。操作系统钥匙串保护防止随意窃取；AES-GCM 回退防止 Docker 卷中的明文暴露。

---

## 分发

### Docker

```bash
make build-docker
# 或手动：
docker build -t lite-agent-harness .
docker run -p 8000:8000 -e HARNESS_KEY_PASSWORD=<你的密码> lite-agent-harness
```

多阶段构建：Node 22-alpine 构建前端，Python 3.12-slim 运行服务端。监听 `0.0.0.0:8000`。

### PyInstaller 二进制

```bash
make build-binary
# 输出：dist/lite-agent-harness（Windows 下为 .exe）
```

**已知限制：**
- Windows SmartScreen 可能对未签名二进制文件发出警告。
- 推荐安装 ripgrep 以提升 `search_code` 速度；不可用时回退至 Python 正则。
- 二进制文件封装了嵌入的数据目录。

---

## 测试

### 测试套件

| 套件 | 数量 | 范围 |
|---|---|---|
| 单元测试 | 82 | 所有组件隔离测试，零网络依赖，Mock LLM |
| 集成测试 | 12 | 完整智能体循环、WebSocket、REST API（TestClient）|
| **合计** | **94** | |

```bash
# 完整套件
make test

# 分别运行
make test-unit
make test-integration

# 指定测试文件
python -m pytest tests/unit/test_state_machine.py -v
```

### 可运行的演示脚本

```bash
python tests/demo/demo_guardrail.py       # 护栏拦截 rm -rf /
python tests/demo/demo_sandbox.py         # 路径沙箱 + 命令白名单
python tests/demo/demo_feedback_loop.py   # 注入失败 → 检测 → 修正 → 完成
```

### 测试哲学

- **单元测试零网络依赖**：所有测试使用 `MockLLMAdapter` 和预编程响应。
- **确定性状态机**：`transition()` 是纯函数，不依赖 LLM 即可测试。
- **反馈分析器是代码而非提示词**：判定来自 exit code 和结构化 JSON，永不依赖 LLM 判断。
- **护栏隔离测试**：每一层（路径、白名单、模式）有独立的测试文件。

---

## 智能体架构

### 状态机

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
RETRY / MAX_RETRIES --> PLANNING 或 COMPLETED
```

所有状态转换由 `harness/state_machine.py` 中的纯函数 `transition(state, event) → state` 计算，不涉及任何 LLM 调用——这保证了测试时的确定性行为。

### 三层护栏

| 层 | 组件 | 动作 | 范围 |
|---|---|---|---|
| 1 | `PathSandbox` | 拦截 | 沙箱根目录外的文件读写 |
| 2 | `CommandWhitelist` | 请求审批 | 不在白名单中的 shell 命令 |
| 3 | `PatternBlacklist` | 拦截或请求审批 | 危险模式（`rm -rf /`、`DROP TABLE`、强制推送、curl 管道执行等）|

### 反馈与自我修正

`FeedbackAnalyzer` 对工具执行结果进行确定性分析：

- `run_tests`：解析 `pytest-json-report` 输出，提取结构化的失败详情。生成包含每个失败测试的文件、行号和错误信息的修正建议。
- `execute_shell`：基于 exit code 判定。
- `write_file`：基于 exit code 判定。
- `read_file` / `search_code`：返回 `UNKNOWN`（无客观的通过/失败信号）。

`RetryPolicy` 限制重试次数（`max_retries`，默认 3），并通过比较最近 3 次失败签名检测死循环——若完全一致则提前终止。

---

## 安全边界

- **单用户本地工具**：仅监听 `localhost:8000`。不适用于多用户或公网暴露场景。
- **无身份认证**：WebSocket 和 REST API 无认证层。访问受网络绑定限制。
- **护栏是纵深防御**：为代码生成任务提供合理的安全保障，但不是安全保证。基于正则的模式匹配可被编码或间接调用绕过。
- **凭据威胁模型**：桌面端密钥存储在操作系统钥匙串中，Docker 中为 AES-GCM 加密磁盘存储。加密密码（`HARNESS_KEY_PASSWORD`）需通过环境变量提供。密钥绝不记录到日志或暴露于 Git。

---

## 许可证

MIT License。详见 [LICENSE](LICENSE)。

Copyright (c) 2026 Jingyu Wang
