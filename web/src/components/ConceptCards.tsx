import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Shield, BarChart3, Brain, Library, BookOpen, Play } from 'lucide-react';

interface Concept { title: string; icon: React.ReactNode; summary: string; details: string[]; }

const CONCEPTS: Concept[] = [
  { title: '状态机（State Machine）', icon: <Zap size={20} />, summary: 'deterministic transition table — 纯函数路由决策', details: ['状态：IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → COMPLETED', '转换由纯函数 transition(state, event) 计算，无 LLM 参与', '可完全在单元测试中验证（test_state_machine.py）'] },
  { title: '三层护栏（Guardrails）', icon: <Shield size={20} />, summary: '路径沙箱 + 命令白名单 + 正则黑名单', details: ['Layer 1 - PathSandbox：限制文件读写范围', 'Layer 2 - CommandWhitelist：仅允许安全命令通过', 'Layer 3 - PatternBlacklist：拦截危险模式（rm -rf / 等）', '每层可返回 ALLOW / BLOCK / ASK_HUMAN'] },
  { title: '确定性反馈（Feedback Analysis）', icon: <BarChart3 size={20} />, summary: 'exit-code 和结构化报告分析，不依赖 LLM', details: ['run_tests → 解析 pytest-json-report', 'execute_shell → exit code 判定', 'RetryPolicy 检测 stuck loop（连续3次相同失败）'] },
  { title: '多模型适配（LLM Adapters）', icon: <Brain size={20} />, summary: '统一接口，即插即用', details: ['Anthropic：Messages API（claude-sonnet-5 等）', 'OpenAI：Chat Completions API（gpt-4o 等）', 'Mock：预设回复，零网络测试', '通过 ABC 抽象基类实现新 Provider'] },
];

const DEMOS = [
  { name: 'demo_guardrail.py', desc: '演示护栏拦截 rm -rf / 等危险命令' },
  { name: 'demo_sandbox.py', desc: '演示路径沙箱 + 命令白名单' },
  { name: 'demo_feedback_loop.py', desc: '演示 Agent 失败 → 修正 → 完成流程' },
];

const ConceptCards: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="learn-section">
      <h2 className="learn-section__title"><Library size={20} /> 核心概念</h2>
      <div className="concept-list">
        {CONCEPTS.map((c, i) => (
          <motion.div key={c.title} className={`concept-card ${openIndex === i ? 'concept-card--open' : ''}`} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}>
            <button className="concept-card__header" onClick={() => setOpenIndex(openIndex === i ? null : i)} type="button">
              <span className="concept-card__icon">{c.icon}</span>
              <div className="concept-card__header-text">
                <h3 className="concept-card__title">{c.title}</h3>
                <p className="concept-card__summary">{c.summary}</p>
              </div>
              <span className="concept-card__expand">{openIndex === i ? '▲' : '▼'}</span>
            </button>
            <AnimatePresence>
              {openIndex === i && (
                <motion.div className="concept-card__body" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                  <ul className="concept-card__details">{c.details.map((d, j) => (<li key={j}>{d}</li>))}</ul>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      <h2 className="learn-section__title" style={{ marginTop: 'var(--space-8)' }}><BookOpen size={20} /> 文档链接</h2>
      <div className="learn-links">
        <a href="/README.md" className="learn-link">README — 项目文档</a>
        <a href="/DESIGN.md" className="learn-link">DESIGN.md — 设计系统</a>
        <a href="https://github.com/jingyu-wang/lite-agent-harness/wiki" target="_blank" rel="noopener noreferrer" className="learn-link">GitHub Wiki — 更多资源</a>
      </div>

      <h2 className="learn-section__title" style={{ marginTop: 'var(--space-8)' }}><Play size={20} /> 演示 Demo</h2>
      <div className="demo-list">
        {DEMOS.map((d) => (
          <div key={d.name} className="demo-item">
            <code className="demo-item__name">{d.name}</code>
            <span className="demo-item__desc">{d.desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConceptCards;
