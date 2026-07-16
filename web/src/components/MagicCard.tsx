import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

interface MagicCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  to: string;
}

const MagicCard: React.FC<MagicCardProps> = ({ icon, title, description, to }) => {
  const navigate = useNavigate();

  return (
    <motion.div
      className="magic-card"
      whileHover={{ y: -8, boxShadow: 'var(--glow-card)' }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      onClick={() => navigate(to)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && navigate(to)}
    >
      <motion.span
        className="magic-card__icon"
        whileHover={{ scale: 1.15, rotate: [0, -5, 5, 0] }}
        transition={{ duration: 0.4 }}
      >
        {icon}
      </motion.span>
      <h3 className="magic-card__title">{title}</h3>
      <p className="magic-card__desc">{description}</p>
      <span className="magic-card__cta">探索 →</span>
    </motion.div>
  );
};

export default MagicCard;
