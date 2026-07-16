import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Shield, BarChart3, Zap, KeyRound, Container } from 'lucide-react';

const FEATURES = [
  { icon: <Brain size={24} />, title: '多模型支持', desc: 'Anthropic Messages API 和 OpenAI Chat Completions API，统一抽象接口' },
  { icon: <Shield size={24} />, title: '三层护栏', desc: '路径沙箱 + 命令白名单 + 正则黑名单，层层安全防护' },
  { icon: <BarChart3 size={24} />, title: '确定性反馈', desc: '基于 exit code 和结构化报告的反馈分析，不依赖 LLM 判断' },
  { icon: <Zap size={24} />, title: '状态机驱动', desc: '纯函数状态转换表，确定性路由，零 LLM 参与决策' },
  { icon: <KeyRound size={24} />, title: '凭证加密', desc: 'OS Keyring（桌面）+ AES-GCM（Docker），密钥不落盘' },
  { icon: <Container size={24} />, title: 'Docker 支持', desc: '多阶段构建，Docker + PyInstaller 双分发方案' },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const FeatureGrid: React.FC = () => (
  <motion.div
    className="feature-grid"
    variants={container}
    initial="hidden"
    whileInView="show"
    viewport={{ once: true }}
  >
    {FEATURES.map((f) => (
      <motion.div
        key={f.title}
        className="feature-card"
        variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } }}
        whileHover={{ y: -4, boxShadow: 'var(--glow-card)' }}
      >
        <span className="feature-card__icon">{f.icon}</span>
        <h3 className="feature-card__title">{f.title}</h3>
        <p className="feature-card__desc">{f.desc}</p>
      </motion.div>
    ))}
  </motion.div>
);

export default FeatureGrid;
