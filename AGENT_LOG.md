# AGENT_LOG.md：智能体实现过程日志

> 记录使用 Superpowers subagent-driven-development 技能实现 lite-agent-harness 的完整过程。

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

**产出**：`docs/superpowers/specs/2026-07-15-lite-agent-harness-design.md`（503 行）、`docs/superpowers/plans/2026-07-15-lite-agent-harness.md`（2754 行）

---

### 2026-07-15：实现阶段（subagent-driven-development）

**触发的技能**：`superpowers:subagent-driven-development`

#### Task 1: 项目脚手架
- **子智能体**：haiku
- **提交**：`5df9f94`
- **内容**：requirements.txt, Makefile, .harness/config.yaml, .gitignore
- **审查结果**：✅ 规范合规，无问题
- **耗时**：~3 分钟

#### Task 2: 核心数据模型
- **子智能体**：haiku
- **提交**：`e0775a5`
- **内容**：14 个 Pydantic 模型 + 3 个枚举 + conftest fixtures
- **审查结果**：✅ 规范合规，轻微问题（未使用的 `Any` 导入）
- **耗时**：~2 分钟

#### Task 3: LLM 抽象层 — 接口 + Mock
- **子智能体**：haiku
- **提交**：`32f93fb`
- **内容**：LLMAdapter ABC, MockLLMAdapter, 4 个异步测试
- **偏差**：需添加 pytest.ini（asyncio_mode=auto）和 tests/unit/__init__.py
- **审查结果**：✅ 规范合规，偏差合理
- **耗时**：~3 分钟

#### Task 4: Anthropic + OpenAI 适配器
- **子智能体**：haiku
- **提交**：`1159a90`
- **内容**：AnthropicAdapter, OpenAIAdapter
- **审查结果**：✅ 通过，轻微问题（`import json` 在循环内）
- **耗时**：~1 分钟

#### Task 5: 工具注册表 + 内置工具
- **子智能体**：haiku
- **提交**：`eebfb68`，修复：`cbeded7`
- **内容**：Tool ABC, ToolRegistry, 5 个内置工具
- **审查发现**：shell=False 与字符串命令不兼容 POSIX（已修复：shlex.split），缺少 pytest-json-report 依赖（已修复）
- **人工干预**：要求修复以上两个问题
- **耗时**：~5 分钟（含修复）

#### Task 6: 三层护栏
- **子智能体**：haiku
- **提交**：`a6fdac6`，修复：`7ffa2f3`
- **内容**：PathSandbox, CommandWhitelist, PatternBlacklist, GuardrailEngine
- **审查发现**：未知 mode 静默放行（已修复），run_tests 绕过第 2/3 层检查（已修复）
- **人工干预**：要求修复以上两个 bug
- **耗时**：~5 分钟（含修复）

#### Task 7: 反馈分析器
- **子智能体**：haiku
- **提交**：`65b49af`
- **内容**：FeedbackAnalyzer, pytest_parser, RetryPolicy
- **审查结果**：✅ 规范合规，无问题
- **耗时**：~2 分钟

#### Task 8: 状态机引擎
- **子智能体**：haiku
- **提交**：`8a1680f`
- **内容**：EventType 枚举, 转换表, transition() 纯函数
- **审查结果**：✅ 规范合规，12/12 测试通过
- **耗时**：~1 分钟

#### Task 9: Agent 主循环（**最复杂任务**）
- **子智能体**：sonnet（提高模型等级）
- **提交**：`9fff1b4`，修复：后续提交
- **内容**：AgentLoop.run(), 集成测试
- **审查发现（严重）**：批量工具调用丢失、AWAITING_HUMAN 死胡同
- **人工干预**：要求修复两个严重 bug，重构为 _run_loop() + resume()
- **耗时**：~10 分钟（含修复）

#### Task 10: 记忆/配置/凭据管理器
- **子智能体**：haiku
- **提交**：`250fcf9`
- **内容**：MemoryManager, ConfigManager, CredentialManager，42 个测试
- **审查结果**：✅ 通过，轻微文档/设计问题
- **耗时**：~7 分钟

#### Task 11: FastAPI 服务器 + WebSocket
- **子智能体**：sonnet
- **提交**：后续提交
- **内容**：server/main.py, ws_handler.py, REST 路由，7 个 WebSocket 集成测试
- **关键设计**：事件发射系统，WebSocket 生命周期管理
- **耗时**：~17 分钟

#### Task 12: React 前端
- **子智能体**：sonnet
- **提交**：后续提交
- **内容**：22 个源文件，10 个组件，暗色主题，WebSocket hooks
- **耗时**：~7 分钟

#### Task 14: 演示脚本
- **子智能体**：haiku
- **提交**：`88a5ac1`
- **内容**：demo_guardrail.py, demo_sandbox.py, demo_feedback_loop.py
- **耗时**：~2 分钟

#### Task 15: Docker + PyInstaller
- **子智能体**：haiku
- **提交**：`37c3e16`
- **内容**：Dockerfile（多阶段），pyinstaller.spec
- **耗时**：~1 分钟

#### Task 16: README + 文档
- **子智能体**：haiku
- **提交**：`6b93e81`，后续：`839a7ef`（中文版）
- **内容**：完整 README.md + README.zh.md（双语切换）
- **耗时**：~5 分钟

#### Task 17: Open Design 集成（后期补充）
- **子智能体**：sonnet
- **提交**：`28394b5`
- **内容**：将前端从纯手写 CSS 升级为 Open Design 的 Linear 设计系统。重写 `index.css` 为结构化的 design token 体系（颜色/间距/字体/圆角/阴影/过渡），所有组件改用 CSS 变量引用，新增 `DESIGN.md` 记录完整 token 参考
- **触发原因**：项目要求文档明确规定"凡涉及前端 / UI，强烈推荐使用 Open Design 进行界面开发，并在 SPEC 中说明所选设计系统与 skill"
- **耗时**：~4 分钟

#### 最终审查与修复
- **子智能体**：sonnet
- **提交**：`f8d8bb5`
- **修复内容**：7 个严重/重要问题（LLM 超时、compile 检查、批量绕过、重试升级消息、共享状态、白名单无界追加、run_tests 路径沙箱）
- **审查结果**：全分支审查通过，94/94 测试

---

## 学到的教训

1. **批量工具调用处理**：最初的实现只处理第一个工具调用，然后重新调用 LLM 覆盖了等待列表。这是一个原型中容易遗漏但真实 LLM 在单次响应中返回多个工具调用时会导致静默数据丢失的 bug。

2. **审查循环的价值**：每个任务的审查者都发现了实现者遗漏的问题——通常是实现者"忠实遵循规范"导致规范本身设计缺陷的问题（如 `shlex.split` 问题、`run_tests` 绕过护栏）。

3. **模型选择很重要**：haiku 在机械的"复制规范代码"任务上表现出色（1-2 分钟）。sonnet 在复杂的需要判断的集成任务上是必需的——主循环花了 10 分钟并需要大量重构。

4. **事件发射与状态机**：向 loop.py 添加事件系统最初被认为是一个实现细节，但成为了连接 WebSocket 处理程序的关键接口。应在规范中明确设计。

5. **双语 README**：用户要求在最后添加中英文 README 切换功能。这是一项小改动，但显著改善了可访问性。在这些细节被明确提出之前就预见到会更好。

---

*本文档随实现推进同步更新。*
