import React from 'react';
import React from 'react';
import PageTransition from '../components/PageTransition';
import HeroSection from '../components/HeroSection';
import CardGrid from '../components/CardGrid';
import GitHubCommunity from '../components/GitHubCommunity';
import DemoChat from '../components/DemoChat';
import { motion } from 'framer-motion';
import { Wand2, Sparkles, Zap } from 'lucide-react';
import '../styles/home.css';

const HomePage: React.FC = () => (
  <PageTransition>
    <HeroSection />

    {/* Demo section — two columns */}
    <section className="demo-section" id="demo">
      <motion.div
        className="demo-section__left"
        initial={{ opacity: 0, x: -30 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="demo-section__heading">代码咒语，即刻施放</h2>
        <p className="demo-section__sub">
          无需复杂的配置，Glimmer 将你的自然语言直接转化为可运行的代码。
        </p>
        <ul className="demo-section__features">
          <li>
            <Wand2 size={16} /> 支持多模型 — Anthropic / OpenAI 自由切换
          </li>
          <li>
            <Sparkles size={16} /> 实时流式输出 — Token by token, 所见即所得
          </li>
          <li>
            <Zap size={16} /> 自我修正 — 自动检测错误并重新生成
          </li>
        </ul>
      </motion.div>

      <motion.div
        className="demo-section__right"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <DemoChat />
      </motion.div>
    </section>

    <CardGrid />
    <GitHubCommunity />
  </PageTransition>
);

export default HomePage;
