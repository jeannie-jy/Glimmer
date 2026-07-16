import React, { useEffect, useRef } from 'react';
import { motion, useMotionValue } from 'framer-motion';

const ORBIT_RX = 180;
const ORBIT_RY = 40;
const ORBIT_PERIOD = 8;

const FairySprite: React.FC = () => {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const timeRef = useRef(0);

  useEffect(() => {
    let animId: number;
    const start = performance.now();
    const loop = (now: number) => {
      const t = ((now - start) / 1000) % ORBIT_PERIOD;
      const angle = (t / ORBIT_PERIOD) * Math.PI * 2;
      x.set(Math.cos(angle) * ORBIT_RX);
      y.set(Math.sin(angle) * ORBIT_RY + Math.sin(t * 2.5) * 6);
      timeRef.current = t;

      if (Math.abs(t % 7) < 0.05 && Math.random() < 0.3) {
        const titleEl = document.querySelector('.hero__title');
        if (titleEl) {
          const r = titleEl.getBoundingClientRect();
          window.dispatchEvent(new CustomEvent('fairy:burst', {
            detail: { x: r.left + r.width / 2 + Math.cos(angle) * ORBIT_RX, y: r.top + r.height / 2 + Math.sin(angle) * ORBIT_RY - 10 }
          }));
        }
      }
      if (Math.abs(t % 6) < 0.05) {
        window.dispatchEvent(new CustomEvent('fairy:sweep'));
      }

      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [x, y]);

  return (
    <motion.div className="fairy-sprite" style={{ x, y, position: 'relative' }} aria-hidden="true">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <ellipse cx="16" cy="20" rx="10" ry="5" fill="rgba(248,164,200,0.4)" transform="rotate(-25 16 20)" />
        <ellipse cx="32" cy="20" rx="10" ry="5" fill="rgba(255,214,232,0.4)" transform="rotate(25 32 20)" />
        <circle cx="24" cy="26" r="2.5" fill="rgba(255,255,255,0.9)" />
        <circle cx="24" cy="26" r="10" fill="rgba(248,164,200,0.2)" />
        <line x1="30" y1="22" x2="42" y2="12" stroke="#f8a4c8" strokeWidth="1.2" strokeLinecap="round" />
        <circle cx="42" cy="12" r="2.5" fill="#ffd6e8" className="wand-tip" />
      </svg>
    </motion.div>
  );
};

export default FairySprite;
