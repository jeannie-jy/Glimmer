import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import ConceptCards from '../components/ConceptCards';
import '../styles/learn.css';
import { GraduationCap } from 'lucide-react';

const LearnPage: React.FC = () => (
  <PageTransition>
    <div className="learn-page">
      <motion.h1 className="learn-page__heading" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
        <GraduationCap size={24} /> 学习入口
      </motion.h1>
      <motion.p className="learn-page__intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.15 }}>
        深入理解 Agent 的魔法原理——从状态机到护栏，从反馈分析到多模型适配。
      </motion.p>
      <ConceptCards />
    </div>
  </PageTransition>
);

export default LearnPage;
