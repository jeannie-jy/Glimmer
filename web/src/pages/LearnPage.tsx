import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import '../styles/learn.css';
import {
  GraduationCap, Brain, Shield, BarChart3, Zap, Layers,
  Workflow, Cpu, Terminal, FileCode, Code2, GitBranch,
  TestTube, BookOpen, Play, ExternalLink, Library,
  ChevronDown, Puzzle, Wrench, Database, Globe
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

interface Topic {
  id: string;
  icon: React.ReactNode;
  title: string;
  summary: string;
  details: string[];
  codeExample?: string;
}

const CORE_TOPICS: Topic[] = [
  {
    id: 'state-machine',
    icon: <Cpu size={22} />,
    title: '确定性状态机',
    summary: 'Agent 控制流的纯函数引擎——8 个状态，24 条转换规则，零 LLM 参与路由决策',
    details: [
      '8 个状态：IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → AWAITING_HUMAN → COMPLETED → ERROR',
      '核心转换：IDLE + TASK_SUBMIT → PLANNING → (LLM_FINISH → COMPLETED) / (LLM_TOOL_USE → EXECUTING)',
      '每条转换规则都是 (State, EventType) → State 的纯函数，无副作用，完全可测',
      'ERROR 事件从任何状态都可触发——全局异常捕获',
      'BATCH_CONTINUE 事件支持批量工具调用的流水线处理',
      '在 test_state_machine.py 中有 12 个确定性单元测试',
    ],
    codeExample: `# harness/state_machine.py — 状态转换表
TRANSITIONS: dict[tuple[State, EventType], State] = {
    (State.IDLE, EventType.TASK_SUBMIT): State.PLANNING,
    (State.PLANNING, EventType.LLM_FINISH): State.COMPLETED,
    (State.PLANNING, EventType.LLM_TOOL_USE): State.EXECUTING,
    (State.EXECUTING, EventType.GUARD_ALLOW): State.OBSERVING,
    (State.OBSERVING, EventType.FEEDBACK_FAIL): State.CORRECTING,
    (State.CORRECTING, EventType.MAX_RETRIES): State.COMPLETED,
    # ... 共 24 条规则
}

def transition(current: State, event: EventType) -> State:
    """纯函数——无 LLM，无 I/O，无副作用"""
    if event == EventType.ERROR:
        return State.ERROR
    key = (current, event)
    if key not in TRANSITIONS:
        raise ValueError(f"No transition for ({current}, {event})")
    return TRANSITIONS[key]`,
  },
  {
    id: 'guardrails',
    icon: <Shield size={22} />,
    title: '三层护栏系统',
    summary: '纵深防御——路径沙箱 + 命令白名单 + 正则黑名单，每层独立可测，组合提供全面防护',
    details: [
      'Layer 1 — PathSandbox：resolve() 路径规范化 + 前缀匹配，防止 ../ 穿越攻击',
      'Layer 2 — CommandWhitelist：20+ 默认安全命令 + 可扩展列表，未知命令 → ASK_HUMAN',
      'Layer 3 — PatternBlacklist：11 条正则规则，匹配危险参数模式（rm -rf /、DROP TABLE 等）',
      '每层可返回 ALLOW / BLOCK / ASK_HUMAN 三种动作——HITL（Human-in-the-Loop）审批流',
      'BLOCK 动作：直接拒绝，附带原因，前端弹 GuardrailModal 展示详细信息',
      '已知局限：正则可被编码/混淆绕过。文档明确记录，建议生产环境补充 seccomp/AppArmor',
    ],
    codeExample: `# 三层串行检查引擎
class GuardrailEngine:
    def check(self, tool_call: ToolCall) -> GuardResult:
        # Layer 1: 路径沙箱（文件操作）
        if tool_call.name in ("read_file", "write_file"):
            result = self._path_sandbox.validate(
                tool_call.arguments.get("path", ""), mode
            )
            if result.action != GuardAction.ALLOW:
                return result

        # Layer 2 & 3: 命令安全检查（shell 操作）
        if tool_call.name == "execute_shell":
            command = tool_call.arguments.get("command", "")
            result = self._whitelist.check(command)    # Layer 2
            if result.action != GuardAction.ALLOW: return result
            result = self._patterns.check(command)      # Layer 3
            if result.action != GuardAction.ALLOW: return result

        return GuardResult(action=ALLOW, layer=0)`,
  },
  {
    id: 'feedback',
    icon: <BarChart3 size={22} />,
    title: '确定性反馈闭环',
    summary: '不靠 LLM 判断——exit code + 结构化报告 + 语法检查 = 零幻觉、零延迟、完全可测',
    details: [
      'run_tests → 解析 pytest JSON 报告（--json-report），提取 file/line/function/message',
      'execute_shell → exit_code == 0 → PASS，否则 FAIL 附带 stderr',
      'write_file → 文件存在性验证 + .py 文件 compile() 语法检查',
      'read_file / search_code → 无客观判定 → UNKNOWN，交 LLM 自行判断',
      'RetryPolicy 支持：max_retries 限制（默认 3）+ 卡死检测（连续 3 次相同失败）',
      '逐级升级提示：第 1 次 "请修复" → 第 2 次 "请更加谨慎" → 第 3 次 "最后尝试"',
    ],
    codeExample: `class FeedbackAnalyzer:
    """确定性解析器——不是提示词。去掉 LLM 后仍可独立测试。"""

    def analyze(self, result: ToolResult) -> Feedback:
        # 策略分发——按工具类型路由
        if result.tool_name == "run_tests":
            return self._analyze_test_results(result)
        elif result.tool_name == "execute_shell":
            return self._analyze_shell(result)
        elif result.tool_name == "write_file":
            return self._analyze_write(result)  # 含 compile() 语法检查
        else:
            return Feedback(verdict=UNKNOWN)   # read_file / search_code`,
  },
  {
    id: 'llm-adapters',
    icon: <Brain size={22} />,
    title: '多模型适配器架构',
    summary: 'ABC 抽象基类 + 可插拔实现。Anthropic / OpenAI / DeepSeek / Qwen / Ollama / vLLM / Mock',
    details: [
      'LLMAdapter ABC：chat() + chat_stream() 两个抽象方法，统一返回 LLMResponse',
      'AnthropicAdapter：原生 Messages API，tool-use 透传，系统提示单独处理',
      'OpenAIAdapter：Chat Completions API，支持自定义 base_url（DeepSeek/Qwen/Ollama/vLLM）',
      'MockLLMAdapter：预编程响应序列，FIFO 消费。记录 call_history 供测试断言。',
      '切换 Provider 只需改 model_provider 配置——核心代码零修改',
      '适配器模式使得添加新 Provider 只需实现两个方法，不修改 harness 核心代码',
    ],
    codeExample: `# 适配器接口——统一抽象
class LLMAdapter(ABC):
    @abstractmethod
    async def chat(
        self, messages: list[Message],
        tools: list[ToolDef], stream: bool = True
    ) -> LLMResponse: ...

    @abstractmethod
    async def chat_stream(
        self, messages: list[Message],
        tools: list[ToolDef]
    ) -> AsyncIterator[str]: ...

# 创建适配器——一行切换
if provider == "anthropic":
    llm = AnthropicAdapter(api_key, model)
elif provider == "openai":
    llm = OpenAIAdapter(api_key, model, base_url)
else:
    llm = MockLLMAdapter([])  # 测试模式`,
  },
  {
    id: 'tools',
    icon: <Wrench size={22} />,
    title: '工具系统与扩展',
    summary: '5 内置工具 + Tool ABC 接口。本地/Docker 双执行路径，自动切换。',
    details: [
      'read_file：文件读取，支持 offset/limit 分页。Docker 模式通过 cat 执行',
      'write_file：文件创建/覆写，Docker 模式用 base64 编码安全写入。自动 mkdir -p',
      'execute_shell：命令执行，shell=False 防注入，30s 超时。Docker 模式隔离执行',
      'run_tests：pytest 运行 + --json-report 结构化输出。60s 超时',
      'search_code：ripgrep 搜索（优先）→ Python re 模块回退。支持 glob 过滤',
      '扩展：实现 Tool ABC → register() 注册即可，无需改动核心代码',
    ],
    codeExample: `# 自定义工具示例
class MyTool(Tool):
    @property
    def name(self) -> str: return "my_tool"

    @property
    def description(self) -> str:
        return "执行自定义操作"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }

    async def execute(self, args: dict) -> ToolResult:
        result = do_something(args["input"])
        return ToolResult(
            tool_name="my_tool", exit_code=0,
            stdout=result
        )`,
  },
  {
    id: 'testing',
    icon: <TestTube size={22} />,
    title: 'Mock 驱动测试范式',
    summary: '"移除 LLM 后仍可验证"——MockLLMAdapter + 确定性机制 = 零网络全链路测试',
    details: [
      'MockLLMAdapter：预编程 LLMResponse 序列，FIFO 消费。通过 call_history 验证 LLM 被调用参数',
      '状态机测试：枚举所有 (state, event) 对，断言 next_state 正确性',
      '护栏测试：构造危险命令（rm -rf /、DROP TABLE 等），断言 BLOCK/ASK_HUMAN/ALLOW',
      '反馈测试：构造 ToolResult（不同 exit_code + 结构化数据），断言 PASS/FAIL/UNKNOWN',
      '集成测试：AgentLoop.run() + MockLLM → 完整流程验证（规划→执行→观察→完成）',
      '94+ 测试用例：82 单元 + 12 集成 + 3 可执行 Demo 脚本',
    ],
    codeExample: `# 确定性集成测试——零网络依赖
mock = MockLLMAdapter([
    LLMResponse(content="让我检查代码", stop_reason="tool_use",
        tool_calls=[ToolCall(id="t1", name="read_file",
            arguments={"path": "src/main.py"})]),
    LLMResponse(content="任务完成", stop_reason="complete"),
])

loop = AgentLoop(tools, guardrails, analyzer, policy)
session = await loop.run("审查 src/main.py", mock)

assert session.state == State.COMPLETED
assert len(session.tool_calls) == 1
assert session.tool_calls[0].name == "read_file"`,
  },
];

const EXTENDING_TOPICS: Topic[] = [
  {
    id: 'custom-tool',
    icon: <Puzzle size={22} />,
    title: '添加自定义工具',
    summary: '三步添加新工具：实现 Tool ABC → 注册到 ToolRegistry → 添加护栏和反馈策略',
    details: [
      '1. 创建类继承 harness.tools.registry.Tool，实现 name/description/parameters/execute',
      '2. 在 server/ws_handler.py 的 _build_default_tool_registry() 中 register()',
      '3. 如需文件操作，在 GuardrailEngine.check() 中添加 Layer 1 路径检查',
      '4. 如需执行 shell 命令，确保命令在白名单中或扩展 command_whitelist_extra',
      '5. 如需反馈分析，在 FeedbackAnalyzer.analyze() 中添加工具分发分支',
      '6. 编写测试——使用 MockLLMAdapter + AgentLoop 验证工具被正确调用',
    ],
  },
  {
    id: 'custom-provider',
    icon: <Globe size={22} />,
    title: '添加 LLM Provider',
    summary: '实现 LLMAdapter ABC：chat() + chat_stream() → 注册 → 前端下拉菜单',
    details: [
      '1. 创建类继承 harness.llm.adapter.LLMAdapter，实现 chat() 和 chat_stream()',
      '2. chat() 返回统一 LLMResponse（content + tool_calls + stop_reason + usage）',
      '3. 在 harness/llm/__init__.py 中导出新适配器',
      '4. 在 server/ws_handler.py 的 _create_llm_from_config() 中添加 provider 判断',
      '5. 更新前端 SettingsPanel.tsx 的 Provider 下拉菜单选项',
      '6. 编写 Mock 测试——确保适配器正确转换消息和工具格式',
    ],
  },
  {
    id: 'custom-guardrail',
    icon: <Shield size={22} />,
    title: '扩展护栏规则',
    summary: '添加自定义危险模式、扩展白名单、添加可写目录——全部通过配置或代码扩展',
    details: [
      '添加正则黑名单：PatternBlacklist(extra_patterns=[(r"pattern", BLOCK, "reason")])',
      '扩展白名单：config.yaml 中 command_whitelist_extra: [poetry, yarn, ...]',
      '添加可写目录：PathSandbox.add_writable_dir(Path("/extra/path"))',
      '自定义护栏层：在 GuardrailEngine.check() 中插入自定义检查逻辑',
    ],
  },
  {
    id: 'memory-system',
    icon: <Database size={22} />,
    title: '记忆与学习系统',
    summary: '三层记忆模型——项目约定 + 决策记录 + 学习记录。JSON 文件存储，关键词检索。',
    details: [
      'Layer 1 — 项目约定：启动时加载 CLAUDE.md、.editorconfig 等项目配置文件',
      'Layer 2 — 决策记录：按文件名关键词匹配，最多返回 5 条（.harness/memory/decisions/）',
      'Layer 3 — 学习记录：最近修改时间排序，最多 20 条（.harness/memory/learnings/）',
      'MemoryManager.record_decision(tag, content) — 覆盖同 tag 旧记录',
      'MemoryManager.record_learning(tag, content) — 每次创建新时间戳文件',
      '不引入向量数据库——文件名 + 标签匹配 + 最近修改时间排序足够',
    ],
    codeExample: `# 记忆注入上下文
memory = MemoryManager(project_root)
context = memory.get_context(query="login bug")
# → "=== Project Conventions ===\\n..."
# → "=== Relevant Decisions ===\\n..."
# → "=== Recent Learnings ===\\n..."

# 记录新的学习
memory.record_learning(
    tag="sql-injection-fix",
    content="修复了 api/users.py 第 42 行的 SQL 注入..."\n)`,
  },
];

const DEMOS = [
  { file: 'tests/demo/demo_guardrail.py', desc: '护栏拦截演示：rm -rf /、DROP TABLE、curl|bash 被拦截', lines: 44 },
  { file: 'tests/demo/demo_sandbox.py', desc: '路径沙箱 + 命令白名单演示：越界阻止、未知命令拦截', lines: 42 },
  { file: 'tests/demo/demo_feedback_loop.py', desc: '反馈闭环演示：失败→修正→通过 完整流程', lines: 40 },
];

const DOCS = [
  { label: 'SPEC.md — 完整技术规约', href: 'https://github.com/jeannie-jy/Glimmer/blob/main/SPEC.md', desc: '27 KB，涵盖问题陈述、功能规约、数据模型、非功能性需求', external: true },
  { label: 'DESIGN.md — 设计系统', href: 'https://github.com/jeannie-jy/Glimmer/blob/main/DESIGN.md', desc: 'Fairy-Tale Dream 主题，CSS 变量、排版、动效系统', external: true },
  { label: 'README.md — 项目文档', href: 'https://github.com/jeannie-jy/Glimmer/blob/main/README.zh.md', desc: '快速开始、API 参考、WebSocket 协议、部署指南', external: true },
  { label: 'GitHub Wiki', href: 'https://github.com/jeannie-jy/Glimmer/wiki', desc: '更多资源和社区文档', external: true },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const TopicCard: React.FC<{ topic: Topic; defaultOpen?: boolean }> = ({ topic, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <motion.div
      className={`topic-card ${open ? 'topic-card--open' : ''}`}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
    >
      <button className="topic-card__header" onClick={() => setOpen(!open)} type="button">
        <span className="topic-card__icon">{topic.icon}</span>
        <div className="topic-card__header-text">
          <h3 className="topic-card__title">{topic.title}</h3>
          <p className="topic-card__summary">{topic.summary}</p>
        </div>
        <ChevronDown size={18} className={`topic-card__chevron ${open ? 'topic-card__chevron--open' : ''}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            className="topic-card__body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="topic-card__details">
              <ul>
                {topic.details.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
            {topic.codeExample && (
              <div className="topic-card__code-section">
                <div className="topic-card__code-label">
                  <FileCode size={14} /> 源码示例
                </div>
                <pre className="topic-card__code"><code>{topic.codeExample}</code></pre>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const DemoCard: React.FC<{ file: string; desc: string; lines: number }> = ({ file, desc, lines }) => (
  <div className="demo-card">
    <div className="demo-card__header">
      <Play size={16} />
      <code className="demo-card__file">{file}</code>
      <span className="demo-card__lines">{lines} lines</span>
    </div>
    <p className="demo-card__desc">{desc}</p>
  </div>
);

const DocLink: React.FC<{ label: string; href: string; desc: string; external?: boolean }> = ({ label, href, desc, external }) => (
  <a
    href={href}
    className="doc-link"
    target={external ? '_blank' : undefined}
    rel={external ? 'noopener noreferrer' : undefined}
  >
    <div className="doc-link__body">
      <span className="doc-link__label">{label}</span>
      <span className="doc-link__desc">{desc}</span>
    </div>
    <ExternalLink size={14} className="doc-link__arrow" />
  </a>
);

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const LearnPage: React.FC = () => (
  <PageTransition>
    <div className="learn-page">

      {/* Header */}
      <motion.div
        className="learn-page__header"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <span className="learn-page__badge">Deep Dive</span>
        <h1 className="learn-page__heading">
          <GraduationCap size={26} /> 学习入口
        </h1>
        <p className="learn-page__intro">
          深入理解 Agent 系统的工程原理——从状态机到护栏，从反馈分析到多模型适配。
          每个机制都是确定性代码，你可以理解每一行，也能修改每一行。
        </p>
      </motion.div>

      {/* =============================================================== */}
      {/* Core Concepts */}
      {/* =============================================================== */}
      <section className="learn-page__section">
        <motion.h2
          className="learn-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <BookOpen size={22} /> 核心概念
        </motion.h2>
        <p className="learn-page__section-desc">
          以下六大模块构成了 Glimmer 的核心架构。每个模块都是纯代码实现，不依赖 LLM 推断。
          点击展开查看详细解释和源码示例。
        </p>
        <div className="topic-list">
          {CORE_TOPICS.map(topic => (
            <TopicCard key={topic.id} topic={topic} defaultOpen={topic.id === 'state-machine'} />
          ))}
        </div>
      </section>

      {/* =============================================================== */}
      {/* Extending Glimmer */}
      {/* =============================================================== */}
      <section className="learn-page__section">
        <motion.h2
          className="learn-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Puzzle size={22} /> 扩展 Glimmer
        </motion.h2>
        <p className="learn-page__section-desc">
          Glimmer 的模块化架构使得添加新工具、新 Provider、新护栏规则非常简单。
          所有扩展点都通过抽象基类定义，不修改核心代码。
        </p>
        <div className="topic-list">
          {EXTENDING_TOPICS.map(topic => (
            <TopicCard key={topic.id} topic={topic} />
          ))}
        </div>
      </section>

      {/* =============================================================== */}
      {/* Interactive Demo */}
      {/* =============================================================== */}
      <section className="learn-page__section">
        <motion.h2
          className="learn-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Play size={22} /> 可运行演示
        </motion.h2>
        <p className="learn-page__section-desc">
          以下 Demo 脚本可直接用 Python 运行，无需 LLM API Key——全部使用 MockLLM。
          适合理解每个机制的独立行为。
        </p>
        <div className="demo-grid">
          {DEMOS.map(demo => (
            <DemoCard key={demo.file} {...demo} />
          ))}
        </div>
        <div className="demo-run-hint">
          <Terminal size={14} />
          <span>运行方式：<code>python {DEMOS[0].file}</code>（从项目根目录）</span>
        </div>
      </section>

      {/* =============================================================== */}
      {/* Documentation */}
      {/* =============================================================== */}
      <section className="learn-page__section">
        <motion.h2
          className="learn-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Library size={22} /> 文档与资源
        </motion.h2>
        <div className="doc-link-list">
          {DOCS.map(doc => (
            <DocLink key={doc.href} {...doc} />
          ))}
        </div>
      </section>

      {/* =============================================================== */}
      {/* Architecture Summary */}
      {/* =============================================================== */}
      <section className="learn-page__section">
        <motion.h2
          className="learn-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Workflow size={22} /> 架构速查
        </motion.h2>
        <div className="arch-summary">
          {[
            { label: '数据流', items: '用户输入 → WebSocket → AgentLoop.run() → 状态机驱动 → LLM 调用 → 工具分发 → 护栏检查 → 反馈分析 → 循环 → 完成' },
            { label: '文件存储', items: '.harness/config.yaml（配置）、.harness/credentials/.key（凭据）、.harness/memory/*.json（记忆）' },
            { label: '数据库', items: 'PostgreSQL（部署模式）— users + user_configs + sessions + messages 四表' },
            { label: '安全边界', items: 'Docker 沙箱（--network none, 512MB, 1CPU）+ 三层护栏 + shell=False + timeout' },
            { label: '测试策略', items: 'MockLLMAdapter → 零网络全链路单测 + pytest + pytest-asyncio + 94+ 用例' },
            { label: '前端技术', items: 'React 18 + TypeScript 5 + Vite 6 + Framer Motion v11 + CSS Variables + WebSocket' },
          ].map(item => (
            <div key={item.label} className="arch-summary-item">
              <span className="arch-summary-item__label">{item.label}</span>
              <span className="arch-summary-item__value">{item.items}</span>
            </div>
          ))}
        </div>
      </section>

    </div>
  </PageTransition>
);

export default LearnPage;
