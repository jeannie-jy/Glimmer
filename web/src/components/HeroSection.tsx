import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, BookOpen, ChevronDown } from 'lucide-react';
import FairySprite from './FairySprite';

const HeroSection: React.FC = () => {
  const navigate = useNavigate();
  const scrollToCards = () => document.getElementById('magic-cards')?.scrollIntoView({ behavior: 'smooth' });

  return (
    <section className="hero">
      <div className="hero__bg" />
      <div className="hero__content">
        <div className="hero__fairy-orbit">
          <FairySprite />
        </div>

        <motion.h1
          className="hero__title gradient-text"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        >
          Lite Agent Harness
        </motion.h1>

        <motion.p
          className="hero__subtitle"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        >
          Where Code Becomes Magic
        </motion.p>

        <motion.p
          className="hero__tagline"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
        >
          每一次编码，都是一场施法
        </motion.p>

        <motion.div
          className="hero__actions"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <button className="hero__btn hero__btn--primary" onClick={() => navigate('/agent')}>
            <Sparkles size={18} /> 开始施法
          </button>
          <button className="hero__btn hero__btn--secondary" onClick={scrollToCards}>
            <BookOpen size={18} /> 了解更多
          </button>
        </motion.div>
      </div>

      <motion.button
        className="hero__scroll-hint"
        onClick={scrollToCards}
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
        aria-label="Scroll to learn more"
        type="button"
      >
        <ChevronDown size={24} />
      </motion.button>
    </section>
  );
};

export default HeroSection;
