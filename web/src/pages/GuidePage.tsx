import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import StepTimeline from '../components/StepTimeline';
import '../styles/guide.css';

const GuidePage: React.FC = () => (
  <PageTransition>
    <div className="guide-page">
      <motion.h1 className="guide-page__heading" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
        🧭 使用指南
      </motion.h1>
      <motion.p className="guide-page__intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.15 }}>
        只需四个步骤，在本地启动你的 AI 编程助手。
      </motion.p>
      <StepTimeline />
    </div>
  </PageTransition>
);

export default GuidePage;
