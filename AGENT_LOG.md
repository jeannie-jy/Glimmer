# AGENT_LOG.md：智能体实现过程日志

> 记录使用 Superpowers subagent-driven-development 技能实现 Glimmer 的完整过程。

## 环境

| 项目 | 值 |
|------|-----|
| 主智能体 | Claude Code (DeepSeek V4 Pro) |
| 子智能体模型 | haiku（机械任务）/ sonnet（集成任务）|
| Superpowers 版本 | main 分支 |
| 开发分支 | feature/implement-harness |
| 基分支 | main |

---

## 时间线

### 2026-07-15：设计阶段（brainstorming + writing-plans）

**触发的技能**：`superpowers:brainstorming` → `superpowers:writing-plans`

**关键决策**：
- 语言：纯 Python（放弃了 Python+Java 混用方案）
- 架构：状态机驱动
- 重点维度：反馈闭环 + 治理护栏（双重点）
- 前端：React + FastAPI WebSocket
- 分发：Docker + PyInstaller

**产出**：`docs/superpowers/specs/2026-07-15-lite-agent-harness-design.md`、`docs/superpowers/plans/2026-07-15-lite-agent-harness.md`

---

### 2026-07-15：核心实现阶段

**触发的技能**：`superpowers:subagent-driven-development`

Tasks 1-16 实现了完整 harness 内核、FastAPI 服务端、React 前端、演示脚本和文档。

---

### 2026-07-16：童话主题前端改版

**触发的技能**：`superpowers:brainstorming` → `superpowers:writing-plans` → `superpowers:subagent-driven-development`

**关键决策**：
- 从暗色 Linear 主题彻底转换为童话梦幻风格
- 粉白配色（`#fefaf5` 背景，`#f8a4c8` 主色调），零紫色零金色
- Great Vibes 手写体标题 + Noto Serif SC 中文艺术字
- Canvas 2D 重写粒子系统：仅细碎圆点（≤1.5px），闪粉掠过标题，仙女挥棒爆发
- Framer Motion 仙女椭圆轨道动画 + 魔法棒闪烁
- 项目从 "Lite Agent Harness" 更名为 **Glimmer**
- DemoChat 组件：主页动态代码生成演示窗
- Lucide React SVG 图标替代所有 emoji
- Settings 面板简化：Provider + Base URL + Model + API Key 四合一

**产出**：`docs/superpowers/specs/2026-07-16-fairy-tale-theme-redesign.md`、`docs/superpowers/plans/2026-07-16-fairy-tale-theme-redesign.md`

**7 次提交**，39 个文件变更。

---

### 2026-07-16：多用户部署架构

**触发的技能**：`superpowers:brainstorming` → `superpowers:writing-plans` → `superpowers:subagent-driven-development`

**关键决策**：
- GitHub OAuth 登录（无密码管理）
- JWT 鉴权（所有 API/WebSocket 路由保护）
- PostgreSQL 持久化（用户、配置、会话、消息）
- Docker 容器沙箱（每会话独立容器，无网络，512MB 内存限制）
- AES-256-GCM 加密存储 API Key
- 前端相对 URL + AuthContext + LoginPage + ProtectedRoute
- Nginx 反代 + slowapi 限流 + docker-compose 一键部署
- 保留本地单用户模式（无 DATABASE_URL 时自动降级）

**产出**：`docs/superpowers/specs/2026-07-16-multi-user-deployment-design.md`、`docs/superpowers/plans/2026-07-16-multi-user-deployment.md`

**8 次提交**，16 个新文件，12 个文件修改。

---

## 当前状态

| 指标 | 值 |
|------|-----|
| 总提交数 | 30+ |
| Python 测试 | 94+ |
| 前端页面 | 6（Home / About / Guide / Learn / Agent / Login） |
| 支持 LLM | Anthropic + 任意 OpenAI 兼容（DeepSeek / Qwen / Ollama / vLLM） |
| 部署方式 | 本地单用户 / docker-compose 多用户 |
| 设计语言 | Fairy-Tale Dream（粉白童话） |
| 项目名称 | Glimmer |

---

## 学到的教训

1. **审查循环的价值**：每个任务的审查者都发现了实现者遗漏的问题——通常是规范本身的设计缺陷。

2. **模型选择很重要**：haiku 在机械任务上表现出色，sonnet 在复杂集成任务上是必需的。

3. **文件存储可靠性**：Windows keyring 的行为不可预测——始终以文件为主要存储，keyring 作为辅助。

4. **前端 URL 硬编码**：localhost 硬编码在部署到生产环境时会直接崩溃。从第一天就应使用相对 URL。

5. **凭证管理的人机工程学**：对于本地工具，文件存储比加密方案更用户友好。

---

*本文档随实现推进同步更新。*
