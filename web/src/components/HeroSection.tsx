import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import FairySprite from './FairySprite';

const HeroSection: React.FC = () => {
  const navigate = useNavigate();

  const scrollToCards = () => {
    document.getElementById('magic-cards')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="hero">
      <div className="hero__bg" />
      <div className="hero__content">
        <FairySprite />

        <motion.h1
          className="hero__title gradient-text"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          Lite Agent Harness
        </motion.h1>

        <motion.p
          className="hero__subtitle"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        >
          Where Code Becomes Magic
        </motion.p>

        <motion.p
          className="hero__tagline"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          将每一次代码生成，化作魔法咒语
        </motion.p>

        <motion.p
          className="hero__desc"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          轻量、模型无关的 AI 编程助手框架
        </motion.p>

        <motion.div
          className="hero__actions"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <button className="hero__btn hero__btn--primary" onClick={() => navigate('/agent')}>
            <span className="hero__btn-icon">✨</span> 开始施法
          </button>
          <button className="hero__btn hero__btn--secondary" onClick={scrollToCards}>
            <span className="hero__btn-icon">📖</span> 了解更多
          </button>
        </motion.div>
      </div>

      <motion.div
        className="hero__scroll-hint"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        ↓
      </motion.div>
    </section>
  );
};

export default HeroSection;
