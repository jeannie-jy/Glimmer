import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import '../styles/about.css';
import {
  Wand2, Brain, Shield, BarChart3, Cpu, Layers,
  Workflow, GitBranch, Lock, Zap, Server, Palette,
  Box, Terminal, Network, Code2, FileCode, TestTube,
  Database, Container, Globe, Package
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const PRINCIPLES = [
  {
    icon: <Cpu size={28} />,
    title: '确定性优先',
    subtitle: 'Determinism over Prompts',
    desc: '状态机、反馈分析器、护栏引擎——所有决策机制都是纯函数代码，而非 LLM 提示词。去掉 LLM 后系统仍可完整运行并通过单元测试。这是 Glimmer 最核心的工程纪律。',
  },
  {
    icon: <Layers size={28} />,
    title: '纵深防御',
    subtitle: 'Defense in Depth',
    desc: '三层护栏串行检查——路径沙箱阻止文件越界，命令白名单拦截未知程序，正则黑名单捕获危险参数。每层独立可测，组合提供纵深防护。',
  },
  {
    icon: <Workflow size={28} />,
    title: '可插拔架构',
    subtitle: 'Pluggable Everything',
    desc: 'LLM 供应商、工具、护栏规则、反馈策略——全部通过抽象基类定义接口。切换 Anthropic 到 DeepSeek 只需改一行配置，无需修改核心代码。',
  },
  {
    icon: <GitBranch size={28} />,
    title: '可观测性内置',
    subtitle: 'Observable by Default',
    desc: '每次状态转换、每个工具调用、每条反馈判定都通过 WebSocket 实时广播。前端状态指示器、工具卡片、反馈横幅让你完全掌控 Agent 的一举一动。',
  },
  {
    icon: <Lock size={28} />,
    title: '安全零信任',
    subtitle: 'Zero Trust Security',
    desc: 'API Key 绝不落盘明文（AES-256-GCM 加密或 OS 钥匙串）。Docker 沙箱无网络、内存限制、进程限制。凭据掩码显示，绝不出现于日志或 API 响应中。',
  },
  {
    icon: <Zap size={28} />,
    title: '测试驱动设计',
    subtitle: 'Test-Driven Architecture',
    desc: 'MockLLMAdapter 使得全流程可在零网络环境下确定性测试。94+ 测试用例覆盖所有核心路径，CI 在每次 push 自动运行。',
  },
];

const ARCH_LAYERS = [
  {
    label: 'Web UI',
    color: '#f8a4c8',
    items: ['React 18 + TypeScript', 'Framer Motion', 'Canvas 粒子系统', 'WebSocket 实时流'],
  },
  {
    label: 'FastAPI Server',
    color: '#e8879b',
    items: ['JWT 鉴权中间件', 'WebSocket 会话管理', 'REST API (认证/配置/会话/文件)', 'slowapi 限流 (60/min)'],
  },
  {
    label: 'Agent Core',
    color: '#d4859e',
    items: ['确定性状态机 (8 态)', '三层护栏引擎', '5 内置工具 + 自定义扩展', 'LLM 适配器 (Anthropic/OpenAI/Mock)'],
  },
  {
    label: 'Infrastructure',
    color: '#b0708a',
    items: ['PostgreSQL (多用户模式)', 'Docker 沙箱 (每会话隔离)', 'Nginx 反向代理', 'Alembic 数据库迁移'],
  },
];

const TECH_STACK = [
  { cat: '语言', items: ['Python 3.12+', 'TypeScript 5'] },
  { cat: 'Web 框架', items: ['FastAPI', 'Uvicorn', 'React 18'] },
  { cat: 'LLM SDK', items: ['Anthropic SDK', 'OpenAI SDK'] },
  { cat: '数据', items: ['Pydantic v2', 'SQLAlchemy 2.0', 'PostgreSQL 16', 'Alembic'] },
  { cat: '安全', items: ['AES-256-GCM', 'HKDF', 'python-jose (JWT)', 'keyring'] },
  { cat: '测试', items: ['pytest', 'pytest-asyncio', 'httpx'] },
  { cat: '前端', items: ['Vite 6', 'React Router v7', 'Framer Motion v11', 'Lucide React'] },
  { cat: '部署', items: ['Docker', 'Docker Compose', 'Nginx', 'PyInstaller'] },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const ArchitectureDiagram: React.FC = () => {
  const [activeLayer, setActiveLayer] = useState<number | null>(null);

  return (
    <div className="arch-diagram">
      {ARCH_LAYERS.map((layer, i) => (
        <motion.div
          key={layer.label}
          className={`arch-layer ${activeLayer === i ? 'arch-layer--active' : ''}`}
          style={{ '--layer-color': layer.color } as React.CSSProperties}
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.12 }}
          onMouseEnter={() => setActiveLayer(i)}
          onMouseLeave={() => setActiveLayer(null)}
        >
          <div className="arch-layer__header">
            <span className="arch-layer__dot" />
            <span className="arch-layer__label">{layer.label}</span>
          </div>
          <AnimatePresence>
            {(activeLayer === i) && (
              <motion.div
                className="arch-layer__body"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <ul className="arch-layer__items">
                  {layer.items.map(item => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      ))}
      <div className="arch-diagram__connectors">
        <span className="arch-diagram__arrow">▼ WebSocket + REST ▼</span>
        <span className="arch-diagram__arrow">▼ 函数调用 ▼</span>
        <span className="arch-diagram__arrow">▼ 数据持久化 ▼</span>
      </div>
    </div>
  );
};

const PhilosophyQuote: React.FC<{ en: string; zh: string }> = ({ en, zh }) => (
  <div className="philosophy-quote">
    <p className="philosophy-quote__en">"{en}"</p>
    <p className="philosophy-quote__zh">{zh}</p>
  </div>
);

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const AboutPage: React.FC = () => (
  <PageTransition>
    <div className="about-page">

      {/* ================================================================= */}
      {/* Hero */}
      {/* ================================================================= */}
      <section className="about-page__hero">
        <motion.div
          className="about-page__hero-text"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="about-page__badge">Open Source · MIT License</span>
          <h1 className="about-page__heading">
            <Wand2 size={28} /> 什么是 Glimmer？
          </h1>
          <p className="about-page__tagline">
            <strong>Agent = LLM + Harness</strong>
          </p>
          <p className="about-page__hero-desc">
            Glimmer 不是一个"用 LLM 封装一切"的 Agent 框架——它是一个
            <strong> 从零构建的 Harness 内核</strong>。
            状态机、护栏、反馈分析、重试策略——每个机制都是自己编写的确定性代码，
            而非隐藏在框架黑盒中的提示词工程。剥离真实 LLM 后，
            系统仍可通过 Mock LLM 进行完整的确定性单元测试。
          </p>
        </motion.div>
      </section>

      {/* ================================================================= */}
      {/* Philosophy */}
      {/* ================================================================= */}
      <section className="about-page__section">
        <motion.h2
          className="about-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Brain size={22} /> 设计哲学
        </motion.h2>
        <PhilosophyQuote
          en="The value of an agent system lies in its harness — the code that governs, guards, and guides — not in the prompt that asks the LLM to do those things."
          zh="Agent 系统的价值在于 Harness 层——治理、防护、引导的确定性代码——而非让 LLM 自己去做的提示词。"
        />
        <div className="about-page__principles">
          {PRINCIPLES.map((p, i) => (
            <motion.div
              key={p.title}
              className="principle-card"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              whileHover={{ y: -3 }}
            >
              <div className="principle-card__icon">{p.icon}</div>
              <div className="principle-card__body">
                <h3 className="principle-card__title">{p.title}</h3>
                <span className="principle-card__subtitle">{p.subtitle}</span>
                <p className="principle-card__desc">{p.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ================================================================= */}
      {/* Architecture */}
      {/* ================================================================= */}
      <section className="about-page__section">
        <motion.h2
          className="about-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Box size={22} /> 系统架构
        </motion.h2>
        <p className="about-page__section-desc">
          Glimmer 采用四层分层架构：前端展示层 → API 网关层 → Agent 核心引擎层 → 基础设施层。
          层间通过 WebSocket（实时双向）、REST（请求-响应）和 Python 函数调用通信。
        </p>
        <ArchitectureDiagram />

        {/* Architecture text diagram */}
        <div className="arch-text-diagram">
          <pre className="arch-text-diagram__code">
{`┌─────────────────────────────────────────────────┐
│              Web UI (React + TypeScript)          │
│  ChatView │ ToolPanel │ Settings │ GuardrailModal │
└─────────────────┬───────────────────────────────┘
                  │  WebSocket + REST
┌─────────────────┴───────────────────────────────┐
│              FastAPI Server                       │
│  WS Handler │ Auth │ Config API │ Session API    │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│              Agent Core (State Machine)           │
│                                                   │
│  ┌──────┐  ┌───────────┐  ┌───────────────┐     │
│  │ Loop │─▶│ Guardrail │─▶│ Tool Dispatch │     │
│  │Engine│  │ Engine(3L)│  │   Registry    │     │
│  └──────┘  └───────────┘  └───────────────┘     │
│      │                           │               │
│  ┌───┴───┐                ┌──────┴──────┐       │
│  │  LLM  │                │  Feedback   │       │
│  │Adapters│               │  Analyzer   │       │
│  └───────┘                └─────────────┘       │
│                                                   │
│  ┌──────┐  ┌──────┐  ┌──────────┐               │
│  │Memory│  │Config│  │Credential│               │
│  └──────┘  └──────┘  └──────────┘               │
└─────────────────────────────────────────────────┘`}
          </pre>
        </div>
      </section>

      {/* ================================================================= */}
      {/* Component Breakdown */}
      {/* ================================================================= */}
      <section className="about-page__section">
        <motion.h2
          className="about-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Package size={22} /> 核心组件详解
        </motion.h2>

        <div className="component-breakdown">
          <motion.div
            className="comp-card"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <div className="comp-card__header">
              <Code2 size={20} />
              <h3>harness/ — Agent 核心引擎</h3>
              <span className="comp-card__lang">Python 3.12+</span>
            </div>
            <div className="comp-card__grid">
              <div className="comp-card__item">
                <span className="comp-card__item-name">loop.py</span>
                <span className="comp-card__item-desc">主循环协调器——驱动状态机、调度工具、管理重试</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">state_machine.py</span>
                <span className="comp-card__item-desc">确定性状态转换表——纯函数，零 LLM 参与</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">guardrails/</span>
                <span className="comp-card__item-desc">三层护栏——路径沙箱 + 命令白名单 + 正则黑名单</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">feedback/</span>
                <span className="comp-card__item-desc">确定性反馈分析——exit code + 结构化报告 + 语法检查</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">llm/</span>
                <span className="comp-card__item-desc">可插拔适配器——Anthropic / OpenAI / Mock（ABC 接口）</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">tools/</span>
                <span className="comp-card__item-desc">5 个内置工具——文件读写、Shell 执行、测试运行、代码搜索</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="comp-card"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            <div className="comp-card__header">
              <Server size={20} />
              <h3>server/ — API 服务层</h3>
              <span className="comp-card__lang">FastAPI</span>
            </div>
            <div className="comp-card__grid">
              <div className="comp-card__item">
                <span className="comp-card__item-name">ws_handler.py</span>
                <span className="comp-card__item-desc">WebSocket 总控——会话生命周期、Docker 容器管理、多轮对话</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">auth_routes.py</span>
                <span className="comp-card__item-desc">GitHub OAuth 认证——登录重定向、回调换 JWT、用户信息</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">config_routes.py</span>
                <span className="comp-card__item-desc">配置 CRUD + 凭据管理——双模式（本地文件 / 数据库加密）</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">session_registry.py</span>
                <span className="comp-card__item-desc">内存会话注册表——跨路由共享容器引用（TTL: 1h）</span>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="comp-card"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <div className="comp-card__header">
              <Globe size={20} />
              <h3>web/ — 前端展示层</h3>
              <span className="comp-card__lang">React + TypeScript</span>
            </div>
            <div className="comp-card__grid">
              <div className="comp-card__item">
                <span className="comp-card__item-name">AgentPage + ChatView</span>
                <span className="comp-card__item-desc">三栏布局——历史会话｜实时聊天（流式 + 工具卡片 + 护栏弹窗）｜设置/文件面板</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">ParticleCanvas + FairySprite</span>
                <span className="comp-card__item-desc">Canvas 2D 粒子系统——背景闪粉 + 掠过粒子 + 仙女轨道 + 魔法棒爆发</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">useWebSocket + useSession</span>
                <span className="comp-card__item-desc">自定义 Hooks——WebSocket 连接管理 + 消息队列 + 状态提取</span>
              </div>
              <div className="comp-card__item">
                <span className="comp-card__item-name">Design System (DESIGN.md)</span>
                <span className="comp-card__item-desc">Fairy-Tale Dream 主题——50+ CSS 变量、响应式、无障碍、prefers-reduced-motion</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ================================================================= */}
      {/* Tech Stack */}
      {/* ================================================================= */}
      <section className="about-page__section">
        <motion.h2
          className="about-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Terminal size={22} /> 技术栈
        </motion.h2>
        <div className="tech-grid">
          {TECH_STACK.map(cat => (
            <motion.div
              key={cat.cat}
              className="tech-group"
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <h4 className="tech-group__cat">{cat.cat}</h4>
              <div className="tech-group__tags">
                {cat.items.map(t => (
                  <span key={t} className="tech-group__tag">{t}</span>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ================================================================= */}
      {/* Why Glimmer */}
      {/* ================================================================= */}
      <section className="about-page__section">
        <motion.h2
          className="about-page__section-title"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <Shield size={22} /> 为什么选择 Glimmer？
        </motion.h2>
        <div className="why-grid">
          {[
            { q: '与其他 Agent 框架的区别？', a: 'LangChain/AutoGen 将核心循环封装为黑盒。Glimmer 反其道而行——每个机制都是自己编写的确定性代码，你理解每一行，也能修改每一行。' },
            { q: '为什么用状态机而不是事件驱动？', a: '状态机是 Agent 控制流最可验证的模型。每个 (state, event) → next_state 转换都是纯函数，可独立单测。事件驱动在复杂场景下难以穷举和验证。' },
            { q: '为什么反馈分析不用 LLM？', a: 'LLM 判断测试通过/失败不如 exit_code 可靠——它可能产生幻觉。确定性解析器（exit_code + 结构化报告 + 语法检查）零幻觉、零延迟、完全可测。' },
            { q: '产品级还是教育项目？', a: '两者兼具。代码质量达到生产标准（94+ 测试、Docker 部署、CI/CD），同时每个机制的设计决策都在文档中详细解释，适合学习 Agent 系统工程。' },
          ].map((item, i) => (
            <motion.div
              key={i}
              className="why-item"
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
            >
              <h4 className="why-item__q">{item.q}</h4>
              <p className="why-item__a">{item.a}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ================================================================= */}
      {/* Stats */}
      {/* ================================================================= */}
      <section className="about-page__section">
        <motion.div
          className="stats-row"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          {[
            { value: '8', label: 'Agent 状态' },
            { value: '3', label: '护栏层' },
            { value: '5', label: '内置工具' },
            { value: '7+', label: 'LLM 供应商' },
            { value: '94+', label: '测试用例' },
            { value: '6', label: '前端页面' },
          ].map(s => (
            <div key={s.label} className="stat-item">
              <span className="stat-item__value">{s.value}</span>
              <span className="stat-item__label">{s.label}</span>
            </div>
          ))}
        </motion.div>
      </section>

      {/* ================================================================= */}
      {/* Footer */}
      {/* ================================================================= */}
      <motion.footer
        className="about-page__footer"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      >
        <p>Built with ❤️ using Python, FastAPI, React, and a love for deterministic software.</p>
        <p>MIT License · Copyright © 2026 <a href="https://github.com/jingyu-wang" target="_blank" rel="noopener noreferrer">Jingyu Wang</a></p>
        <p className="about-page__footer-links">
          <a href="https://github.com/jingyu-wang/lite-agent-harness" target="_blank" rel="noopener noreferrer">GitHub</a>
          <span>·</span>
          <a href="https://github.com/jingyu-wang/lite-agent-harness/issues" target="_blank" rel="noopener noreferrer">Issues</a>
          <span>·</span>
          <a href="/SPEC.md">SPEC</a>
        </p>
      </motion.footer>

    </div>
  </PageTransition>
);

export default AboutPage;
