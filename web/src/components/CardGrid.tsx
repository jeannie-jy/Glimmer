import React from 'react';
import { motion } from 'framer-motion';
import MagicCard from './MagicCard';
import { Wand2, ScrollText, GraduationCap } from 'lucide-react';

const CARDS = [
  { icon: <Wand2 size={32} />, title: '项目简介', description: '了解 Lite Agent Harness 的核心魔法', to: '/about' },
  { icon: <ScrollText size={32} />, title: '使用指南', description: '施展你的第一个代码咒语', to: '/guide' },
  { icon: <GraduationCap size={32} />, title: '学习入口', description: '深入理解 Agent 的魔法原理', to: '/learn' },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};

const CardGrid: React.FC = () => (
  <motion.div
    id="magic-cards"
    className="card-grid"
    variants={container}
    initial="hidden"
    whileInView="show"
    viewport={{ once: true, margin: '-100px' }}
  >
    {CARDS.map((card) => (
      <motion.div
        key={card.to}
        variants={{
          hidden: { opacity: 0, y: 40 },
          show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
        }}
      >
        <MagicCard {...card} />
      </motion.div>
    ))}
  </motion.div>
);

export default CardGrid;
