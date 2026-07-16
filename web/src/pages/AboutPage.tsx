import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import FeatureGrid from '../components/FeatureGrid';
import '../styles/about.css';
import { Wand2 } from 'lucide-react';

const TECH = ['Python 3.12+', 'FastAPI', 'React 18', 'TypeScript', 'WebSocket', 'pytest', 'Docker', 'PyInstaller'];

const AboutPage: React.FC = () => (
  <PageTransition>
    <div className="about-page">
      <motion.h1 className="about-page__heading" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
        <Wand2 size={24} /> 什么是 Lite Agent Harness？
      </motion.h1>
      <motion.p className="about-page__intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.15 }}>
        一个轻量级、模型无关的编程 Agent 框架，将 AI 代码生成抽象为"魔法咒语"的执行过程。
        从状态机驱动到三层护栏，从确定性反馈到安全凭证存储——每个环节都经过精心设计，
        让你在本地安全、可控地运行 AI 编码助手。
      </motion.p>
      <FeatureGrid />
      <motion.div className="about-page__tech" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
        <h2 className="about-page__tech-title">技术栈</h2>
        <div className="about-page__tech-stack">
          {TECH.map((t) => (<span key={t} className="about-page__tech-tag">{t}</span>))}
        </div>
        <p className="about-page__footer">MIT License · © 2026 Jingyu Wang</p>
      </motion.div>
    </div>
  </PageTransition>
);

export default AboutPage;
