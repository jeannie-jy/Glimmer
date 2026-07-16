# Glimmer

轻量级、模型无关的 AI 编程智能体，具备确定性护栏、Docker 沙箱隔离和童话主题 Web 界面。

> "每一次编码，都是一场施法"

---

## 特性

- **状态机驱动的智能体循环** — 纯函数状态转换（IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → COMPLETED），路由决策不依赖 LLM。
- **多供应商 LLM** — Anthropic（Messages API）+ OpenAI 兼容（DeepSeek、Qwen、Ollama、vLLM 等）。支持自定义 Base URL 和 Model。
- **多用户支持** — GitHub OAuth 登录、JWT 鉴权、每用户独立配置、AES-256-GCM 加密存储 API Key、PostgreSQL 持久化。
- **Docker 沙箱** — 每个 Agent 会话在独立容器中运行（无网络、512MB 内存限制），安全执行代码。
- **三层护栏** — 路径沙箱 + 命令白名单 + 正则黑名单，每层可放行/拦截/请求审批。
- **确定性反馈分析** — 基于 exit code 和结构化报告，不依赖 LLM 判断。多轮自修正 + 死循环检测。
- **童话主题前端** — React + TypeScript，粉白梦幻配色，Great Vibes 手写标题，framer-motion 动效，Canvas 闪粉粒子，仙女环绕动画，动态演示聊天窗。
- **实时流式输出** — WebSocket 驱动的流式 Token 显示、工具调用卡片、护栏弹窗、反馈横幅。
- **Docker + docker-compose 部署** — 生产就绪，Nginx 反代、支持 HTTPS、slowapi 限流。

---

## 快速开始

### 本地单用户模式

```bash
pip install -r requirements.txt
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
# 浏览器打开 http://localhost:8000
```

### 多用户模式（需要 PostgreSQL + Docker）

```bash
export GITHUB_CLIENT_ID=你的GitHub_OAuth_Client_ID
export GITHUB_CLIENT_SECRET=你的GitHub_OAuth_Client_Secret
export GLIMMER_SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=你的数据库密码
docker-compose up -d
```

---

## 项目结构

```
glimmer/
├── harness/                       # 核心库
│   ├── auth/                      #   鉴权（JWT + OAuth + 加密）
│   ├── config/                    #   配置管理（本地模式）
│   ├── credentials/               #   凭据存储（本地模式）
│   ├── db/                        #   PostgreSQL 数据模型
│   ├── feedback/                  #   确定性反馈分析
│   ├── guardrails/                #   三层护栏
│   ├── llm/                       #   多供应商 LLM 适配器
│   ├── memory/                    #   学习记录
│   ├── sandbox/                   #   Docker 容器管理
│   ├── tools/                     #   Agent 工具
│   ├── loop.py                    #   主循环
│   ├── models.py                  #   数据模型
│   └── state_machine.py           #   状态机
├── server/                        # FastAPI 服务端
│   ├── api/                       #   REST 路由
│   │   ├── auth_routes.py         #     GitHub OAuth
│   │   ├── config_routes.py       #     每用户配置
│   │   └── session_routes.py      #     会话历史
│   ├── static/                    #   前端构建产物
│   └── ws_handler.py              #   WebSocket 处理
├── web/                           # React 前端
│   └── src/
│       ├── components/            #   组件
│       ├── contexts/              #   AuthContext
│       ├── hooks/                 #   useWebSocket 等
│       ├── pages/                 #   页面（Home/About/Guide/Learn/Agent/Login）
│       ├── services/              #   API 客户端
│       └── styles/                #   CSS 样式
├── tests/                         # 测试（94+ 用例）
├── DESIGN.md                      # 童话主题设计系统
├── Dockerfile                     # 多阶段构建
├── Dockerfile.sandbox             # Agent 沙箱镜像
├── docker-compose.yml             # 生产部署配置
├── nginx.conf                     # 反向代理配置
└── requirements.txt               # Python 依赖
```

---

## 配置

### Web 界面 Settings

| 字段 | 说明 |
|------|------|
| **Provider** | Anthropic 或 OpenAI Compatible |
| **Base URL** | OpenAI 兼容端点（如 `https://api.deepseek.com`） |
| **Model Name** | 模型名（如 `claude-sonnet-5`、`deepseek-chat`） |
| **API Key** | 你的 API 密钥（加密存储） |

### 多用户部署环境变量

| 变量 | 必须 | 说明 |
|------|------|------|
| `GLIMMER_SECRET_KEY` | 是 | JWT 签名 + 凭据加密的主密钥 |
| `GITHUB_CLIENT_ID` | 是 | GitHub OAuth 客户端 ID |
| `GITHUB_CLIENT_SECRET` | 是 | GitHub OAuth 客户端密钥 |
| `DATABASE_URL` | 是 | PostgreSQL 连接字符串 |
| `OAUTH_REDIRECT_URI` | 否 | OAuth 回调地址 |
| `DOCKER_HOST` | 否 | Docker 守护进程地址 |

---

## 支持的模型

| 供应商 | Base URL | 示例模型 |
|--------|----------|----------|
| Anthropic | （内置） | `claude-sonnet-5` |
| OpenAI | （内置） | `gpt-4o` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| Qwen（通义千问）| `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Ollama | `http://localhost:11434/v1` | `llama3` |
| 任意 OpenAI 兼容 | 自定义 | — |

---

## 测试

```bash
make test              # 全部测试
make test-unit         # 单元测试（82 用例）
make test-integration  # 集成测试（12 用例）
```

---

## 设计系统

详见 [DESIGN.md](DESIGN.md)：
- 粉白配色（`#fefaf5` 背景，`#f8a4c8` 主色调）
- Great Vibes + Noto Serif SC + Inter 字体
- Canvas 闪粉粒子 + framer-motion 动效
- 仙女环绕标题 + 魔法棒挥动闪光

---

## 许可证

MIT License · Copyright (c) 2026 Jingyu Wang
