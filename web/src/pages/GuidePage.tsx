import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import '../styles/guide.css';
import {
  Compass, Terminal, Download, Settings, Rocket,
  CheckCircle, AlertTriangle, Info, ExternalLink,
  ChevronDown, Code2, Zap, Shield,
  Play, BookOpen, Wrench
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const FAQ_DATA = [
  { q: '启动后浏览器无法访问', a: '检查 8000 端口是否被占用（lsof -i :8000）。确认 uvicorn 输出无报错。本地模式访问 http://localhost:8000，部署模式访问 http://localhost。' },
  { q: '"API key not configured"', a: '检查 Settings 面板是否已保存 API Key。本地模式下确认 .harness/credentials/ 目录下有对应的 .key 文件。部署模式下确认 user_configs 表中有加密的 api_key_enc 字段。' },
  { q: '"Authentication required" (WebSocket 4001)', a: 'JWT 令牌过期（7 天有效期）。退出后重新登录 GitHub OAuth。本地模式不应出现此错误。' },
  { q: '"Command not in whitelist"', a: 'Agent 尝试使用不在白名单中的命令。在弹窗中 Approve（单次有效）或在 config.yaml 的 command_whitelist_extra 中永久添加。' },
  { q: 'Agent 反复修正但测试始终不通过', a: '检查 RetryPolicy 的 is_stuck() 检测——连续 3 次相同失败会自动终止。如果问题确实复杂，手动介入给出更精确的指示。' },
  { q: 'Docker 沙箱创建失败', a: '确认 Docker daemon 正在运行（docker ps）。检查 DOCKER_HOST 环境变量。确保 sandbox 镜像已构建（make build-sandbox）。' },
  { q: '"Write outside sandbox"', a: 'Agent 尝试写入 sandbox_root 之外的文件。调整 config.yaml 中的 sandbox_root，或通过 PathSandbox.add_writable_dir() 添加可写目录。' },
  { q: '前端样式异常或动画不流畅', a: '清除浏览器缓存。确认 CSS 变量在 index.css 中正确定义。如果启用了 prefers-reduced-motion，动画会自动降级。' },
];

// ---------------------------------------------------------------------------
// Sub-components (must be defined before SECTIONS which references them)
// ---------------------------------------------------------------------------

const FaqItem: React.FC<{ q: string; a: string }> = ({ q, a }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className={`guide-faq-item ${open ? 'guide-faq-item--open' : ''}`}>
      <button className="guide-faq-item__q" onClick={() => setOpen(!open)} type="button">
        <span>{q}</span>
        <ChevronDown size={16} className={`guide-faq-item__chevron ${open ? 'guide-faq-item__chevron--open' : ''}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div className="guide-faq-item__a" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}>
            <p>{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface GuideSection {
  id: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  content: React.ReactNode;
}

const SECTIONS: GuideSection[] = [
  {
    id: 'prerequisites',
    icon: <CheckCircle size={20} />,
    title: '前置条件',
    subtitle: '开始之前需要准备的环境和工具',
    content: (
      <div className="guide-section__body">
        <div className="guide-prereq-grid">
          <div className="guide-prereq-card">
            <h4>本地模式（单用户）</h4>
            <ul>
              <li><strong>Python</strong> ≥ 3.12（<code>python --version</code>）</li>
              <li><strong>pip</strong> 最新版本（<code>pip install --upgrade pip</code>）</li>
              <li><strong>Node.js</strong> ≥ 22（可选，仅开发前端时需要）</li>
              <li>任意 LLM API Key（Anthropic / OpenAI / DeepSeek / ...）</li>
            </ul>
          </div>
          <div className="guide-prereq-card">
            <h4>部署模式（多用户）</h4>
            <ul>
              <li>以上所有 +</li>
              <li><strong>Docker</strong> & <strong>Docker Compose</strong>（<code>docker compose version</code>）</li>
              <li><strong>GitHub OAuth App</strong>（<a href="https://github.com/settings/developers" target="_blank" rel="noopener noreferrer">创建 <ExternalLink size={10} /></a>）</li>
              <li>可访问的 PostgreSQL 实例</li>
            </ul>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'install',
    icon: <Download size={20} />,
    title: '安装与启动',
    subtitle: '克隆项目、安装依赖、启动服务',
    content: (
      <div className="guide-section__body">
        <div className="guide-tabs">
          <div className="guide-tab-content">
            <h4>本地模式 — 最快 2 分钟上手</h4>
            <div className="guide-code-block">
              <div className="guide-code-block__header">
                <span className="guide-code-block__dots"><span /><span /><span /></span>
                <span className="guide-code-block__title">Terminal</span>
              </div>
              <pre className="guide-code-block__code">
{`# 1. 克隆仓库
git clone https://github.com/jeannie-jy/Glimmer.git
cd Glimmer

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 启动开发服务器
make dev
# → FastAPI 运行在 http://localhost:8000
# → 自动热重载已启用`}
              </pre>
            </div>
            <p className="guide-note">
              <Info size={14} /> 访问 <code>http://localhost:8000</code>，点击右上角<strong> Settings</strong>，
              选择 LLM Provider 并填入 API Key，即可开始使用。
            </p>
          </div>
        </div>

        <div className="guide-divider" />

        <h4>部署模式 — 一键生产部署</h4>
        <div className="guide-code-block">
          <div className="guide-code-block__header">
            <span className="guide-code-block__dots"><span /><span /><span /></span>
            <span className="guide-code-block__title">Terminal</span>
          </div>
          <pre className="guide-code-block__code">
{`# 1. 配置环境变量
cp .env.example .env
vim .env  # 填入 GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, 密码

# 2. 一键部署（构建沙箱镜像 + 启动 nginx + API + PostgreSQL）
make deploy
# → http://localhost (nginx 80 端口)`}
          </pre>
        </div>
        <p className="guide-note">
          <Info size={14} /> <code>make deploy</code> 会自动完成沙箱镜像构建 → Docker Compose 启动三个服务。
          首次构建约需 2-3 分钟。
        </p>
      </div>
    ),
  },
  {
    id: 'configure',
    icon: <Settings size={20} />,
    title: '配置详解',
    subtitle: 'LLM Provider、API Key、护栏与工具配置',
    content: (
      <div className="guide-section__body">
        <h4>Web UI — Settings 面板</h4>
        <p className="guide-text">
          在 Agent 页面右侧面板，点击 <strong>Settings</strong> 标签，可配置：
        </p>
        <div className="guide-config-table">
          <div className="guide-config-row guide-config-row--header">
            <span>字段</span><span>说明</span><span>示例</span>
          </div>
          <div className="guide-config-row">
            <span><strong>Provider</strong></span>
            <span>选择 Anthropic（原生）或 OpenAI Compatible（自定义 Base URL）</span>
            <span><code>Anthropic</code></span>
          </div>
          <div className="guide-config-row">
            <span><strong>Base URL</strong></span>
            <span>仅 OpenAI Compatible 模式需要。支持 DeepSeek / Qwen / Ollama / vLLM 等</span>
            <span><code>https://api.deepseek.com</code></span>
          </div>
          <div className="guide-config-row">
            <span><strong>Model Name</strong></span>
            <span>模型 ID，取决于你选择的 Provider</span>
            <span><code>claude-sonnet-5</code> / <code>deepseek-chat</code></span>
          </div>
          <div className="guide-config-row">
            <span><strong>API Key</strong></span>
            <span>加密存储。查看时只显示掩码（sk-...wxyz）</span>
            <span><code>sk-ant-api03-...</code></span>
          </div>
        </div>

        <div className="guide-divider" />

        <h4>配置文件 — <code>.harness/config.yaml</code></h4>
        <p className="guide-text">
          项目根目录下的 <code>.harness/config.yaml</code> 支持更详细的配置。
          优先级：项目配置 &gt; 全局配置（<code>~/.harness/config.yaml</code>）&gt; 内置默认值。
        </p>
        <div className="guide-code-block">
          <div className="guide-code-block__header">
            <span className="guide-code-block__dots"><span /><span /><span /></span>
            <span className="guide-code-block__title">.harness/config.yaml</span>
          </div>
          <pre className="guide-code-block__code">
{`model:
  provider: anthropic          # "anthropic" | "openai"
  model_id: claude-sonnet-5
  max_tokens: 4096

guardrails:
  max_retries: 3               # 最大自修正次数 (1-10)
  sandbox_root: "."            # 路径沙箱根目录
  command_whitelist_extra: []  # 额外白名单命令
  timeout_seconds: 30          # 工具执行超时 (秒)

tools:
  enabled:
    - read_file
    - write_file
    - execute_shell
    - run_tests
    - search_code

memory:
  max_context_tokens: 8000
  learnings_limit: 20`}
          </pre>
        </div>

        <div className="guide-divider" />

        <h4>支持的 LLM Provider 配置示例</h4>
        <div className="guide-provider-grid">
          {[
            { name: 'Anthropic', config: 'provider: anthropic\nmodel_id: claude-sonnet-5', note: '无需 Base URL，内置 SDK' },
            { name: 'OpenAI', config: 'provider: openai\nmodel_id: gpt-4o', note: '无需 Base URL，内置 SDK' },
            { name: 'DeepSeek', config: 'provider: openai\nbase_url: https://api.deepseek.com\nmodel_id: deepseek-chat', note: '性价比高，中文能力强' },
            { name: 'Qwen (通义千问)', config: 'provider: openai\nbase_url: https://dashscope.aliyuncs.com/compatible-mode/v1\nmodel_id: qwen-plus', note: '阿里云，OpenAI 兼容' },
            { name: 'Ollama (本地)', config: 'provider: openai\nbase_url: http://localhost:11434/v1\nmodel_id: llama3', note: '本地运行，无 API 费用，隐私最佳' },
          ].map(p => (
            <div key={p.name} className="guide-provider-card">
              <h5>{p.name}</h5>
              <pre className="guide-provider-card__config"><code>{p.config}</code></pre>
              <span className="guide-provider-card__note">{p.note}</span>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'first-task',
    icon: <Play size={20} />,
    title: '第一次任务',
    subtitle: '提交编码任务，观察 Agent 如何规划、执行、自我修正',
    content: (
      <div className="guide-section__body">
        <h4>典型工作流</h4>
        <div className="guide-workflow">
          {[
            { step: '1', title: '输入任务', desc: '在 Agent 页面输入框描述你的需求。可以附带文件（支持 .py / .js / .ts 等，最大 95KB）。', icon: <Code2 size={16} /> },
            { step: '2', title: 'Agent 规划', desc: '状态机转入 PLANNING。LLM 分析任务，决定调用哪些工具。流式输出思考过程。', icon: <Zap size={16} /> },
            { step: '3', title: '工具执行', desc: 'EXECUTING 状态。工具调用经过三层护栏检查，安全后在沙箱中执行。', icon: <Terminal size={16} /> },
            { step: '4', title: '反馈分析', desc: 'OBSERVING 状态。确定性分析执行结果。测试通过→继续；失败→自动修正。', icon: <Shield size={16} /> },
            { step: '5', title: '查看结果', desc: '任务完成后查看：Token 用量、工具调用次数、修改的文件、最终代码。', icon: <CheckCircle size={16} /> },
          ].map(w => (
            <div key={w.step} className="guide-workflow-item">
              <div className="guide-workflow-item__step">
                <span className="guide-workflow-item__num">{w.step}</span>
                <span className="guide-workflow-item__icon">{w.icon}</span>
              </div>
              <div className="guide-workflow-item__body">
                <h5 className="guide-workflow-item__title">{w.title}</h5>
                <p className="guide-workflow-item__desc">{w.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="guide-divider" />

        <h4>示例任务</h4>
        <div className="guide-examples">
          {[
            { task: '帮我用 Python 写一个快速排序算法', desc: 'Agent 会使用 write_file 创建文件，然后用 execute_shell 运行测试', tags: ['文件创建', '代码生成'] },
            { task: '修复 tests/test_login.py 中的失败测试', desc: 'Agent 会用 read_file 读代码 → 分析 → write_file 修复 → run_tests 验证', tags: ['调试', '自修正'] },
            { task: '在代码库中搜索所有 SQL 注入风险', desc: 'Agent 会用 search_code 搜索危险模式，然后报告发现', tags: ['代码分析', '安全审计'] },
            { task: '为 src/utils.py 编写单元测试', desc: 'Agent 会先读代码理解逻辑，再创建测试文件并验证', tags: ['测试生成', '代码理解'] },
          ].map((ex, i) => (
            <div key={i} className="guide-example-card">
              <div className="guide-example-card__task">
                <Play size={14} />
                <span>{ex.task}</span>
              </div>
              <p className="guide-example-card__desc">{ex.desc}</p>
              <div className="guide-example-card__tags">
                {ex.tags.map(t => <span key={t} className="guide-example-card__tag">{t}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'best-practices',
    icon: <BookOpen size={20} />,
    title: '最佳实践',
    subtitle: '让 Agent 更高效、更安全的提示技巧和配置建议',
    content: (
      <div className="guide-section__body">
        <div className="guide-tips">
          {[
            { title: '明确具体目标', desc: '"修 bug" ❌ → "修复 src/auth.py 第 42 行 login 函数中 JWT token 过期时间为 0 的 bug" ✅。越具体越好。', icon: <CheckCircle size={16} /> },
            { title: '分批提交任务', desc: '复杂需求拆成多个小任务。Agent 在单次会话中保留上下文，可以逐步推进。每次完成后检查结果再继续。', icon: <CheckCircle size={16} /> },
            { title: '善用附件功能', desc: '涉及现有代码时，直接上传文件作为上下文附件（最多 95KB）。Agent 在生成代码前会参考附件内容。', icon: <CheckCircle size={16} /> },
            { title: '合理设置 max_retries', desc: '调试阶段设为 3-5 次给 Agent 足够的修正机会，生产环境设为 2-3 次以节省 Token。', icon: <CheckCircle size={16} /> },
            { title: '扩展命令白名单', desc: '如果常用某个不在白名单的工具（如 poetry / yarn），将其加入 command_whitelist_extra，避免每次手动审批。', icon: <CheckCircle size={16} /> },
            { title: '关注护栏弹窗', desc: '当 Agent 尝试执行危险操作时，系统会弹出 GuardrailModal。仔细阅读原因后再决定 Approve 或 Reject。', icon: <AlertTriangle size={16} /> },
          ].map((tip, i) => (
            <div key={i} className="guide-tip-card">
              <div className="guide-tip-card__icon">{tip.icon}</div>
              <div className="guide-tip-card__body">
                <h5>{tip.title}</h5>
                <p>{tip.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'troubleshooting',
    icon: <Wrench size={20} />,
    title: '常见问题排查',
    subtitle: '遇到问题？这里是最常见的解决方案',
    content: (
      <div className="guide-section__body">
        <div className="guide-faq">
          {FAQ_DATA.map((faq, i) => (
            <FaqItem key={i} {...faq} />
          ))}
        </div>
      </div>
    ),
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const SectionNav: React.FC<{ sections: GuideSection[]; activeId: string; onSelect: (id: string) => void }> = ({ sections, activeId, onSelect }) => (
  <nav className="guide-nav">
    <h4 className="guide-nav__title">目录</h4>
    {sections.map(s => (
      <button
        key={s.id}
        className={`guide-nav__item ${activeId === s.id ? 'guide-nav__item--active' : ''}`}
        onClick={() => onSelect(s.id)}
        type="button"
      >
        <span className="guide-nav__icon">{s.icon}</span>
        <span className="guide-nav__label">{s.title}</span>
      </button>
    ))}
  </nav>
);

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const GuidePage: React.FC = () => {
  const [activeSection, setActiveSection] = useState(SECTIONS[0].id);

  return (
    <PageTransition>
      <div className="guide-page">

        {/* Header */}
        <motion.div
          className="guide-page__header"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <span className="guide-page__badge">Getting Started</span>
          <h1 className="guide-page__heading">
            <Compass size={26} /> 使用指南
          </h1>
          <p className="guide-page__intro">
            从零开始，在本地或服务器上部署你的 AI 编程助手。覆盖安装、配置、使用和问题排查的全流程。
          </p>
        </motion.div>

        {/* Layout: Nav + Content */}
        <div className="guide-page__layout">
          <SectionNav sections={SECTIONS} activeId={activeSection} onSelect={setActiveSection} />

          <div className="guide-page__content">
            {SECTIONS.map((section, idx) => (
              <motion.section
                key={section.id}
                id={section.id}
                className={`guide-section ${activeSection === section.id ? 'guide-section--active' : ''}`}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.04 }}
              >
                <div className="guide-section__header">
                  <span className="guide-section__icon">{section.icon}</span>
                  <div>
                    <h2 className="guide-section__title">{section.title}</h2>
                    <p className="guide-section__subtitle">{section.subtitle}</p>
                  </div>
                </div>
                {section.content}
              </motion.section>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <motion.div
          className="guide-page__cta"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Rocket size={22} />
          <div>
            <h3>准备就绪？</h3>
            <p>前往 <a href="/agent">Agent 页面</a> 开始你的第一次"施法"。</p>
          </div>
        </motion.div>

      </div>
    </PageTransition>
  );
};

export default GuidePage;
