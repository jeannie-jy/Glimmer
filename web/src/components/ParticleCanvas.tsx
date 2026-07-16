import React, { useRef, useEffect, useCallback } from 'react';

interface Particle {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  opacity: number;
  opacityDir: number;
  type: 'dust' | 'sparkle' | 'fairy';
  phase: number;
  life: number;
  maxLife: number;
}

const PARTICLE_COUNT = 80;
const FAIRY_CHANCE = 0.003;

function createParticle(canvasW: number, canvasH: number): Particle {
  const type: Particle['type'] =
    Math.random() < FAIRY_CHANCE ? 'fairy'
    : Math.random() < 0.3 ? 'sparkle'
    : 'dust';

  const base = {
    x: Math.random() * canvasW,
    y: Math.random() * canvasH,
    opacity: Math.random() * 0.5 + 0.2,
    opacityDir: Math.random() > 0.5 ? 1 : -1,
    phase: Math.random() * Math.PI * 2,
  };

  switch (type) {
    case 'dust':
      return { ...base, type: 'dust', size: Math.random() * 1.5 + 0.5, speedX: (Math.random() - 0.5) * 0.3, speedY: -(Math.random() * 0.4 + 0.1), life: 0, maxLife: Infinity };
    case 'sparkle':
      return { ...base, type: 'sparkle', size: Math.random() * 2 + 1, speedX: (Math.random() - 0.5) * 0.5, speedY: -(Math.random() * 0.6 + 0.15), life: 0, maxLife: Infinity };
    case 'fairy':
      return { ...base, type: 'fairy', size: Math.random() * 10 + 20, speedX: (Math.random() - 0.5) * 1.5, speedY: -(Math.random() * 0.3 + 0.05), opacity: 0, opacityDir: 1, life: 0, maxLife: 400 + Math.random() * 200 };
  }
}

function drawSparkle(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, opacity: number) {
  ctx.save();
  ctx.translate(x, y);
  ctx.globalAlpha = opacity;
  ctx.fillStyle = '#fbbf24';
  ctx.beginPath();
  for (let i = 0; i < 4; i++) {
    const angle = (i * Math.PI) / 2;
    const outerX = Math.cos(angle) * size;
    const outerY = Math.sin(angle) * size;
    const innerX = Math.cos(angle + Math.PI / 4) * (size * 0.35);
    const innerY = Math.sin(angle + Math.PI / 4) * (size * 0.35);
    if (i === 0) ctx.moveTo(outerX, outerY);
    else ctx.lineTo(outerX, outerY);
    ctx.lineTo(innerX, innerY);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawFairy(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, opacity: number, phase: number) {
  ctx.save();
  ctx.globalAlpha = opacity * 0.5;
  const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 1.5);
  gradient.addColorStop(0, 'rgba(236, 72, 153, 0.6)');
  gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.3)');
  gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(x, y, size * 1.5, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
  ctx.beginPath();
  ctx.ellipse(x - size * 0.6, y - size * 0.2, size * 0.4, size * 0.25, -0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(x + size * 0.6, y - size * 0.2, size * 0.4, size * 0.25, 0.4, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
  ctx.beginPath();
  ctx.arc(x, y, size * 0.15, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

const ParticleCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const cursorRef = useRef<{ x: number; y: number } | null>(null);
  const reducedRef = useRef(false);

  const resize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }, []);

  const initParticles = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const isMobile = window.innerWidth < 768;
    const count = isMobile ? 30 : PARTICLE_COUNT;
    const arr: Particle[] = [];
    for (let i = 0; i < count; i++) {
      arr.push(createParticle(canvas.width, canvas.height));
    }
    particlesRef.current = arr;
  }, []);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedRef.current = mq.matches;
    const handleChange = (e: MediaQueryListEvent) => { reducedRef.current = e.matches; };
    mq.addEventListener('change', handleChange);
    resize();
    initParticles();
    window.addEventListener('resize', () => { resize(); initParticles(); });
    return () => {
      mq.removeEventListener('change', handleChange);
      window.removeEventListener('resize', resize);
    };
  }, [resize, initParticles]);

  useEffect(() => {
    const isMobile = window.innerWidth < 768;
    if (isMobile) return;
    const onMove = (e: MouseEvent) => { cursorRef.current = { x: e.clientX, y: e.clientY }; };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  useEffect(() => {
    if (reducedRef.current) return;
    let animId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const loop = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      const cp = cursorRef.current;
      if (cp) {
        for (let i = 0; i < 2; i++) {
          ctx.beginPath();
          ctx.arc(cp.x + (Math.random() - 0.5) * 20, cp.y + (Math.random() - 0.5) * 20, Math.random() * 2 + 0.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(139, 92, 246, ${Math.random() * 0.3 + 0.1})`;
          ctx.fill();
        }
      }

      const particles = particlesRef.current;
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.speedX + Math.sin(p.phase + performance.now() * 0.001) * 0.3;
        p.y += p.speedY;
        p.phase += 0.02;
        p.life++;

        if (p.type === 'sparkle') {
          p.opacity += p.opacityDir * 0.008;
          if (p.opacity >= 0.6) p.opacityDir = -1;
          if (p.opacity <= 0.1) p.opacityDir = 1;
        }

        if (p.type === 'fairy') {
          if (p.life < 60) p.opacity = Math.min(p.opacity + 0.008, 0.5);
          if (p.life > p.maxLife - 60) p.opacity = Math.max(p.opacity - 0.008, 0);
        }

        if ((p.type === 'fairy' && p.life >= p.maxLife) || p.y < -50 || p.y > height + 50 || p.x < -50 || p.x > width + 50) {
          particles.splice(i, 1);
          continue;
        }

        switch (p.type) {
          case 'dust':
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(196, 181, 253, ${p.opacity})`;
            ctx.fill();
            break;
          case 'sparkle':
            drawSparkle(ctx, p.x, p.y, p.size, p.opacity);
            break;
          case 'fairy':
            drawFairy(ctx, p.x, p.y, p.size, p.opacity, p.phase);
            break;
        }
      }

      while (particles.length < PARTICLE_COUNT) {
        particles.push(createParticle(width, height));
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    const onVisibility = () => {
      if (document.hidden) cancelAnimationFrame(animId);
      else animId = requestAnimationFrame(loop);
    };
    document.addEventListener('visibilitychange', onVisibility);

    return () => {
      cancelAnimationFrame(animId);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }}
      aria-hidden="true"
    />
  );
};

export default ParticleCanvas;
