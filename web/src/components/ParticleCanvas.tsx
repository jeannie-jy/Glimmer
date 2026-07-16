import React, { useRef, useEffect, useCallback } from 'react';

interface Particle {
  x: number; y: number; size: number; speedX: number; speedY: number;
  opacity: number; phase: number; life: number; maxLife: number;
  group: 'background' | 'sweep' | 'burst' | 'afterglow';
}

const BG_COUNT = 55;
const SWEEP_COUNT = 40;
const SWEEP_DURATION = 90;
const SWEEP_INTERVAL = 360;
const BURST_COUNT = 15;

function bgParticle(w: number, h: number): Particle {
  return {
    x: Math.random() * w, y: Math.random() * h,
    size: Math.random() * 0.7 + 0.3,
    speedX: (Math.random() - 0.5) * 0.2,
    speedY: -(Math.random() * 0.3 + 0.1),
    opacity: Math.random() * 0.4 + 0.1,
    phase: Math.random() * Math.PI * 2,
    life: 0, maxLife: Infinity,
    group: 'background',
  };
}

function sweepParticle(startX: number, startY: number): Particle {
  return {
    x: startX + (Math.random() - 0.5) * 60,
    y: startY + (Math.random() - 0.5) * 40,
    size: Math.random() * 1.2 + 0.3,
    speedX: 2 + Math.random() * 3,
    speedY: (Math.random() - 0.5) * 1.5,
    opacity: Math.random() * 0.4 + 0.3,
    phase: 0,
    life: 0, maxLife: SWEEP_DURATION + Math.random() * 30,
    group: 'sweep',
  };
}

function burstParticle(x: number, y: number): Particle {
  const angle = Math.random() * Math.PI * 2;
  const speed = Math.random() * 2 + 0.5;
  return {
    x, y,
    size: Math.random() * 1.5 + 0.5,
    speedX: Math.cos(angle) * speed,
    speedY: Math.sin(angle) * speed - 1,
    opacity: Math.random() * 0.6 + 0.3,
    phase: 0,
    life: 0, maxLife: 40 + Math.random() * 20,
    group: 'burst',
  };
}

const ParticleCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const frameRef = useRef(0);
  const reducedRef = useRef(false);

  const resize = useCallback(() => {
    const c = canvasRef.current; if (!c) return;
    c.width = window.innerWidth; c.height = window.innerHeight;
  }, []);

  const initBg = useCallback(() => {
    const c = canvasRef.current; if (!c) return;
    const arr: Particle[] = [];
    for (let i = 0; i < BG_COUNT; i++) arr.push(bgParticle(c.width, c.height));
    particlesRef.current = arr;
  }, []);

  useEffect(() => {
    const onBurst = (e: CustomEvent) => {
      const { x, y } = e.detail;
      for (let i = 0; i < BURST_COUNT; i++) particlesRef.current.push(burstParticle(x, y));
    };
    const onSweep = () => {
      const titleEl = document.querySelector('.hero__title');
      if (!titleEl) return;
      const r = titleEl.getBoundingClientRect();
      for (let i = 0; i < SWEEP_COUNT; i++) particlesRef.current.push(sweepParticle(r.left - 40, r.top + r.height / 2));
    };
    window.addEventListener('fairy:burst', onBurst as EventListener);
    window.addEventListener('fairy:sweep', onSweep as EventListener);
    return () => {
      window.removeEventListener('fairy:burst', onBurst as EventListener);
      window.removeEventListener('fairy:sweep', onSweep as EventListener);
    };
  }, []);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedRef.current = mq.matches;
    const h = (e: MediaQueryListEvent) => { reducedRef.current = e.matches; };
    mq.addEventListener('change', h);
    resize(); initBg();
    window.addEventListener('resize', () => { resize(); initBg(); });
    return () => { mq.removeEventListener('change', h); window.removeEventListener('resize', resize); };
  }, [resize, initBg]);

  useEffect(() => {
    if (reducedRef.current) return;
    let animId: number;
    const canvas = canvasRef.current; if (!canvas) return;
    const ctx = canvas.getContext('2d'); if (!ctx) return;

    const loop = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      frameRef.current++;

      if (frameRef.current % SWEEP_INTERVAL === 0) {
        const titleEl = document.querySelector('.hero__title');
        if (titleEl) {
          const r = titleEl.getBoundingClientRect();
          for (let i = 0; i < SWEEP_COUNT; i++) particlesRef.current.push(sweepParticle(r.left - 40, r.top + r.height / 2));
        }
      }

      const particles = particlesRef.current;
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.speedX; p.y += p.speedY; p.life++;

        if (p.group === 'sweep') {
          p.speedY += Math.sin(p.life * 0.1) * 0.05;
          if (p.life > p.maxLife * 0.7) p.opacity -= 0.008;
          if (p.life > p.maxLife * 0.6 && Math.random() < 0.15) {
            particles.push({
              x: p.x, y: p.y, size: p.size * 0.5,
              speedX: (Math.random() - 0.5) * 0.3,
              speedY: -(Math.random() * 0.2),
              opacity: p.opacity * 0.5, phase: 0,
              life: 0, maxLife: 100,
              group: 'afterglow',
            });
          }
        }
        if (p.group === 'burst') { p.opacity -= 0.012; p.speedY += 0.02; }
        if (p.group === 'afterglow') { p.opacity -= 0.005; p.speedY -= 0.01; }
        if (p.group === 'background') {
          p.opacity = 0.1 + Math.sin(frameRef.current * 0.02 + p.phase) * 0.15 + 0.15;
        }

        if (p.opacity <= 0 || p.y < -30 || p.y > height + 30 || p.x < -30 || p.x > width + 30 || (p.group !== 'background' && p.life >= p.maxLife)) {
          particles.splice(i, 1); continue;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        const isBg = p.group === 'background';
        const color = isBg ? (Math.random() < 0.3 ? '#ffffff' : '#ffe4ec') : (p.group === 'burst' ? '#f8a4c8' : '#ffe4ec');
        ctx.fillStyle = color;
        ctx.globalAlpha = Math.max(0, Math.min(1, p.opacity));
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      while (particles.filter(p => p.group === 'background').length < BG_COUNT) {
        particles.push(bgParticle(width, height));
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    const onVis = () => { if (document.hidden) cancelAnimationFrame(animId); else animId = requestAnimationFrame(loop); };
    document.addEventListener('visibilitychange', onVis);
    return () => { cancelAnimationFrame(animId); document.removeEventListener('visibilitychange', onVis); };
  }, []);

  return <canvas ref={canvasRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} aria-hidden="true" />;
};

export default ParticleCanvas;
