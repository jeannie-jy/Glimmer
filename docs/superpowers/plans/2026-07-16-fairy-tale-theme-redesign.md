# Fairy-Tale Dream Theme — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the entire frontend color palette and animation system with a Western fairy-tale dream aesthetic — pink-white gradients, Great Vibes calligraphic titles, lightweight glitter Canvas particles, fairy orbiting the title, zero purple/zero yellow.

**Architecture:** Single sweep across ~18 files. CSS tokens rebuilt first (index.css), then Canvas particle system rebuilt (tiny dots only), then FairySprite + HeroSection rebuilt (fonts + orbit), then all sub-pages and Agent page pink-ified. No backend changes. No component logic changes.

**Tech Stack:** React 18, TypeScript, Vite 6, react-router-dom v7, framer-motion v11, lucide-react, Canvas 2D

## Global Constraints

- Zero purple (`#8b5cf6` range), zero yellow/gold (`#f59e0b` range) in any CSS or component
- Titles: Great Vibes (Google Fonts), Chinese tagline: Noto Serif SC (Google Fonts), body: Inter
- Canvas particles: only round dots ≤1.5px, no 4-point stars, no fairy silhouettes in canvas
- Peak particle count ≤120, pause on tab hidden, mobile half + no sweep/fairy
- `prefers-reduced-motion`: disable animations
- No WebSocket/backend changes
- No component logic changes — visual only

---

### Task 1: Foundation — Fonts + CSS Tokens

**Files:**
- Modify: `web/index.html` (add Great Vibes + Noto Serif SC fonts)
- Modify: `web/src/index.css` (full replace — pink-white palette)
- Modify: `web/src/styles/magic-animations.css` (replace purple keyframes with pink)

**Interfaces:**
- Produces: All CSS tokens available globally (pink-white `:root` variables)
- Produces: Great Vibes, Noto Serif SC, Inter fonts loaded in `<head>`
- Produces: CSS keyframes use pink glow colors

- [ ] **Step 1: Update web/index.html with new fonts**

Read `web/index.html` first, then overwrite:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lite Agent Harness — Where Code Becomes Magic</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Inter:wght@400;500;600;700&family=Noto+Serif+SC:ital@0;1&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: Full replace web/src/index.css with pink-white palette**

Write `web/src/index.css`:

```css
/* Design System: Fairy-Tale Dream Theme */

:root {
  --color-bg-primary: #fefaf5;
  --color-bg-surface: #ffffff;
  --color-bg-element: #fff0f5;
  --color-bg-elevated: #ffeef2;
  --color-bg-input: #fff5f7;

  --color-accent: #f8a4c8;
  --color-accent-hover: #f595b8;
  --color-glow: #ffd6e8;
  --color-sparkle: #ffe4ec;

  --color-text-primary: #3d2c2c;
  --color-text-secondary: #8c7575;
  --color-text-tertiary: #b8a0a0;

  --color-status-success: #7ecb9a;
  --color-status-error: #e88b8b;
  --color-status-warning: #e8c48b;

  --color-border-base: #f0e6e8;

  --gradient-hero: linear-gradient(180deg, #fefaf5 0%, #fff0f3 40%, #ffeef2 100%);
  --gradient-title: linear-gradient(135deg, #e8879b, #f8a4c8, #d4859e);
  --gradient-fairy: linear-gradient(135deg, #f8a4c8, #ffd6e8);
  --gradient-card-glow: radial-gradient(circle at center, rgba(248,164,200,0.15) 0%, transparent 70%);

  --shadow-sm: 0 1px 3px rgba(61, 44, 44, 0.04);
  --shadow-md: 0 4px 16px rgba(61, 44, 44, 0.06);
  --shadow-lg: 0 12px 40px rgba(61, 44, 44, 0.08);
  --shadow-glow: 0 8px 30px rgba(248, 164, 200, 0.2);

  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-7: 28px; --space-8: 32px;

  --text-xs: 11px; --text-sm: 13px; --text-base: 15px; --text-lg: 18px;
  --text-xl: 22px; --text-2xl: 28px;
  --text-hero: clamp(2.5rem, 6vw, 4.5rem);
  --text-tagline-en: clamp(1.2rem, 2.5vw, 1.8rem);
  --text-tagline-zh: clamp(1rem, 1.5vw, 1.3rem);

  --font-display: 'Great Vibes', cursive;
  --font-tagline: 'Noto Serif SC', serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

  --font-regular: 400; --font-medium: 500; --font-semibold: 600; --font-bold: 700;
  --leading-tight: 1.25; --leading-normal: 1.5; --leading-relaxed: 1.6;

  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 20px; --radius-full: 9999px;

  --magic-float-duration: 8s;
  --magic-sparkle-duration: 2s;
  --magic-sweep-interval: 6s;
  --magic-sweep-duration: 1.5s;
  --magic-breathe: 3s ease-in-out infinite;

  --transition-fast: 150ms;
  --transition-normal: 250ms;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body { height: 100%; }

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#root { height: 100%; }

::-webkit-scrollbar { width: var(--space-2); height: var(--space-2); }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--color-border-base); border-radius: var(--radius-sm); }
::-webkit-scrollbar-thumb:hover { background: var(--color-text-tertiary); }

:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
button:focus:not(:focus-visible) { outline: none; }
::selection { background: var(--color-accent); color: #fff; }
```

- [ ] **Step 3: Replace magic-animations.css with pink-themed keyframes**

Write `web/src/styles/magic-animations.css`:

```css
@keyframes magic-float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-12px) rotate(2deg); }
  66% { transform: translateY(-6px) rotate(-1deg); }
}

@keyframes magic-breathe {
  0%, 100% { opacity: 0.6; box-shadow: 0 0 16px rgba(248,164,200,0.3), 0 0 32px rgba(248,164,200,0.15); }
  50% { opacity: 1; box-shadow: 0 0 24px rgba(248,164,200,0.5), 0 0 48px rgba(248,164,200,0.25); }
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes sparkle-blink {
  0%, 100% { opacity: 0.2; transform: scale(0.7); }
  50% { opacity: 1; transform: scale(1.3); }
}

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes expand-ring {
  0% { box-shadow: 0 0 0 0 rgba(248,164,200,0.4); }
  100% { box-shadow: 0 0 0 12px rgba(248,164,200,0); }
}

@keyframes fairy-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.gradient-text {
  background: var(--gradient-title);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 5s ease infinite;
}

.magic-breathe { animation: magic-breathe var(--magic-breathe); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Removed: `magic-circle`, `magic-float` utility class, `sparkle-blink` utility class (no longer needed for purple theme).

- [ ] **Step 4: Verify build**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --emptyOutDir
```

Expected: Build passes. Pages render with pink-white tokens but may look broken until subsequent tasks.

- [ ] **Step 5: Commit**

```bash
git -C G:/github/lite-agent-harness add web/index.html web/src/index.css web/src/styles/magic-animations.css
git -C G:/github/lite-agent-harness commit -m "feat: fairy-tale foundation — pink-white tokens, Great Vibes + Noto Serif SC fonts"
```

---

### Task 2: Rebuild Canvas Particle System

**Files:**
- Modify: `web/src/components/ParticleCanvas.tsx`

**Interfaces:**
- Consumes: CSS tokens `--color-sparkle`, `--color-accent`, `--color-glow`
- Produces: `<ParticleCanvas />` — renders lightweight round-dot glitter particles, glitter sweep events, fairy wand burst events
- New public method (via ref or window event): `triggerWandBurst(x, y)`, `triggerGlitterSweep()`

- [ ] **Step 1: Write new ParticleCanvas.tsx**

Write `web/src/components/ParticleCanvas.tsx`:

```tsx
import React, { useRef, useEffect, useCallback } from 'react';

interface Particle {
  x: number; y: number; size: number; speedX: number; speedY: number;
  opacity: number; phase: number; life: number; maxLife: number;
  group: 'background' | 'sweep' | 'burst' | 'afterglow';
}

const BG_COUNT = 55;
const SWEEP_COUNT = 40;
const SWEEP_DURATION = 90;   // frames (~1.5s at 60fps)
const SWEEP_INTERVAL = 360;  // frames (~6s at 60fps)
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

function sweepParticle(startX: number, startY: number, w: number): Particle {
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
  const titleRectRef = useRef<DOMRect | null>(null);
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

  // Expose trigger methods via window events
  useEffect(() => {
    const onBurst = (e: CustomEvent) => {
      const { x, y } = e.detail;
      for (let i = 0; i < BURST_COUNT; i++) particlesRef.current.push(burstParticle(x, y));
    };
    const onSweep = () => {
      const titleEl = document.querySelector('.hero__title');
      if (!titleEl) return;
      const r = titleEl.getBoundingClientRect();
      const startY = r.top + r.height / 2;
      for (let i = 0; i < SWEEP_COUNT; i++) particlesRef.current.push(sweepParticle(r.left - 40, startY, window.innerWidth));
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

      // Auto-trigger sweep
      if (frameRef.current % SWEEP_INTERVAL === 0) {
        const titleEl = document.querySelector('.hero__title');
        if (titleEl) {
          const r = titleEl.getBoundingClientRect();
          for (let i = 0; i < SWEEP_COUNT; i++) particlesRef.current.push(sweepParticle(r.left - 40, r.top + r.height / 2, width));
        }
      }

      const particles = particlesRef.current;
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.speedX; p.y += p.speedY; p.life++;

        if (p.group === 'sweep') {
          p.speedY += Math.sin(p.life * 0.1 + p.phase) * 0.05;
          if (p.life > p.maxLife * 0.7) p.opacity -= 0.008;
          // Afterglow
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
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd G:/github/lite-agent-harness/web && npx tsc --noEmit 2>&1 | head -20
```

Expected: No new errors from ParticleCanvas.tsx.

- [ ] **Step 3: Build check**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --emptyOutDir
```

- [ ] **Step 4: Commit**

```bash
git -C G:/github/lite-agent-harness add web/src/components/ParticleCanvas.tsx
git -C G:/github/lite-agent-harness commit -m "feat: rebuild particle canvas — tiny round glitter, sweep, wand burst"
```

---

### Task 3: Rebuild FairySprite + HeroSection

**Files:**
- Modify: `web/src/components/FairySprite.tsx`
- Modify: `web/src/components/HeroSection.tsx`
- Modify: `web/src/styles/home.css` (hero section styles)

**Interfaces:**
- Consumes: CSS tokens `--font-display`, `--font-tagline`, `--gradient-title`
- `<FairySprite>` uses framer-motion elliptical orbit, dispatches `fairy:burst` and `fairy:sweep` events
- `<HeroSection>` renders 3-line title layout with new fonts

- [ ] **Step 1: Write new FairySprite.tsx — elliptical orbit + magic wand**

Write `web/src/components/FairySprite.tsx`:

```tsx
import React, { useEffect, useRef } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';

const ORBIT_RX = 180;
const ORBIT_RY = 40;
const ORBIT_PERIOD = 8;

const FairySprite: React.FC = () => {
  const timeRef = useRef(0);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  useEffect(() => {
    let animId: number;
    const start = performance.now();
    const loop = (now: number) => {
      const t = ((now - start) / 1000) % ORBIT_PERIOD;
      const angle = (t / ORBIT_PERIOD) * Math.PI * 2;
      x.set(Math.cos(angle) * ORBIT_RX);
      y.set(Math.sin(angle) * ORBIT_RY + Math.sin(t * 2.5) * 6);
      timeRef.current = t;

      // Trigger wand burst every ~7s
      if (Math.abs(t % 7) < 0.05 && Math.random() < 0.3) {
        const titleEl = document.querySelector('.hero__title');
        if (titleEl) {
          const r = titleEl.getBoundingClientRect();
          const cx = r.left + r.width / 2 + Math.cos(angle) * ORBIT_RX;
          const cy = r.top + r.height / 2 + Math.sin(angle) * ORBIT_RY;
          window.dispatchEvent(new CustomEvent('fairy:burst', { detail: { x: cx, y: cy - 10 } }));
        }
      }
      // Trigger sweep every ~6s at a specific point in orbit
      if (Math.abs(t % 6) < 0.05) {
        window.dispatchEvent(new CustomEvent('fairy:sweep'));
      }

      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [x, y]);

  return (
    <motion.div
      className="fairy-sprite"
      style={{ x, y, position: 'relative' }}
      aria-hidden="true"
    >
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        {/* Wings */}
        <ellipse cx="16" cy="20" rx="10" ry="5" fill="rgba(248,164,200,0.4)" transform="rotate(-25 16 20)" />
        <ellipse cx="32" cy="20" rx="10" ry="5" fill="rgba(255,214,232,0.4)" transform="rotate(25 32 20)" />
        {/* Body */}
        <circle cx="24" cy="26" r="2.5" fill="rgba(255,255,255,0.9)" />
        {/* Glow */}
        <circle cx="24" cy="26" r="10" fill="rgba(248,164,200,0.2)" />
        {/* Magic wand */}
        <line x1="30" y1="22" x2="42" y2="12" stroke="#f8a4c8" strokeWidth="1.2" strokeLinecap="round" />
        {/* Wand tip star */}
        <circle cx="42" cy="12" r="2.5" fill="#ffd6e8" className="wand-tip" />
      </svg>
    </motion.div>
  );
};

export default FairySprite;
```

- [ ] **Step 2: Add wand-tip CSS animation to home.css**

Append to `web/src/styles/home.css`:

```css
.wand-tip {
  animation: sparkle-blink 2s ease-in-out infinite;
}
```

- [ ] **Step 3: Write new HeroSection.tsx — 3-line layout**

Write `web/src/components/HeroSection.tsx`:

```tsx
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
```

- [ ] **Step 4: Update home.css hero styles for new fonts**

Replace hero-related CSS in `web/src/styles/home.css`:

Read the current file first, then replace the hero section styles. The key new styles:

```css
.hero__fairy-orbit {
  position: relative;
  width: 100%;
  height: 60px;
  margin-bottom: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero__title {
  font-family: var(--font-display);
  font-size: var(--text-hero);
  font-weight: 400;
  line-height: 1.2;
  margin-bottom: var(--space-2);
  text-shadow: 0 2px 20px rgba(248, 164, 200, 0.3);
}

.hero__subtitle {
  font-family: var(--font-display);
  font-size: var(--text-tagline-en);
  font-weight: 400;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.hero__tagline {
  font-family: var(--font-tagline);
  font-size: var(--text-tagline-zh);
  font-weight: 400;
  font-style: italic;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-6);
}
```

The full file should replace all previous hero-related rules with the pink palette versions. Also update `.hero__btn--primary` to use `--color-accent` instead of gradient, and remove `--gradient-magic-primary` references.

- [ ] **Step 5: Build + verify**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --emptyOutDir
```

- [ ] **Step 6: Commit**

```bash
git -C G:/github/lite-agent-harness add web/src/components/FairySprite.tsx web/src/components/HeroSection.tsx web/src/styles/home.css
git -C G:/github/lite-agent-harness commit -m "feat: rebuild FairySprite (orbit + wand) and HeroSection (calligraphic titles)"
```

---

### Task 4: Pink-ify NavBar + Cards + GitHub Section

**Files:**
- Modify: `web/src/styles/nav.css`
- Modify: `web/src/components/NavBar.tsx` (logo gradient)
- Modify: `web/src/components/CardGrid.tsx` (Lucide icons, pink)
- Modify: `web/src/components/MagicCard.tsx` (pink styling)
- Modify: `web/src/components/GitHubCommunity.tsx` (pink buttons)
- Modify: `web/src/styles/home.css` (card + github section pink styles)

**Key changes:**
- NavBar: `rgba(254,250,245,0.85)` background, pink gradient logo text (`--gradient-title`), gold underline → pink underline
- Magic cards: `border-radius: 20px`, `--gradient-card-glow` on hover, `--shadow-glow`, Lucide pink icons
- GitHub: pink gradient primary button, simplified layout

- [ ] **Step 1: Update nav.css — pink palette**

Replace all color references in `web/src/styles/nav.css`:
- `.nav`: `background: rgba(254,250,245,0.85)` (was `rgba(255,255,255,0.8)`)
- `.nav__logo-text`: use `--gradient-title` (was `--gradient-magic-primary`)
- `.nav__link--active::after`: use `--color-accent` and `--shadow-glow` (was `--gradient-magic-gold` and `--glow-gold`)
- `.nav__github-btn:hover`: use `--color-accent` border + `--shadow-glow`

- [ ] **Step 2: Update home.css — cards + GitHub section pink**

Replace color references in card/github styles:
- `.magic-card::before`: use `--gradient-card-glow`
- `.magic-card:hover`: `border-color: var(--color-accent)`, `box-shadow: var(--shadow-glow)`
- `.magic-card__cta`: `color: var(--color-accent)`
- `.github-community__btn--primary`: `background: var(--gradient-fairy)`
- `.github-community__bg`: pink gradient from `--gradient-hero`

- [ ] **Step 3: Update GitHubCommunity.tsx — use pink-themed icons**

Update Lucide icon colors to `color="var(--color-accent)"` or via className.

- [ ] **Step 4: Build + commit**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --emptyOutDir
git -C G:/github/lite-agent-harness add web/src/styles/nav.css web/src/styles/home.css web/src/components/NavBar.tsx web/src/components/GitHubCommunity.tsx web/src/components/MagicCard.tsx web/src/components/CardGrid.tsx
git -C G:/github/lite-agent-harness commit -m "feat: pink-ify NavBar, cards, GitHub section"
```

---

### Task 5: Pink-ify Sub-Pages (About, Guide, Learn)

**Files:**
- Modify: `web/src/styles/about.css`
- Modify: `web/src/styles/guide.css`
- Modify: `web/src/styles/learn.css`
- Modify: `web/src/components/FeatureGrid.tsx` (icons)
- Modify: `web/src/components/StepTimeline.tsx` (code block bg, bubble colors)
- Modify: `web/src/components/ConceptCards.tsx` (icons)

**Key changes:**
- All accent references: `--color-accent-primary` → `--color-accent`
- All glow references: `--glow-magic` → `--shadow-glow`
- Feature cards: pink border on hover, Lucide pink icons
- Step bubble: `--color-accent` fill when active (was purple)
- Code blocks: `background: #fdf6f8`, `color: #3d2c2c` (was dark purple)
- Concept card open: `border-color: var(--color-accent)`

- [ ] **Step 1: Replace all CSS color references in about.css, guide.css, learn.css**

Search and replace patterns:
- `var(--color-accent-primary)` → `var(--color-accent)`
- `var(--glow-magic)` → `var(--shadow-glow)`
- `var(--gradient-magic-gold)` → `var(--gradient-fairy)` (gold underline → pink underline)
- `#1e1b2e` (dark code bg) → `#fdf6f8` (warm pink-white code bg)
- `#c4b5fd` (purple code text) → `#3d2c2c` (warm brown code text)

- [ ] **Step 2: Update StepTimeline.tsx code block**

Change `.step-item__code` styling: light pink background, dark brown text.

- [ ] **Step 3: Build + commit**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --emptyOutDir
git -C G:/github/lite-agent-harness add web/src/styles/about.css web/src/styles/guide.css web/src/styles/learn.css web/src/components/FeatureGrid.tsx web/src/components/StepTimeline.tsx web/src/components/ConceptCards.tsx web/src/pages/AboutPage.tsx web/src/pages/GuidePage.tsx web/src/pages/LearnPage.tsx
git -C G:/github/lite-agent-harness commit -m "feat: pink-ify About, Guide, Learn pages"
```

---

### Task 6: Pink-ify Agent Page

**Files:**
- Modify: `web/src/styles/agent.css`
- Modify: `web/src/components/ChatView.tsx` (header text)
- Modify: `web/src/components/StateIndicator.tsx` (orb colors)

**Key changes:**
- Sidebar bg: `--color-bg-element` (`#fff0f5`)
- Send button: `--color-accent` gradient
- Crystal ball orbs: pink glow instead of purple
- Input focus: pink expand-ring
- Guardrail modal: pink border
- ChatView title: "Agent — 代码魔法" → keep with Wand2 icon but pink

- [ ] **Step 1: Replace all CSS color references in agent.css**

Search/replace:
- `var(--color-accent-primary)` → `var(--color-accent)`
- `var(--glow-magic)` → `var(--shadow-glow)`
- `var(--gradient-magic-primary)` → `var(--gradient-fairy)`
- `var(--color-bg-element)` is already `#fff0f5` in new tokens, works
- State orb colors: planning → `var(--color-accent)` with pink glow, correcting → pink glow

- [ ] **Step 2: Update StateIndicator.tsx orbs**

The `.state-indicator__orb--planning` uses `var(--color-accent-primary)` and `--glow-magic` — change to `var(--color-accent)` and `--shadow-glow`. Same for other states currently using purple.

- [ ] **Step 3: Build + commit**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --emptyOutDir
git -C G:/github/lite-agent-harness add web/src/styles/agent.css web/src/components/ChatView.tsx web/src/components/StateIndicator.tsx web/src/pages/AgentPage.tsx
git -C G:/github/lite-agent-harness commit -m "feat: pink-ify Agent chat page"
```

---

### Task 7: Final Polish — Build + Verify

**Files:**
- Verify: `server/static/` (production build output)
- Modify: `DESIGN.md` (already done — skip)

- [ ] **Step 1: Build production assets to server/static**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --outDir ../server/static --emptyOutDir
```

Expected: Clean build, zero errors.

- [ ] **Step 2: Verify no purple/yellow remains in CSS output**

```bash
grep -rE '#8b5cf6|#7c3aed|#6d28d9|#f59e0b|#fbbf24|--color-accent-primary|--color-accent-gold|--glow-magic|--glow-gold|--gradient-magic-primary|--gradient-magic-gold' G:/github/lite-agent-harness/web/src/
```

Expected: Zero matches (or only in comments/docs).

- [ ] **Step 3: Start server and verify visually**

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Open browser, check:
- Home: Great Vibes title, fairy orbiting, pink glitter, 3-line layout
- About: pink cards, pink underline
- Guide: pink steps, light code blocks
- Learn: pink concept cards
- Agent: pink chat bubbles, pink send button
- Nav: pink active underline, pink gradient logo

- [ ] **Step 4: Commit**

```bash
git -C G:/github/lite-agent-harness add server/static/
git -C G:/github/lite-agent-harness commit -m "feat: build production assets, final pink verification pass"
```
