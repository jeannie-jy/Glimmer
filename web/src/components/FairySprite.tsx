import React from 'react';
import { motion } from 'framer-motion';

const FairySprite: React.FC = () => (
  <motion.div
    className="fairy-sprite"
    animate={{
      y: [0, -16, -8, -20, 0],
      rotate: [0, 3, -2, 4, 0],
    }}
    transition={{
      duration: 8,
      repeat: Infinity,
      ease: 'easeInOut',
    }}
    aria-hidden="true"
  >
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      <ellipse cx="20" cy="28" rx="14" ry="8" fill="rgba(236, 72, 153, 0.3)" transform="rotate(-30 20 28)" />
      <ellipse cx="44" cy="28" rx="14" ry="8" fill="rgba(139, 92, 246, 0.3)" transform="rotate(30 44 28)" />
      <circle cx="32" cy="32" r="3" fill="rgba(255, 255, 255, 0.9)" />
      <circle cx="32" cy="32" r="12" fill="rgba(236, 72, 153, 0.15)" />
      <circle cx="32" cy="18" r="1" fill="#fbbf24" opacity="0.6" />
      <circle cx="24" cy="22" r="0.8" fill="#fbbf24" opacity="0.4" />
      <circle cx="40" cy="22" r="0.8" fill="#fbbf24" opacity="0.4" />
      <circle cx="32" cy="48" r="0.6" fill="#f59e0b" opacity="0.3" />
    </svg>
  </motion.div>
);

export default FairySprite;
