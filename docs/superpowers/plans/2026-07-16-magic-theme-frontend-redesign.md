# Magic Theme Frontend Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dark Linear-themed frontend with a light, dreamy "Magic" theme — multi-page React Router architecture, framer-motion animations, Canvas particle system, fairy/glitter aesthetic.

**Architecture:** React Router v7 for 5-page SPA routing. Global `ParticleCanvas` (Canvas 2D) renders background particles. `NavBar` is fixed across all pages. Each page wrapped in `PageTransition` (framer-motion `AnimatePresence`). Existing chat components moved into `/agent` route with reskinned CSS. All CSS tokens replaced from dark Linear → light magic theme per `DESIGN.md`.

**Tech Stack:** React 18, TypeScript, Vite 6, react-router-dom v7, framer-motion v11, Canvas 2D (no library), CSS Custom Properties

## Global Constraints

- No breaking changes to WebSocket protocol or Python backend
- CSS tokens fully replaced: dark → light magic theme (exact values in `DESIGN.md`)
- Existing component logic kept — visual changes only
- `prefers-reduced-motion`: disable animations, reduce particles
- Canvas particles: ≤100, pause on tab hidden, reduce on mobile
- No new dependencies beyond react-router-dom and framer-motion

---

### Task 1: Foundation — Dependencies, Router, CSS Tokens

**Files:**
- Modify: `web/package.json`
- Modify: `web/src/main.tsx`
- Modify: `web/src/index.css` (full replace)
- Create: `web/src/styles/magic-animations.css`

**Interfaces:**
- Produces: CSS tokens available globally (`:root` variables in `index.css`)
- Produces: `<BrowserRouter>` wrapping `<App />` in `main.tsx`
- Produces: `package.json` with react-router-dom ^7, framer-motion ^11

- [ ] **Step 1: Install new dependencies**

```bash
cd web && npm install react-router-dom@^7 framer-motion@^11
```

- [ ] **Step 2: Verify package.json has new dependencies**

Run: `node -e "const p=require('./web/package.json'); console.log(p.dependencies['react-router-dom'], p.dependencies['framer-motion'])"`

- [ ] **Step 3: Replace index.css with magic light theme tokens**

Write `web/src/index.css`:

```css
/* Design System: Magic Dream Theme
   Light, dreamy, fairy-tale aesthetic */

/* =========================================================================
   Design Tokens — Backgrounds (Light)
   ========================================================================= */

:root {
  --color-bg-primary: #faf5ff;
  --color-bg-surface: #ffffff;
  --color-bg-element: #f3e8ff;
  --color-bg-elevated: #ede9fe;
  --color-bg-input: #f8f0ff;

  /* ---- Accent Colors ---- */
  --color-accent-primary: #8b5cf6;
  --color-accent-hover: #7c3aed;
  --color-accent-gold: #f59e0b;
  --color-accent-gold-light: #fbbf24;
  --color-accent-pink: #ec4899;
  --color-accent-cyan: #06b6d4;

  /* ---- Text Colors ---- */
  --color-text-primary: #1e1b4b;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;

  /* ---- Status Colors ---- */
  --color-status-success: #10b981;
  --color-status-error: #ef4444;
  --color-status-warning: #f59e0b;

  /* ---- Borders ---- */
  --color-border-base: #e5e0f0;
  --color-border-muted: #f0ebf8;

  /* ---- Gradients ---- */
  --gradient-hero: linear-gradient(180deg, #faf5ff 0%, #ede9fe 50%, #e0e7ff 100%);
  --gradient-magic-primary: linear-gradient(135deg, #8b5cf6, #6d28d9, #3b82f6);
  --gradient-magic-fairy: linear-gradient(135deg, #ec4899, #8b5cf6, #06b6d4);
  --gradient-magic-text: linear-gradient(135deg, #8b5cf6, #ec4899, #f59e0b);
  --gradient-magic-gold: linear-gradient(135deg, #f59e0b, #fbbf24);

  /* ---- Glow Effects ---- */
  --glow-magic: 0 0 20px rgba(139, 92, 246, 0.3), 0 0 40px rgba(139, 92, 246, 0.15);
  --glow-gold: 0 0 20px rgba(245, 158, 11, 0.3), 0 0 40px rgba(245, 158, 11, 0.15);
  --glow-card: 0 0 30px rgba(139, 92, 246, 0.1), 0 8px 32px rgba(139, 92, 246, 0.08);

  /* ---- Spacing (4px scale) ---- */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-7: 28px;
  --space-8: 32px;

  /* ---- Typography ---- */
  --text-xs: 11px;
  --text-sm: 13px;
  --text-base: 15px;
  --text-lg: 18px;
  --text-xl: 22px;
  --text-2xl: 28px;
  --text-hero: clamp(2.5rem, 6vw, 4.5rem);

  --font-regular: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.6;

  /* ---- Radii ---- */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* ---- Shadows ---- */
  --shadow-sm: 0 1px 3px rgba(139, 92, 246, 0.08);
  --shadow-md: 0 4px 16px rgba(139, 92, 246, 0.1);
  --shadow-lg: 0 12px 40px rgba(139, 92, 246, 0.12);

  /* ---- Magic Animation Timings ---- */
  --magic-float-duration: 6s;
  --magic-sparkle-duration: 2s;
  --magic-transition: 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  --magic-breathe: 3s ease-in-out infinite;

  /* ---- Transitions ---- */
  --transition-fast: 150ms;
  --transition-normal: 250ms;
}

/* =========================================================================
   Reset
   ========================================================================= */

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
    Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#root {
  height: 100%;
}

/* =========================================================================
   Scrollbar (light theme)
   ========================================================================= */

::-webkit-scrollbar {
  width: var(--space-2);
  height: var(--space-2);
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border-base);
  border-radius: var(--radius-sm);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

/* =========================================================================
   Focus visible
   ========================================================================= */

:focus-visible {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
}

button:focus:not(:focus-visible) {
  outline: none;
}

/* =========================================================================
   Selection
   ========================================================================= */

::selection {
  background: var(--color-accent-primary);
  color: #fff;
}
```

- [ ] **Step 4: Create magic-animations.css with CSS keyframes**

Write `web/src/styles/magic-animations.css`:

```css
/* =========================================================================
   Magic CSS Keyframe Animations
   ========================================================================= */

/* Floating (for fairy sprites, decorative elements) */
@keyframes magic-float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-12px) rotate(2deg); }
  66% { transform: translateY(-6px) rotate(-1deg); }
}

/* Breathing glow pulse */
@keyframes magic-breathe {
  0%, 100% { opacity: 0.6; box-shadow: var(--glow-magic); }
  50% { opacity: 1; box-shadow: 0 0 30px rgba(139, 92, 246, 0.5), 0 0 60px rgba(139, 92, 246, 0.25); }
}

/* Gradient text shift */
@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* Sparkle blink */
@keyframes sparkle-blink {
  0%, 100% { opacity: 0.2; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* Magic circle rotate (for button hover effect) */
@keyframes magic-circle {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Fade in up */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Expanding ring */
@keyframes expand-ring {
  0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
  100% { box-shadow: 0 0 0 12px rgba(139, 92, 246, 0); }
}

/* =========================================================================
   Utility classes
   ========================================================================= */

.magic-float {
  animation: magic-float var(--magic-float-duration) ease-in-out infinite;
}

.magic-breathe {
  animation: magic-breathe var(--magic-breathe);
}

.gradient-text {
  background: var(--gradient-magic-text);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 4s ease infinite;
}

/* =========================================================================
   Reduced motion
   ========================================================================= */

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 5: Wrap App with BrowserRouter in main.tsx**

Write `web/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('Root element #root not found');

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
```

- [ ] **Step 6: Verify Vite dev server starts**

Run: `cd web && npx vite build --emptyOutDir`
Expected: Build succeeds, no TypeScript or CSS errors.

- [ ] **Step 7: Commit**

```bash
git add web/package.json web/package-lock.json web/src/main.tsx web/src/index.css web/src/styles/magic-animations.css
git commit -m "feat: add foundation — dependencies, router, magic light theme tokens"
```

---

### Task 2: Particle Canvas Component

**Files:**
- Create: `web/src/components/ParticleCanvas.tsx`

**Interfaces:**
- Produces: `<ParticleCanvas />` — renders full-screen fixed canvas behind all content
- Props: none (self-contained, reads `prefers-reduced-motion` internally)

- [ ] **Step 1: Write ParticleCanvas component**

Write `web/src/components/ParticleCanvas.tsx`:

```tsx
import React, { useRef, useEffect, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PARTICLE_COUNT = 80;
const FAIRY_CHANCE = 0.003; // Rare fairy spawn per frame

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
      return {
        ...base,
        type: 'dust',
        size: Math.random() * 1.5 + 0.5,
        speedX: (Math.random() - 0.5) * 0.3,
        speedY: -(Math.random() * 0.4 + 0.1),
        life: 0,
        maxLife: Infinity,
      };
    case 'sparkle':
      return {
        ...base,
        type: 'sparkle',
        size: Math.random() * 2 + 1,
        speedX: (Math.random() - 0.5) * 0.5,
        speedY: -(Math.random() * 0.6 + 0.15),
        life: 0,
        maxLife: Infinity,
      };
    case 'fairy':
      return {
        ...base,
        type: 'fairy',
        size: Math.random() * 10 + 20,
        speedX: (Math.random() - 0.5) * 1.5,
        speedY: -(Math.random() * 0.3 + 0.05),
        opacity: 0,
        opacityDir: 1,
        life: 0,
        maxLife: 400 + Math.random() * 200,
      };
  }
}

function drawSparkle(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  size: number,
  opacity: number,
) {
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

function drawFairy(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  size: number,
  opacity: number,
  phase: number,
) {
  ctx.save();
  ctx.globalAlpha = opacity * 0.5;
  // Glow halo
  const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 1.5);
  gradient.addColorStop(0, 'rgba(236, 72, 153, 0.6)');
  gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.3)');
  gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(x, y, size * 1.5, 0, Math.PI * 2);
  ctx.fill();

  // Wings (two ellipses)
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
  ctx.beginPath();
  const wingBob = Math.sin(phase * 3) * 3;
  ctx.ellipse(x - size * 0.6, y - size * 0.2, size * 0.4, size * 0.25, -0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(x + size * 0.6, y - size * 0.2, size * 0.4, size * 0.25, 0.4, 0, Math.PI * 2);
  ctx.fill();

  // Body (small dot)
  ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
  ctx.beginPath();
  ctx.arc(x, y, size * 0.15, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

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
    const handleChange = (e: MediaQueryListEvent) => {
      reducedRef.current = e.matches;
    };
    mq.addEventListener('change', handleChange);

    resize();
    initParticles();
    window.addEventListener('resize', () => {
      resize();
      initParticles();
    });

    return () => {
      mq.removeEventListener('change', handleChange);
      window.removeEventListener('resize', resize);
    };
  }, [resize, initParticles]);

  // Cursor trail
  useEffect(() => {
    const isMobile = window.innerWidth < 768;
    if (isMobile) return;

    const onMove = (e: MouseEvent) => {
      cursorRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  // Animation loop
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

      // Cursor trail particles
      const cp = cursorRef.current;
      if (cp) {
        for (let i = 0; i < 2; i++) {
          ctx.beginPath();
          ctx.arc(
            cp.x + (Math.random() - 0.5) * 20,
            cp.y + (Math.random() - 0.5) * 20,
            Math.random() * 2 + 0.5,
            0,
            Math.PI * 2,
          );
          ctx.fillStyle = `rgba(139, 92, 246, ${Math.random() * 0.3 + 0.1})`;
          ctx.fill();
        }
      }

      const particles = particlesRef.current;

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];

        // Update position
        p.x += p.speedX + Math.sin(p.phase + performance.now() * 0.001) * 0.3;
        p.y += p.speedY;
        p.phase += 0.02;
        p.life++;

        // Opacity pulsing for sparkles
        if (p.type === 'sparkle') {
          p.opacity += p.opacityDir * 0.008;
          if (p.opacity >= 0.6) p.opacityDir = -1;
          if (p.opacity <= 0.1) p.opacityDir = 1;
        }

        // Fairy lifecycle
        if (p.type === 'fairy') {
          if (p.life < 60) p.opacity = Math.min(p.opacity + 0.008, 0.5); // fade in
          if (p.life > p.maxLife - 60) p.opacity = Math.max(p.opacity - 0.008, 0); // fade out
        }

        // Remove dead fairies or off-screen particles
        if (
          (p.type === 'fairy' && p.life >= p.maxLife) ||
          p.y < -50 ||
          p.y > height + 50 ||
          p.x < -50 ||
          p.x > width + 50
        ) {
          particles.splice(i, 1);
          continue;
        }

        // Draw
        switch (p.type) {
          case 'dust': {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(196, 181, 253, ${p.opacity})`;
            ctx.fill();
            break;
          }
          case 'sparkle': {
            drawSparkle(ctx, p.x, p.y, p.size, p.opacity);
            break;
          }
          case 'fairy': {
            drawFairy(ctx, p.x, p.y, p.size, p.opacity, p.phase);
            break;
          }
        }
      }

      // Maintain particle count
      while (particles.length < PARTICLE_COUNT) {
        particles.push(createParticle(width, height));
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    // Pause when tab hidden
    const onVisibility = () => {
      if (document.hidden) {
        cancelAnimationFrame(animId);
      } else {
        animId = requestAnimationFrame(loop);
      }
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
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
      aria-hidden="true"
    />
  );
};

export default ParticleCanvas;
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd web && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add web/src/components/ParticleCanvas.tsx
git commit -m "feat: add ParticleCanvas — star dust, sparkles, fairy sprites, cursor trail"
```

---

### Task 3: Navigation Bar + GitHub Star Button

**Files:**
- Create: `web/src/components/NavBar.tsx`
- Create: `web/src/components/GitHubStarButton.tsx`
- Create: `web/src/hooks/useGitHubStars.ts`
- Create: `web/src/styles/nav.css`

**Interfaces:**
- Produces: `<NavBar />` — fixed top nav, renders on all pages
- Produces: `<GitHubStarButton />` — displays live star count, links to GitHub
- Produces: `useGitHubStars()` hook → `{ stars: number, forks: number, loading: boolean }`

- [ ] **Step 1: Write useGitHubStars hook**

Write `web/src/hooks/useGitHubStars.ts`:

```ts
import { useState, useEffect } from 'react';

interface GitHubStats {
  stars: number;
  forks: number;
  loading: boolean;
}

const REPO = 'jingyu-wang/lite-agent-harness';
const API = `https://api.github.com/repos/${REPO}`;

export function useGitHubStars(): GitHubStats {
  const [stats, setStats] = useState<GitHubStats>({
    stars: 0,
    forks: 0,
    loading: true,
  });

  useEffect(() => {
    fetch(API)
      .then((res) => res.json())
      .then((data) => {
        setStats({
          stars: data.stargazers_count ?? 0,
          forks: data.forks_count ?? 0,
          loading: false,
        });
      })
      .catch(() => {
        setStats((s) => ({ ...s, loading: false }));
      });
  }, []);

  return stats;
}
```

- [ ] **Step 2: Write GitHubStarButton component**

Write `web/src/components/GitHubStarButton.tsx`:

```tsx
import React from 'react';
import { useGitHubStars } from '../hooks/useGitHubStars';

const REPO_URL = 'https://github.com/jingyu-wang/lite-agent-harness';

const GitHubStarButton: React.FC = () => {
  const { stars, loading } = useGitHubStars();

  return (
    <a
      href={REPO_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="nav__github-btn"
      aria-label="Star on GitHub"
    >
      <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
      </svg>
      <span>Star</span>
      {!loading && (
        <span className="nav__github-count">{stars.toLocaleString()}</span>
      )}
    </a>
  );
};

export default GitHubStarButton;
```

- [ ] **Step 3: Write NavBar component**

Write `web/src/components/NavBar.tsx`:

```tsx
import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import GitHubStarButton from './GitHubStarButton';

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: '🏠' },
  { path: '/about', label: 'About', icon: '📖' },
  { path: '/guide', label: 'Guide', icon: '🧭' },
  { path: '/learn', label: 'Learn', icon: '🎓' },
  { path: '/agent', label: 'Agent', icon: '🤖' },
];

const NavBar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="nav">
      <div className="nav__inner">
        {/* Logo */}
        <NavLink to="/" className="nav__logo" onClick={() => setMobileOpen(false)}>
          <span className="nav__logo-icon">✨</span>
          <span className="nav__logo-text">Lite Agent Harness</span>
        </NavLink>

        {/* Desktop links */}
        <div className="nav__links">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `nav__link ${isActive ? 'nav__link--active' : ''}`
              }
            >
              <span className="nav__link-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Right side */}
        <div className="nav__right">
          <GitHubStarButton />
          {/* Mobile hamburger */}
          <button
            className="nav__hamburger"
            onClick={() => setMobileOpen(!mobileOpen)}
            type="button"
            aria-label="Toggle menu"
          >
            <span className={`nav__hamburger-line ${mobileOpen ? 'open' : ''}`} />
            <span className={`nav__hamburger-line ${mobileOpen ? 'open' : ''}`} />
            <span className={`nav__hamburger-line ${mobileOpen ? 'open' : ''}`} />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="nav__mobile"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
          >
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `nav__mobile-link ${isActive ? 'nav__mobile-link--active' : ''}`
                }
                onClick={() => setMobileOpen(false)}
              >
                <span>{item.icon}</span> {item.label}
              </NavLink>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default NavBar;
```

- [ ] **Step 4: Write nav.css**

Write `web/src/styles/nav.css`:

```css
/* =========================================================================
   Navigation Bar
   ========================================================================= */

.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border-base);
}

.nav__inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 var(--space-6);
  gap: var(--space-6);
}

/* Logo */
.nav__logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-decoration: none;
  color: var(--color-text-primary);
  font-weight: var(--font-bold);
  font-size: var(--text-lg);
  flex-shrink: 0;
}

.nav__logo-icon {
  font-size: 22px;
  animation: magic-float 4s ease-in-out infinite;
}

.nav__logo-text {
  background: var(--gradient-magic-primary);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 4s ease infinite;
}

/* Desktop links */
.nav__links {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex: 1;
}

.nav__link {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: color var(--transition-fast), background var(--transition-fast);
  position: relative;
}

.nav__link:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-element);
}

.nav__link--active {
  color: var(--color-accent-primary);
}

.nav__link--active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 2px;
  background: var(--gradient-magic-gold);
  border-radius: var(--radius-full);
  box-shadow: var(--glow-gold);
}

.nav__link-icon {
  font-size: var(--text-base);
}

/* Right section */
.nav__right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

/* GitHub button */
.nav__github-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-element);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
}

.nav__github-btn:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--glow-magic);
}

.nav__github-count {
  background: var(--color-bg-elevated);
  padding: 1px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

/* Hamburger */
.nav__hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-2);
  background: none;
  border: none;
  cursor: pointer;
}

.nav__hamburger-line {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--color-text-primary);
  border-radius: 2px;
  transition: transform var(--transition-fast);
}

.nav__hamburger-line.open:nth-child(1) {
  transform: rotate(45deg) translate(4px, 4px);
}
.nav__hamburger-line.open:nth-child(2) {
  opacity: 0;
}
.nav__hamburger-line.open:nth-child(3) {
  transform: rotate(-45deg) translate(4px, -4px);
}

/* Mobile menu */
.nav__mobile {
  overflow: hidden;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border-base);
  padding: var(--space-3) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.nav__mobile-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-text-primary);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  transition: background var(--transition-fast);
}

.nav__mobile-link:hover {
  background: var(--color-bg-element);
}

.nav__mobile-link--active {
  color: var(--color-accent-primary);
  background: var(--color-bg-element);
}

/* =========================================================================
   Responsive
   ========================================================================= */

@media (max-width: 900px) {
  .nav__links {
    display: none;
  }
  .nav__github-btn span:not(:first-child) {
    display: none;
  }
  .nav__hamburger {
    display: flex;
  }
}
```

- [ ] **Step 5: Verify TypeScript compiles with new components**

Run: `cd web && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/NavBar.tsx web/src/components/GitHubStarButton.tsx web/src/hooks/useGitHubStars.ts web/src/styles/nav.css
git commit -m "feat: add NavBar with mobile menu, GitHubStarButton, and useGitHubStars hook"
```

---

### Task 4: PageTransition Wrapper + Page Shells

**Files:**
- Create: `web/src/components/PageTransition.tsx`
- Create: `web/src/pages/HomePage.tsx` (shell)
- Create: `web/src/pages/AboutPage.tsx` (shell)
- Create: `web/src/pages/GuidePage.tsx` (shell)
- Create: `web/src/pages/LearnPage.tsx` (shell)
- Create: `web/src/pages/AgentPage.tsx` (shell)
- Modify: `web/src/App.tsx` (replace with router)

**Interfaces:**
- Produces: `<PageTransition>` — wraps children in framer-motion fade+slide
- Produces: All page shells render placeholder content with PageTransition
- Produces: App.tsx renders Router with NavBar + ParticleCanvas + Routes

- [ ] **Step 1: Write PageTransition wrapper**

Write `web/src/components/PageTransition.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';

interface PageTransitionProps {
  children: React.ReactNode;
}

const variants = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

const PageTransition: React.FC<PageTransitionProps> = ({ children }) => (
  <motion.div
    variants={variants}
    initial="initial"
    animate="animate"
    exit="exit"
    transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
    style={{ minHeight: '100%' }}
  >
    {children}
  </motion.div>
);

export default PageTransition;
```

- [ ] **Step 2: Write HomePage shell**

Write `web/src/pages/HomePage.tsx`:

```tsx
import React from 'react';
import PageTransition from '../components/PageTransition';

const HomePage: React.FC = () => (
  <PageTransition>
    <div style={{ padding: '80px 24px', textAlign: 'center' }}>
      <h1>Home — Coming Soon</h1>
    </div>
  </PageTransition>
);

export default HomePage;
```

- [ ] **Step 3: Write AboutPage shell**

Write `web/src/pages/AboutPage.tsx`:

```tsx
import React from 'react';
import PageTransition from '../components/PageTransition';

const AboutPage: React.FC = () => (
  <PageTransition>
    <div style={{ padding: '80px 24px', maxWidth: 800, margin: '0 auto' }}>
      <h1>About — Coming Soon</h1>
    </div>
  </PageTransition>
);

export default AboutPage;
```

- [ ] **Step 4: Write GuidePage shell**

Write `web/src/pages/GuidePage.tsx`:

```tsx
import React from 'react';
import PageTransition from '../components/PageTransition';

const GuidePage: React.FC = () => (
  <PageTransition>
    <div style={{ padding: '80px 24px', maxWidth: 800, margin: '0 auto' }}>
      <h1>Guide — Coming Soon</h1>
    </div>
  </PageTransition>
);

export default GuidePage;
```

- [ ] **Step 5: Write LearnPage shell**

Write `web/src/pages/LearnPage.tsx`:

```tsx
import React from 'react';
import PageTransition from '../components/PageTransition';

const LearnPage: React.FC = () => (
  <PageTransition>
    <div style={{ padding: '80px 24px', maxWidth: 800, margin: '0 auto' }}>
      <h1>Learn — Coming Soon</h1>
    </div>
  </PageTransition>
);

export default LearnPage;
```

- [ ] **Step 6: Write AgentPage shell**

Write `web/src/pages/AgentPage.tsx`:

```tsx
import React from 'react';
import PageTransition from '../components/PageTransition';

const AgentPage: React.FC = () => (
  <PageTransition>
    <div style={{ padding: '80px 24px', textAlign: 'center' }}>
      <h1>Agent — Coming Soon</h1>
    </div>
  </PageTransition>
);

export default AgentPage;
```

- [ ] **Step 7: Rewrite App.tsx with router and layout**

Write `web/src/App.tsx`:

```tsx
import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import NavBar from './components/NavBar';
import ParticleCanvas from './components/ParticleCanvas';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import GuidePage from './pages/GuidePage';
import LearnPage from './pages/LearnPage';
import AgentPage from './pages/AgentPage';
import './styles/magic-animations.css';
import './styles/nav.css';

const GITHUB_URL = 'https://github.com/jingyu-wang/lite-agent-harness';

// Client-side redirect to GitHub
const GitHubRedirect: React.FC = () => {
  React.useEffect(() => {
    window.location.href = GITHUB_URL;
  }, []);
  return null;
};

const App: React.FC = () => {
  const location = useLocation();

  return (
    <>
      <ParticleCanvas />
      <NavBar />
      <main style={{ paddingTop: 56, minHeight: '100vh' }}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/guide" element={<GuidePage />} />
            <Route path="/learn" element={<LearnPage />} />
            <Route path="/agent" element={<AgentPage />} />
            <Route path="/github" element={<GitHubRedirect />} />
          </Routes>
        </AnimatePresence>
      </main>
    </>
  );
};

export default App;
```

- [ ] **Step 8: Remove old App.css and verify build**

Remove old App.css import since we're using modular styles:

```bash
rm web/src/App.css
```

Run: `cd web && npx vite build --emptyOutDir`
Expected: Build succeeds. All 5 routes render placeholder shells.

- [ ] **Step 9: Commit**

```bash
git add web/src/components/PageTransition.tsx web/src/pages/HomePage.tsx web/src/pages/AboutPage.tsx web/src/pages/GuidePage.tsx web/src/pages/LearnPage.tsx web/src/pages/AgentPage.tsx web/src/App.tsx
git rm web/src/App.css
git commit -m "feat: add router, PageTransition wrapper, and page shells"
```

---

### Task 5: Home Page — Hero, Cards, GitHub Section

**Files:**
- Create: `web/src/components/FairySprite.tsx`
- Create: `web/src/components/HeroSection.tsx`
- Create: `web/src/components/MagicCard.tsx`
- Create: `web/src/components/CardGrid.tsx`
- Create: `web/src/components/GitHubCommunity.tsx`
- Create: `web/src/styles/home.css`
- Modify: `web/src/pages/HomePage.tsx`

**Interfaces:**
- Consumes: `PageTransition`, `ParticleCanvas`, `useGitHubStars` (from prior tasks)
- `<MagicCard>` props: `{ icon: string; title: string; description: string; to: string }`
- `<FairySprite>` props: none (self-contained SVG animation)

- [ ] **Step 1: Write FairySprite component**

Write `web/src/components/FairySprite.tsx`:

```tsx
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
      {/* Wings */}
      <ellipse cx="20" cy="28" rx="14" ry="8" fill="rgba(236, 72, 153, 0.3)" transform="rotate(-30 20 28)" />
      <ellipse cx="44" cy="28" rx="14" ry="8" fill="rgba(139, 92, 246, 0.3)" transform="rotate(30 44 28)" />
      {/* Body */}
      <circle cx="32" cy="32" r="3" fill="rgba(255, 255, 255, 0.9)" />
      {/* Glow */}
      <circle cx="32" cy="32" r="12" fill="rgba(236, 72, 153, 0.15)" />
      {/* Sparkle dots */}
      <circle cx="32" cy="18" r="1" fill="#fbbf24" opacity="0.6" />
      <circle cx="24" cy="22" r="0.8" fill="#fbbf24" opacity="0.4" />
      <circle cx="40" cy="22" r="0.8" fill="#fbbf24" opacity="0.4" />
      <circle cx="32" cy="48" r="0.6" fill="#f59e0b" opacity="0.3" />
    </svg>
  </motion.div>
);

export default FairySprite;
```

- [ ] **Step 2: Write HeroSection component**

Write `web/src/components/HeroSection.tsx`:

```tsx
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
          <button
            className="hero__btn hero__btn--primary"
            onClick={() => navigate('/agent')}
          >
            <span className="hero__btn-icon">✨</span>
            开始施法
          </button>
          <button
            className="hero__btn hero__btn--secondary"
            onClick={scrollToCards}
          >
            <span className="hero__btn-icon">📖</span>
            了解更多
          </button>
        </motion.div>
      </div>

      {/* Scroll hint */}
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
```

- [ ] **Step 3: Write MagicCard component**

Write `web/src/components/MagicCard.tsx`:

```tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

interface MagicCardProps {
  icon: string;
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
```

- [ ] **Step 4: Write CardGrid component**

Write `web/src/components/CardGrid.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';
import MagicCard from './MagicCard';

const CARDS = [
  {
    icon: '🔮',
    title: '项目简介',
    description: '了解 Lite Agent Harness 的核心魔法',
    to: '/about',
  },
  {
    icon: '📜',
    title: '使用指南',
    description: '施展你的第一个代码咒语',
    to: '/guide',
  },
  {
    icon: '🎓',
    title: '学习入口',
    description: '深入理解 Agent 的魔法原理',
    to: '/learn',
  },
];

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.12 },
  },
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
```

- [ ] **Step 5: Write GitHubCommunity component**

Write `web/src/components/GitHubCommunity.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';
import { useGitHubStars } from '../hooks/useGitHubStars';

const REPO_URL = 'https://github.com/jingyu-wang/lite-agent-harness';

const GitHubCommunity: React.FC = () => {
  const { stars, forks, loading } = useGitHubStars();

  return (
    <section className="github-community">
      <div className="github-community__bg" />
      <motion.div
        className="github-community__content"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="github-community__title">🌟 开源魔法，众人共创</h2>

        {!loading && (
          <motion.div
            className="github-community__stats"
            initial={{ scale: 0.8 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
          >
            <span className="github-community__stat">
              ⭐ {stars.toLocaleString()} Stars
            </span>
            <span className="github-community__stat">
              🍴 {forks.toLocaleString()} Forks
            </span>
          </motion.div>
        )}

        <div className="github-community__actions">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="github-community__btn github-community__btn--primary"
          >
            ⭐ Star on GitHub
          </a>
          <a
            href={`${REPO_URL}/issues`}
            target="_blank"
            rel="noopener noreferrer"
            className="github-community__btn github-community__btn--secondary"
          >
            📋 View Issues
          </a>
        </div>
      </motion.div>
    </section>
  );
};

export default GitHubCommunity;
```

- [ ] **Step 6: Write home.css**

Write `web/src/styles/home.css`:

```css
/* =========================================================================
   Hero Section
   ========================================================================= */

.hero {
  position: relative;
  min-height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero__bg {
  position: absolute;
  inset: 0;
  background: var(--gradient-hero);
  z-index: 0;
}

.hero__content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: var(--space-8) var(--space-6);
  max-width: 720px;
}

.hero__title {
  font-size: var(--text-hero);
  font-weight: var(--font-bold);
  line-height: 1.1;
  margin-bottom: var(--space-4);
}

.hero__subtitle {
  font-size: var(--text-xl);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
  font-weight: var(--font-medium);
}

.hero__tagline {
  font-size: var(--text-lg);
  color: var(--color-accent-primary);
  margin-bottom: var(--space-3);
  font-weight: var(--font-medium);
}

.hero__desc {
  font-size: var(--text-base);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-8);
}

.hero__actions {
  display: flex;
  gap: var(--space-4);
  justify-content: center;
  flex-wrap: wrap;
}

.hero__btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 12px var(--space-8);
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.hero__btn--primary {
  background: var(--gradient-magic-primary);
  color: #fff;
  box-shadow: var(--glow-magic);
}

.hero__btn--primary:hover {
  box-shadow: 0 0 30px rgba(139, 92, 246, 0.5), 0 0 60px rgba(139, 92, 246, 0.25);
}

/* Magic circle on primary hover */
.hero__btn--primary::after {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: var(--radius-full);
  background: var(--gradient-magic-fairy);
  z-index: -1;
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.hero__btn--primary:hover::after {
  opacity: 1;
  animation: magic-circle 3s linear infinite;
}

.hero__btn--secondary {
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-base);
}

.hero__btn--secondary:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-md);
}

.hero__btn-icon {
  font-size: 1.1em;
}

.hero__scroll-hint {
  position: absolute;
  bottom: var(--space-6);
  font-size: var(--text-xl);
  color: var(--color-text-tertiary);
  z-index: 1;
}

/* Fairy sprite */
.fairy-sprite {
  margin-bottom: var(--space-4);
  display: inline-block;
}

/* =========================================================================
   Card Grid
   ========================================================================= */

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
  max-width: 960px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

/* =========================================================================
   Magic Card
   ========================================================================= */

.magic-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-5);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.magic-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--radius-lg);
  padding: 1px;
  background: var(--gradient-magic-fairy);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.magic-card:hover::before {
  opacity: 1;
}

.magic-card__icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: var(--space-4);
}

.magic-card__title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.magic-card__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-3);
}

.magic-card__cta {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-accent-primary);
}

/* =========================================================================
   GitHub Community
   ========================================================================= */

.github-community {
  position: relative;
  padding: var(--space-8) var(--space-6);
  text-align: center;
  overflow: hidden;
}

.github-community__bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, var(--color-bg-primary) 0%, #ede9fe 50%, #e0e7ff 100%);
  z-index: 0;
}

.github-community__content {
  position: relative;
  z-index: 1;
  max-width: 600px;
  margin: 0 auto;
}

.github-community__title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.github-community__stats {
  display: flex;
  gap: var(--space-6);
  justify-content: center;
  margin-bottom: var(--space-6);
}

.github-community__stat {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
}

.github-community__actions {
  display: flex;
  gap: var(--space-4);
  justify-content: center;
  flex-wrap: wrap;
}

.github-community__btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px var(--space-6);
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  transition: all var(--transition-normal);
}

.github-community__btn--primary {
  background: var(--gradient-magic-primary);
  color: #fff;
  box-shadow: var(--glow-magic);
}

.github-community__btn--primary:hover {
  box-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
}

.github-community__btn--secondary {
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-base);
}

.github-community__btn--secondary:hover {
  border-color: var(--color-accent-primary);
}

/* =========================================================================
   Responsive
   ========================================================================= */

@media (max-width: 768px) {
  .card-grid {
    grid-template-columns: 1fr;
    padding: var(--space-4) var(--space-4);
  }

  .hero__actions {
    flex-direction: column;
    align-items: center;
  }

  .github-community__stats {
    flex-direction: column;
    gap: var(--space-3);
  }
}
```

- [ ] **Step 7: Update HomePage with real content**

Write `web/src/pages/HomePage.tsx`:

```tsx
import React from 'react';
import PageTransition from '../components/PageTransition';
import HeroSection from '../components/HeroSection';
import CardGrid from '../components/CardGrid';
import GitHubCommunity from '../components/GitHubCommunity';
import '../styles/home.css';

const HomePage: React.FC = () => (
  <PageTransition>
    <HeroSection />
    <CardGrid />
    <GitHubCommunity />
  </PageTransition>
);

export default HomePage;
```

- [ ] **Step 8: Verify build**

Run: `cd web && npx vite build --emptyOutDir`
Expected: Build succeeds. Home page renders Hero + Cards + GitHub section.

- [ ] **Step 9: Commit**

```bash
git add web/src/components/FairySprite.tsx web/src/components/HeroSection.tsx web/src/components/MagicCard.tsx web/src/components/CardGrid.tsx web/src/components/GitHubCommunity.tsx web/src/styles/home.css web/src/pages/HomePage.tsx
git commit -m "feat: build Home page — hero, fairy sprite, magic cards, GitHub community"
```

---

### Task 6: About Page + Guide Page

**Files:**
- Create: `web/src/components/FeatureGrid.tsx`
- Create: `web/src/components/StepTimeline.tsx`
- Create: `web/src/styles/about.css`
- Create: `web/src/styles/guide.css`
- Modify: `web/src/pages/AboutPage.tsx`
- Modify: `web/src/pages/GuidePage.tsx`

**Interfaces:**
- `<FeatureGrid>`: self-contained grid of 6 feature cards
- `<StepTimeline>`: 4 expandable steps with code blocks
- Each page uses `<PageTransition>`

- [ ] **Step 1: Write FeatureGrid component**

Write `web/src/components/FeatureGrid.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';

const FEATURES = [
  { icon: '🧠', title: '多模型支持', desc: 'Anthropic Messages API 和 OpenAI Chat Completions API，统一抽象接口' },
  { icon: '🛡️', title: '三层护栏', desc: '路径沙箱 + 命令白名单 + 正则黑名单，层层安全防护' },
  { icon: '📊', title: '确定性反馈', desc: '基于 exit code 和结构化报告的反馈分析，不依赖 LLM 判断' },
  { icon: '⚡', title: '状态机驱动', desc: '纯函数状态转换表，确定性路由，零 LLM 参与决策' },
  { icon: '🔐', title: '凭证加密', desc: 'OS Keyring（桌面）+ AES-GCM（Docker），密钥不落盘' },
  { icon: '🐳', title: 'Docker 支持', desc: '多阶段构建，Docker + PyInstaller 双分发方案' },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const FeatureGrid: React.FC = () => (
  <motion.div
    className="feature-grid"
    variants={container}
    initial="hidden"
    whileInView="show"
    viewport={{ once: true }}
  >
    {FEATURES.map((f) => (
      <motion.div
        key={f.title}
        className="feature-card"
        variants={{
          hidden: { opacity: 0, scale: 0.95 },
          show: { opacity: 1, scale: 1 },
        }}
        whileHover={{ y: -4, boxShadow: 'var(--glow-card)' }}
      >
        <span className="feature-card__icon">{f.icon}</span>
        <h3 className="feature-card__title">{f.title}</h3>
        <p className="feature-card__desc">{f.desc}</p>
      </motion.div>
    ))}
  </motion.div>
);

export default FeatureGrid;
```

- [ ] **Step 2: Write about.css**

Write `web/src/styles/about.css`:

```css
/* =========================================================================
   About Page
   ========================================================================= */

.about-page {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

.about-page__heading {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  position: relative;
  display: inline-block;
}

.about-page__heading::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -4px;
  width: 60%;
  height: 3px;
  background: var(--gradient-magic-gold);
  border-radius: var(--radius-full);
}

.about-page__intro {
  font-size: var(--text-lg);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-8);
  margin-top: var(--space-4);
}

.about-page__tech {
  margin-top: var(--space-8);
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border-base);
}

.about-page__tech-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.about-page__tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.about-page__tech-tag {
  padding: var(--space-1) var(--space-3);
  background: var(--color-bg-element);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
}

.about-page__footer {
  margin-top: var(--space-6);
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
}

/* =========================================================================
   Feature Grid (used by About)
   ========================================================================= */

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.feature-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  text-align: center;
  transition: border-color var(--transition-normal);
}

.feature-card:hover {
  border-color: var(--color-accent-primary);
}

.feature-card__icon {
  font-size: 2rem;
  display: block;
  margin-bottom: var(--space-3);
}

.feature-card__title {
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.feature-card__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
}

/* =========================================================================
   Responsive
   ========================================================================= */

@media (max-width: 768px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 3: Update AboutPage**

Write `web/src/pages/AboutPage.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import FeatureGrid from '../components/FeatureGrid';
import '../styles/about.css';

const TECH = ['Python 3.12+', 'FastAPI', 'React 18', 'TypeScript', 'WebSocket', 'pytest', 'Docker', 'PyInstaller'];

const AboutPage: React.FC = () => (
  <PageTransition>
    <div className="about-page">
      <motion.h1
        className="about-page__heading"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        🔮 什么是 Lite Agent Harness？
      </motion.h1>

      <motion.p
        className="about-page__intro"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.15 }}
      >
        一个轻量级、模型无关的编程 Agent 框架，将 AI 代码生成抽象为"魔法咒语"的执行过程。
        从状态机驱动到三层护栏，从确定性反馈到安全凭证存储——每个环节都经过精心设计，
        让你在本地安全、可控地运行 AI 编码助手。
      </motion.p>

      <FeatureGrid />

      <motion.div
        className="about-page__tech"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
      >
        <h2 className="about-page__tech-title">技术栈</h2>
        <div className="about-page__tech-stack">
          {TECH.map((t) => (
            <span key={t} className="about-page__tech-tag">{t}</span>
          ))}
        </div>
        <p className="about-page__footer">
          MIT License · © 2026 Jingyu Wang
        </p>
      </motion.div>
    </div>
  </PageTransition>
);

export default AboutPage;
```

- [ ] **Step 4: Write StepTimeline component**

Write `web/src/components/StepTimeline.tsx`:

```tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Step {
  number: number;
  icon: string;
  title: string;
  code: string;
  desc: string;
}

const STEPS: Step[] = [
  {
    number: 1,
    icon: '🔮',
    title: '安装依赖',
    code: 'pip install -r requirements.txt',
    desc: '安装所有 Python 依赖包，包括 FastAPI、pydantic、anthropic、openai 等。',
  },
  {
    number: 2,
    icon: '📜',
    title: '配置 API 密钥',
    code: '# 在 Settings 面板中输入你的 API Key\n# 或设置环境变量:\nexport ANTHROPIC_API_KEY=sk-ant-...',
    desc: '支持 Anthropic 和 OpenAI 两种 Provider。密钥安全存储在 OS Keyring 或 AES-GCM 加密文件中。',
  },
  {
    number: 3,
    icon: '✨',
    title: '启动服务',
    code: 'make run\n# 或直接:\nuvicorn server.main:app --host 127.0.0.1 --port 8000 --reload',
    desc: '启动 FastAPI 开发服务器，WebSocket 和 REST API 自动就绪。',
  },
  {
    number: 4,
    icon: '🧙‍♀️',
    title: '开始施法',
    code: '# 打开浏览器访问 http://localhost:8000\n# 在 Agent 页面输入你的任务，开始施法！',
    desc: '在聊天界面输入任务描述，Agent 将自动规划、执行、观察并自我修正。',
  },
];

const StepTimeline: React.FC = () => (
  <div className="step-timeline">
    {STEPS.map((step, idx) => (
      <StepItem key={step.number} step={step} isLast={idx === STEPS.length - 1} />
    ))}
  </div>
);

// Individual step item
const StepItem: React.FC<{ step: Step; isLast: boolean }> = ({ step, isLast }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="step-item">
      {/* Connector line */}
      {!isLast && <div className="step-item__connector" />}

      {/* Number bubble */}
      <motion.button
        className={`step-item__bubble ${expanded ? 'step-item__bubble--active' : ''}`}
        onClick={() => setExpanded(!expanded)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        <span className="step-item__icon">{step.icon}</span>
        <span className="step-item__number">{step.number}</span>
      </motion.button>

      {/* Content */}
      <div className="step-item__content">
        <h3
          className="step-item__title"
          onClick={() => setExpanded(!expanded)}
          style={{ cursor: 'pointer' }}
        >
          {step.title}
        </h3>

        <AnimatePresence>
          {expanded && (
            <motion.div
              className="step-item__body"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <p className="step-item__desc">{step.desc}</p>
              <pre className="step-item__code">
                <code>{step.code}</code>
              </pre>
              <button
                className="step-item__copy"
                onClick={(e) => {
                  e.stopPropagation();
                  navigator.clipboard.writeText(step.code);
                }}
                type="button"
              >
                📋 Copy
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default StepTimeline;
```

- [ ] **Step 5: Write guide.css**

Write `web/src/styles/guide.css`:

```css
/* =========================================================================
   Guide Page
   ========================================================================= */

.guide-page {
  max-width: 700px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

.guide-page__heading {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  position: relative;
  display: inline-block;
}

.guide-page__heading::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -4px;
  width: 60%;
  height: 3px;
  background: var(--gradient-magic-gold);
  border-radius: var(--radius-full);
}

.guide-page__intro {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-8);
  margin-top: var(--space-4);
}

/* =========================================================================
   Step Timeline
   ========================================================================= */

.step-timeline {
  display: flex;
  flex-direction: column;
}

.step-item {
  display: flex;
  gap: var(--space-4);
  position: relative;
  padding-bottom: var(--space-6);
}

.step-item__connector {
  position: absolute;
  left: 23px;
  top: 48px;
  bottom: 0;
  width: 2px;
  background: var(--color-border-base);
}

.step-item--expanded .step-item__connector {
  background: var(--gradient-magic-primary);
}

.step-item__bubble {
  width: 48px;
  height: 48px;
  min-width: 48px;
  border-radius: 50%;
  background: var(--color-bg-element);
  border: 2px solid var(--color-border-base);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  flex-shrink: 0;
}

.step-item__bubble--active {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  box-shadow: var(--glow-magic);
}

.step-item__bubble--active .step-item__number {
  color: #fff;
}

.step-item__icon {
  font-size: 1.2rem;
  position: absolute;
  top: -8px;
  right: -6px;
}

.step-item__number {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-secondary);
}

.step-item__content {
  flex: 1;
  padding-top: var(--space-3);
}

.step-item__title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.step-item__body {
  overflow: hidden;
  margin-top: var(--space-3);
}

.step-item__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-3);
}

.step-item__code {
  background: #1e1b2e;
  color: #c4b5fd;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  overflow-x: auto;
  white-space: pre-wrap;
  position: relative;
}

.step-item__copy {
  margin-top: var(--space-2);
  padding: var(--space-1) var(--space-3);
  background: var(--color-bg-element);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.step-item__copy:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}
```

- [ ] **Step 6: Update GuidePage**

Write `web/src/pages/GuidePage.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import StepTimeline from '../components/StepTimeline';
import '../styles/guide.css';

const GuidePage: React.FC = () => (
  <PageTransition>
    <div className="guide-page">
      <motion.h1
        className="guide-page__heading"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        🧭 使用指南
      </motion.h1>

      <motion.p
        className="guide-page__intro"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.15 }}
      >
        只需四个步骤，在本地启动你的 AI 编程助手。
      </motion.p>

      <StepTimeline />
    </div>
  </PageTransition>
);

export default GuidePage;
```

- [ ] **Step 7: Verify build**

Run: `cd web && npx vite build --emptyOutDir`
Expected: Build succeeds.

- [ ] **Step 8: Commit**

```bash
git add web/src/components/FeatureGrid.tsx web/src/components/StepTimeline.tsx web/src/styles/about.css web/src/styles/guide.css web/src/pages/AboutPage.tsx web/src/pages/GuidePage.tsx
git commit -m "feat: build About page (feature grid) and Guide page (step timeline)"
```

---

### Task 7: Learn Page

**Files:**
- Create: `web/src/components/ConceptCards.tsx`
- Create: `web/src/styles/learn.css`
- Modify: `web/src/pages/LearnPage.tsx`

**Interfaces:**
- `<ConceptCards>`: expandable accordion cards for core concepts + demo list
- Uses framer-motion for expand/collapse

- [ ] **Step 1: Write ConceptCards component**

Write `web/src/components/ConceptCards.tsx`:

```tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Concept {
  title: string;
  icon: string;
  summary: string;
  details: string[];
}

const CONCEPTS: Concept[] = [
  {
    title: '状态机（State Machine）',
    icon: '⚡',
    summary: 'deterministic transition table — 纯函数路由决策',
    details: [
      '状态：IDLE → PLANNING → EXECUTING → OBSERVING → CORRECTING → COMPLETED',
      '转换由纯函数 transition(state, event) 计算，无 LLM 参与',
      '可完全在单元测试中验证（test_state_machine.py）',
    ],
  },
  {
    title: '三层护栏（Guardrails）',
    icon: '🛡️',
    summary: '路径沙箱 + 命令白名单 + 正则黑名单',
    details: [
      'Layer 1 - PathSandbox：限制文件读写范围',
      'Layer 2 - CommandWhitelist：仅允许安全命令通过',
      'Layer 3 - PatternBlacklist：拦截危险模式（rm -rf / 等）',
      '每层可返回 ALLOW / BLOCK / ASK_HUMAN',
    ],
  },
  {
    title: '确定性反馈（Feedback Analysis）',
    icon: '📊',
    summary: 'exit-code 和结构化报告分析，不依赖 LLM',
    details: [
      'run_tests → 解析 pytest-json-report',
      'execute_shell → exit code 判定',
      'RetryPolicy 检测 stuck loop（连续3次相同失败）',
    ],
  },
  {
    title: '多模型适配（LLM Adapters）',
    icon: '🧠',
    summary: '统一接口，即插即用',
    details: [
      'Anthropic：Messages API（claude-sonnet-5 等）',
      'OpenAI：Chat Completions API（gpt-4o 等）',
      'Mock：预设回复，零网络测试',
      '通过 ABC 抽象基类实现新 Provider',
    ],
  },
];

const DEMOS = [
  { name: 'demo_guardrail.py', desc: '演示护栏拦截 rm -rf / 等危险命令' },
  { name: 'demo_sandbox.py', desc: '演示路径沙箱 + 命令白名单' },
  { name: 'demo_feedback_loop.py', desc: '演示 Agent 失败 → 修正 → 完成流程' },
];

const ConceptCards: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="learn-section">
      {/* Core concepts */}
      <h2 className="learn-section__title">📚 核心概念</h2>
      <div className="concept-list">
        {CONCEPTS.map((c, i) => (
          <motion.div
            key={c.title}
            className={`concept-card ${openIndex === i ? 'concept-card--open' : ''}`}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
          >
            <button
              className="concept-card__header"
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
              type="button"
            >
              <span className="concept-card__icon">{c.icon}</span>
              <div className="concept-card__header-text">
                <h3 className="concept-card__title">{c.title}</h3>
                <p className="concept-card__summary">{c.summary}</p>
              </div>
              <span className="concept-card__expand">
                {openIndex === i ? '▲' : '▼'}
              </span>
            </button>

            <AnimatePresence>
              {openIndex === i && (
                <motion.div
                  className="concept-card__body"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <ul className="concept-card__details">
                    {c.details.map((d, j) => (
                      <li key={j}>{d}</li>
                    ))}
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {/* Documentation links */}
      <h2 className="learn-section__title" style={{ marginTop: 'var(--space-8)' }}>
        📖 文档链接
      </h2>
      <div className="learn-links">
        <a href="/README.md" className="learn-link">README — 项目文档</a>
        <a href="/DESIGN.md" className="learn-link">DESIGN.md — 设计系统</a>
        <a
          href="https://github.com/jingyu-wang/lite-agent-harness/wiki"
          target="_blank"
          rel="noopener noreferrer"
          className="learn-link"
        >
          GitHub Wiki — 更多资源
        </a>
      </div>

      {/* Demo scripts */}
      <h2 className="learn-section__title" style={{ marginTop: 'var(--space-8)' }}>
        🎥 演示 Demo
      </h2>
      <div className="demo-list">
        {DEMOS.map((d) => (
          <div key={d.name} className="demo-item">
            <code className="demo-item__name">{d.name}</code>
            <span className="demo-item__desc">{d.desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConceptCards;
```

- [ ] **Step 2: Write learn.css**

Write `web/src/styles/learn.css`:

```css
/* =========================================================================
   Learn Page
   ========================================================================= */

.learn-page {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6);
}

.learn-page__heading {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  position: relative;
  display: inline-block;
}

.learn-page__heading::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -4px;
  width: 60%;
  height: 3px;
  background: var(--gradient-magic-gold);
  border-radius: var(--radius-full);
}

.learn-page__intro {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-8);
  margin-top: var(--space-4);
}

/* =========================================================================
   Learn Sections
   ========================================================================= */

.learn-section__title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

/* =========================================================================
   Concept Cards
   ========================================================================= */

.concept-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.concept-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-fast);
}

.concept-card--open {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-md);
}

.concept-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  width: 100%;
  padding: var(--space-4) var(--space-5);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--color-text-primary);
}

.concept-card__header:hover {
  background: var(--color-bg-element);
}

.concept-card__icon {
  font-size: 1.8rem;
  flex-shrink: 0;
}

.concept-card__header-text {
  flex: 1;
}

.concept-card__title {
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.concept-card__summary {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  font-family: monospace;
}

.concept-card__expand {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.concept-card__body {
  overflow: hidden;
  border-top: 1px solid var(--color-border-base);
}

.concept-card__details {
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  list-style-position: inside;
}

.concept-card__details li::marker {
  color: var(--color-accent-primary);
}

/* =========================================================================
   Documentation Links
   ========================================================================= */

.learn-links {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.learn-link {
  display: block;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-text-primary);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  transition: all var(--transition-fast);
}

.learn-link:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
  box-shadow: var(--shadow-sm);
}

/* =========================================================================
   Demo List
   ========================================================================= */

.demo-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.demo-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-md);
}

.demo-item__name {
  font-family: monospace;
  font-size: var(--text-sm);
  color: var(--color-accent-primary);
  font-weight: var(--font-semibold);
  white-space: nowrap;
}

.demo-item__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
```

- [ ] **Step 3: Update LearnPage**

Write `web/src/pages/LearnPage.tsx`:

```tsx
import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/PageTransition';
import ConceptCards from '../components/ConceptCards';
import '../styles/learn.css';

const LearnPage: React.FC = () => (
  <PageTransition>
    <div className="learn-page">
      <motion.h1
        className="learn-page__heading"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        🎓 学习入口
      </motion.h1>

      <motion.p
        className="learn-page__intro"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.15 }}
      >
        深入理解 Agent 的魔法原理——从状态机到护栏，从反馈分析到多模型适配。
      </motion.p>

      <ConceptCards />
    </div>
  </PageTransition>
);

export default LearnPage;
```

- [ ] **Step 4: Verify build**

Run: `cd web && npx vite build --emptyOutDir`
Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/ConceptCards.tsx web/src/styles/learn.css web/src/pages/LearnPage.tsx
git commit -m "feat: build Learn page — concept cards, docs links, demo list"
```

---

### Task 8: Agent Page — Refactor Existing Chat

**Files:**
- Create: `web/src/styles/agent.css`
- Modify: `web/src/pages/AgentPage.tsx`
- Modify: `web/src/components/ChatView.tsx` (light theme header)
- Modify: `web/src/components/StateIndicator.tsx` (crystal ball theme)

**Interfaces:**
- AgentPage reuses all existing chat components (ChatView, MessageList, TextBubble, ToolCard, FeedbackBanner, InputBar, HistorySidebar, SettingsPanel, GuardrailModal)
- Visual-only changes: light colors, magic borders, purple glow

- [ ] **Step 1: Write agent.css**

Write `web/src/styles/agent.css`:

```css
/* =========================================================================
   Agent Page Layout
   ========================================================================= */

.agent-page {
  display: grid;
  grid-template-columns: 260px 1fr 300px;
  height: calc(100vh - 56px);
  overflow: hidden;
  background: var(--color-bg-primary);
}

.agent-page__sidebar {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-element);
  border-color: var(--color-border-base);
  overflow-y: auto;
}

.agent-page__sidebar--left {
  border-right: 1px solid var(--color-border-base);
}

.agent-page__sidebar--right {
  border-left: 1px solid var(--color-border-base);
  padding: var(--space-4);
}

.agent-page__main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* ---- Settings toggle ---- */
.agent-page__settings-toggle {
  width: 100%;
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: var(--text-sm);
  text-align: center;
  margin-bottom: var(--space-4);
  transition: all var(--transition-fast);
}

.agent-page__settings-toggle:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-sm);
}

/* ---- Banners ---- */
.agent-page__error-banner,
.agent-page__connecting,
.agent-page__awaiting-banner {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  z-index: 10;
}

.agent-page__error-banner {
  background: rgba(239, 68, 68, 0.08);
  color: var(--color-status-error);
  border: 1px solid var(--color-status-error);
}

.agent-page__connecting {
  background: var(--color-bg-element);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-base);
}

.agent-page__awaiting-banner {
  background: rgba(245, 158, 11, 0.08);
  color: var(--color-status-warning);
  border: 1px solid var(--color-status-warning);
}

/* =========================================================================
   ChatView (light theme)
   ========================================================================= */

.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-view__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--color-border-base);
  background: var(--color-bg-surface);
  flex-shrink: 0;
}

.chat-view__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 0;
  color: var(--color-text-primary);
}

/* =========================================================================
   State Indicator (crystal ball theme)
   ========================================================================= */

.state-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.state-indicator__orb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
}

.state-indicator__orb::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 3px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
}

.state-indicator__orb--idle { background: var(--color-text-tertiary); }
.state-indicator__orb--planning { background: var(--color-accent-primary); box-shadow: var(--glow-magic); animation: magic-breathe var(--magic-breathe); }
.state-indicator__orb--executing { background: var(--color-status-warning); box-shadow: var(--glow-gold); animation: magic-breathe var(--magic-breathe); }
.state-indicator__orb--observing { background: #f0883e; box-shadow: 0 0 12px rgba(240, 136, 62, 0.3); }
.state-indicator__orb--correcting { background: var(--color-accent-pink); box-shadow: 0 0 12px rgba(236, 72, 153, 0.3); }
.state-indicator__orb--awaiting_human { background: #bc8cff; box-shadow: 0 0 12px rgba(188, 140, 255, 0.3); animation: magic-breathe var(--magic-breathe); }
.state-indicator__orb--completed { background: var(--color-status-success); box-shadow: 0 0 12px rgba(16, 185, 129, 0.3); }
.state-indicator__orb--error { background: var(--color-status-error); box-shadow: 0 0 12px rgba(239, 68, 68, 0.3); }

.state-indicator__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
}

/* =========================================================================
   Message List
   ========================================================================= */

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.message-list--empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-list__item {
  animation: fade-in-up 0.3s ease-out;
}

.message-list__placeholder {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
}

.message-list__hint {
  font-size: var(--text-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-2);
}

.message-list__session {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  text-align: center;
}

.message-list__session--complete {
  background: rgba(16, 185, 129, 0.08);
  color: var(--color-status-success);
  border: 1px solid var(--color-status-success);
}

.message-list__session--error {
  background: rgba(239, 68, 68, 0.08);
  color: var(--color-status-error);
  border: 1px solid var(--color-status-error);
}

/* =========================================================================
   Input Bar
   ========================================================================= */

.input-bar {
  padding: var(--space-3) var(--space-6);
  border-top: 1px solid var(--color-border-base);
  background: var(--color-bg-surface);
  flex-shrink: 0;
}

.input-bar__container {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
}

.input-bar__textarea {
  flex: 1;
  resize: none;
  padding: 10px var(--space-4);
  background: var(--color-bg-input);
  border: 2px solid var(--color-border-base);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-size: var(--text-base);
  font-family: inherit;
  line-height: var(--leading-normal);
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.input-bar__textarea:focus {
  border-color: var(--color-accent-primary);
  animation: expand-ring 1.5s ease-out;
}

.input-bar__textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-bar__btn {
  padding: 10px var(--space-5);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.input-bar__btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-bar__btn--send {
  background: var(--gradient-magic-primary);
  color: #fff;
  box-shadow: var(--shadow-sm);
}

.input-bar__btn--send:hover:not(:disabled) {
  box-shadow: var(--glow-magic);
}

.input-bar__btn--stop {
  background: var(--color-status-error);
  color: #fff;
}

/* =========================================================================
   Text Bubble
   ========================================================================= */

.text-bubble {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.text-bubble:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-md);
}

.text-bubble__header {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-accent-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--color-border-base);
  background: var(--color-bg-element);
}

.text-bubble__content {
  padding: var(--space-3) var(--space-4);
}

.text-bubble__text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text-primary);
}

.text-bubble__cursor {
  display: inline-block;
  animation: blink 0.8s step-end infinite;
  color: var(--color-accent-primary);
  font-weight: var(--font-bold);
  margin-left: 2px;
}

@keyframes blink {
  50% { opacity: 0; }
}

/* =========================================================================
   Tool Card
   ========================================================================= */

.tool-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.tool-card:hover {
  border-color: var(--color-accent-primary);
}

.tool-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: var(--text-base);
  text-align: left;
  transition: background var(--transition-fast);
}

.tool-card__header:hover {
  background: var(--color-bg-element);
}

.tool-card__icon { font-size: var(--text-sm); width: var(--space-4); text-align: center; flex-shrink: 0; }
.tool-card__icon--invoked { color: var(--color-status-warning); }
.tool-card__icon--success { color: var(--color-status-success); }
.tool-card__icon--error { color: var(--color-status-error); }

.tool-card__name { font-weight: var(--font-semibold); font-family: monospace; flex: 1; }
.tool-card__duration { font-size: var(--text-sm); color: var(--color-text-tertiary); font-family: monospace; }
.tool-card__status { font-size: var(--text-sm); font-weight: var(--font-medium); }
.tool-card__status--invoked { color: var(--color-status-warning); }
.tool-card__status--success { color: var(--color-status-success); }
.tool-card__status--error { color: var(--color-status-error); }

.tool-card__expand { font-size: 10px; color: var(--color-text-tertiary); flex-shrink: 0; }

.tool-card__body {
  border-top: 1px solid var(--color-border-base);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.tool-card__section { display: flex; flex-direction: column; gap: var(--space-1); }
.tool-card__section-title {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tool-card__code {
  margin: 0;
  padding: var(--space-2) var(--space-3);
  background: #f8f0ff;
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.tool-card__code--stdout { color: var(--color-status-success); }
.tool-card__code--stderr { color: var(--color-status-error); }

.tool-card__meta { font-size: var(--text-sm); color: var(--color-text-tertiary); font-family: monospace; }

/* =========================================================================
   Feedback Banner
   ========================================================================= */

.feedback-banner {
  border-left: 4px solid;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.feedback-banner--pass { border-left-color: var(--color-status-success); background: rgba(16, 185, 129, 0.05); }
.feedback-banner--fail { border-left-color: var(--color-status-error); background: rgba(239, 68, 68, 0.05); }
.feedback-banner--warning { border-left-color: var(--color-status-warning); background: rgba(245, 158, 11, 0.05); }
.feedback-banner--unknown { border-left-color: var(--color-text-secondary); background: var(--color-bg-surface); }

.feedback-banner__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  color: var(--color-text-primary);
  font-size: var(--text-base);
  text-align: left;
}

.feedback-banner__verdict { font-weight: var(--font-bold); font-size: var(--text-sm); flex-shrink: 0; }
.feedback-banner__verdict--pass { color: var(--color-status-success); }
.feedback-banner__verdict--fail { color: var(--color-status-error); }
.feedback-banner__verdict--warning { color: var(--color-status-warning); }
.feedback-banner__verdict--unknown { color: var(--color-text-secondary); }

.feedback-banner__summary { flex: 1; font-size: var(--text-sm); color: var(--color-text-secondary); }
.feedback-banner__retry { font-size: var(--text-sm); color: var(--color-text-tertiary); flex-shrink: 0; }
.feedback-banner__expand { font-size: 10px; color: var(--color-text-tertiary); flex-shrink: 0; }

.feedback-banner__body {
  border-top: 1px solid var(--color-border-base);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.feedback-banner__section-title {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-1);
}

.feedback-banner__failures { display: flex; flex-direction: column; gap: var(--space-2); }
.feedback-banner__failure {
  padding: var(--space-2) var(--space-3);
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--radius-sm);
}

.feedback-banner__failure-location {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-status-error);
  font-family: monospace;
}

.feedback-banner__failure-message {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.feedback-banner__fix {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-sm);
}

.feedback-banner__code {
  margin: 0;
  font-family: monospace;
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  color: var(--color-accent-primary);
  white-space: pre-wrap;
  word-break: break-all;
}

/* =========================================================================
   Guardrail Modal
   ========================================================================= */

.guardrail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(30, 27, 75, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.guardrail-modal {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-accent-primary);
  border-radius: var(--radius-lg);
  width: 480px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--glow-magic), var(--shadow-lg);
}

.guardrail-modal__header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-base);
  background: var(--color-bg-element);
}

.guardrail-modal__icon { font-size: 22px; }

.guardrail-modal__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
}

.guardrail-modal__body {
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.guardrail-modal__field { display: flex; flex-direction: column; gap: var(--space-1); }

.guardrail-modal__label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.guardrail-modal__value {
  margin: 0;
  font-size: var(--text-base);
  color: var(--color-text-primary);
  line-height: var(--leading-normal);
}

.guardrail-modal__value--action {
  font-family: monospace;
  font-weight: var(--font-semibold);
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-element);
  border-radius: var(--radius-sm);
  display: inline-block;
  align-self: flex-start;
}

.guardrail-modal__code {
  margin: 0;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
}

.guardrail-modal__actions {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-border-base);
  justify-content: flex-end;
}

.guardrail-modal__btn {
  padding: var(--space-2) var(--space-6);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.guardrail-modal__btn--approve {
  background: var(--gradient-magic-primary);
  color: #fff;
}

.guardrail-modal__btn--approve:hover {
  box-shadow: var(--glow-magic);
}

.guardrail-modal__btn--reject {
  background: var(--color-bg-element);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-base);
}

.guardrail-modal__btn--reject:hover {
  background: var(--color-status-error);
  border-color: var(--color-status-error);
  color: #fff;
}

/* =========================================================================
   Settings Panel
   ========================================================================= */

.settings-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.settings-panel__title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  margin: 0 0 var(--space-1);
  color: var(--color-text-primary);
}

.settings-panel__message {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.settings-panel__message--success {
  background: rgba(16, 185, 129, 0.08);
  color: var(--color-status-success);
  border: 1px solid var(--color-status-success);
}

.settings-panel__message--error {
  background: rgba(239, 68, 68, 0.08);
  color: var(--color-status-error);
  border: 1px solid var(--color-status-error);
}

.settings-panel__section { display: flex; flex-direction: column; gap: var(--space-1); }

.settings-panel__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-secondary);
}

.settings-panel__input,
.settings-panel__select {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-base);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  font-family: inherit;
  outline: none;
  transition: border-color var(--transition-fast);
}

.settings-panel__input:focus,
.settings-panel__select:focus {
  border-color: var(--color-accent-primary);
}

.settings-panel__select { cursor: pointer; }

.settings-panel__btn {
  padding: var(--space-2) var(--space-4);
  background: var(--gradient-magic-primary);
  border: none;
  border-radius: var(--radius-md);
  color: #fff;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.settings-panel__btn:hover:not(:disabled) {
  box-shadow: var(--glow-magic);
}

.settings-panel__btn:disabled { opacity: 0.5; cursor: not-allowed; }

.settings-panel__divider {
  height: 1px;
  background: var(--color-border-base);
  margin: var(--space-1) 0;
}

.settings-panel__cred-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: var(--space-2); }

.settings-panel__cred-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
}

.settings-panel__cred-provider {
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  text-transform: capitalize;
  min-width: 70px;
}

.settings-panel__cred-status { flex: 1; font-size: var(--text-sm); color: var(--color-text-secondary); }

.settings-panel__cred-delete {
  padding: 2px var(--space-2);
  background: transparent;
  border: 1px solid var(--color-status-error);
  border-radius: var(--radius-sm);
  color: var(--color-status-error);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.settings-panel__cred-delete:hover {
  background: rgba(239, 68, 68, 0.08);
}

.settings-panel__hint { font-size: var(--text-sm); color: var(--color-text-tertiary); margin: 0; }

/* =========================================================================
   History Sidebar
   ========================================================================= */

.history-sidebar {
  display: flex;
  flex-direction: column;
  padding: var(--space-4);
}

.history-sidebar__title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  margin: 0 0 var(--space-3);
  color: var(--color-text-primary);
}

.history-sidebar__empty { display: flex; flex-direction: column; gap: var(--space-1); }

.history-sidebar__hint { font-size: var(--text-sm); color: var(--color-text-tertiary); margin: 0; }
.history-sidebar__subhint { font-size: var(--text-sm); color: var(--color-text-tertiary); margin: 0; opacity: 0.7; }

.history-sidebar__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: var(--space-1); }

.history-sidebar__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.history-sidebar__item:hover { background: var(--color-bg-elevated); }

.history-sidebar__task {
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-sidebar__state {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  text-transform: capitalize;
}

/* =========================================================================
   Responsive
   ========================================================================= */

@media (max-width: 900px) {
  .agent-page {
    grid-template-columns: 1fr;
  }
  .agent-page__sidebar {
    display: none;
  }
}
```

- [ ] **Step 2: Update ChatView for light theme**

Write `web/src/components/ChatView.tsx`:

```tsx
import React from 'react';
import type { WsServerMessage } from '../hooks/useWebSocket';
import type { AgentState } from '../hooks/useSession';
import MessageList from './MessageList';
import InputBar from './InputBar';
import StateIndicator from './StateIndicator';

interface ChatViewProps {
  messages: WsServerMessage[];
  state: AgentState;
  onSend: (text: string) => void;
  onStop: () => void;
}

const ChatView: React.FC<ChatViewProps> = ({
  messages,
  state,
  onSend,
  onStop,
}) => {
  const isRunning = ['planning', 'executing', 'observing', 'correcting'].includes(state);
  const isAwaiting = state === 'awaiting_human';
  const disabled = isRunning || isAwaiting || state === 'completed';

  return (
    <div className="chat-view">
      <div className="chat-view__header">
        <h1 className="chat-view__title">🔮 Agent — 代码魔法</h1>
        <StateIndicator state={state} />
      </div>

      <MessageList messages={messages} />

      <InputBar
        onSend={onSend}
        onStop={onStop}
        disabled={disabled}
        isRunning={isRunning}
        placeholder={
          isAwaiting
            ? 'Awaiting human approval...'
            : isRunning
              ? 'Agent is casting spells...'
              : 'Describe your task — the agent will cast a spell...'
        }
      />
    </div>
  );
};

export default ChatView;
```

- [ ] **Step 3: Update StateIndicator for crystal ball theme**

Write `web/src/components/StateIndicator.tsx`:

```tsx
import React from 'react';

interface StateIndicatorProps {
  state: string;
}

const STATE_LABELS: Record<string, string> = {
  idle: 'Idle',
  planning: 'Planning',
  executing: 'Executing',
  observing: 'Observing',
  correcting: 'Correcting',
  awaiting_human: 'Awaiting Human',
  completed: 'Completed',
  error: 'Error',
};

const StateIndicator: React.FC<StateIndicatorProps> = ({ state }) => {
  const label = STATE_LABELS[state] || state;

  return (
    <div className="state-indicator">
      <span className={`state-indicator__orb state-indicator__orb--${state}`} />
      <span className="state-indicator__label">{label}</span>
    </div>
  );
};

export default StateIndicator;
```

- [ ] **Step 4: Update AgentPage with full chat layout**

Write `web/src/pages/AgentPage.tsx`:

```tsx
import React, { useState, useCallback, useRef } from 'react';
import PageTransition from '../components/PageTransition';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSession, type AgentState } from '../hooks/useSession';
import ChatView from '../components/ChatView';
import HistorySidebar from '../components/HistorySidebar';
import SettingsPanel from '../components/SettingsPanel';
import GuardrailModal from '../components/GuardrailModal';
import '../styles/agent.css';

const AgentPage: React.FC = () => {
  const {
    send,
    messages,
    isConnected,
    connect,
    disconnect,
    error: wsError,
  } = useWebSocket();

  const [task, setTask] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const taskSubmittedRef = useRef(false);

  const { state, pendingGuardrail } = useSession(messages, task);

  const handleSend = useCallback(
    (text: string) => {
      setTask(text);
      taskSubmittedRef.current = true;
      connect();
      setTimeout(() => {
        send({ type: 'task.submit', content: text });
      }, 200);
    },
    [connect, send],
  );

  const handleStop = useCallback(() => {
    send({ type: 'session.cancel' });
    disconnect();
  }, [send, disconnect]);

  const handleGuardrailApprove = useCallback(() => {
    send({ type: 'guardrail.approve' });
  }, [send]);

  const handleGuardrailReject = useCallback(() => {
    send({ type: 'guardrail.reject' });
  }, [send]);

  const chatState: AgentState =
    state === 'idle' && !task ? 'idle' : state;

  const awaitingHuman = state === 'awaiting_human';

  return (
    <PageTransition>
      <div className="agent-page">
        {/* Left sidebar — History */}
        <aside className="agent-page__sidebar agent-page__sidebar--left">
          <HistorySidebar />
        </aside>

        {/* Main — Chat */}
        <main className="agent-page__main">
          <ChatView
            messages={messages}
            state={chatState}
            onSend={handleSend}
            onStop={handleStop}
          />

          {wsError && (
            <div className="agent-page__error-banner">{wsError}</div>
          )}

          {!isConnected && taskSubmittedRef.current && state !== 'completed' && state !== 'error' && (
            <div className="agent-page__connecting">Connecting...</div>
          )}

          {awaitingHuman && (
            <div className="agent-page__awaiting-banner">
              Agent is waiting for your approval.
            </div>
          )}
        </main>

        {/* Right sidebar — Settings */}
        <aside className="agent-page__sidebar agent-page__sidebar--right">
          <button
            className="agent-page__settings-toggle"
            onClick={() => setSettingsOpen(!settingsOpen)}
            type="button"
          >
            {settingsOpen ? 'Close Settings' : '⚙️ Settings'}
          </button>
          {settingsOpen && <SettingsPanel />}
        </aside>

        <GuardrailModal
          guardrail={pendingGuardrail}
          onApprove={handleGuardrailApprove}
          onReject={handleGuardrailReject}
        />
      </div>
    </PageTransition>
  );
};

export default AgentPage;
```

- [ ] **Step 5: Verify build**

Run: `cd web && npx vite build --emptyOutDir`
Expected: Build succeeds, all agent CSS classes resolve correctly.

- [ ] **Step 6: Commit**

```bash
git add web/src/styles/agent.css web/src/pages/AgentPage.tsx web/src/components/ChatView.tsx web/src/components/StateIndicator.tsx
git commit -m "feat: refactor Agent page with magic light theme — crystal ball indicator, white cards, purple glow"
```

---

### Task 9: Polish — Responsive, Accessibility, Final Pass

**Files:**
- Modify: `web/src/components/ParticleCanvas.tsx` (add mobile detection, reduced motion)
- Modify: `web/index.html` (add Inter font)
- (no new files)

- [ ] **Step 1: Add Inter font to index.html**

Read `web/index.html` first, then update `<head>`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lite Agent Harness — Where Code Becomes Magic</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: Verify ParticleCanvas already handles mobile + reduced motion**

The `ParticleCanvas` written in Task 2 already includes:
- `isMobile` check: reduces count to 30, skips cursor trail (< 768px)
- `prefers-reduced-motion` media query listener
- `visibilitychange` pause/resume

No changes needed — just verify by reading the file.

- [ ] **Step 3: Build and verify everything**

Run: `cd web && npx vite build --emptyOutDir`
Expected: Clean build, no errors.

- [ ] **Step 4: Start dev server and do quick visual check**

Run: `cd web && npx vite --host 127.0.0.1 --port 5173`
Open in browser, navigate between all 5 routes, verify:
- Home: Hero renders with gradient, fairy floats, cards have hover effects
- About: Feature grid renders, tags display
- Guide: Steps expand/collapse, code blocks visible
- Learn: Concepts expand/collapse, links work
- Agent: Chat UI renders (no backend needed for visual check)
- Nav: Active link highlight, mobile hamburger works below 900px

- [ ] **Step 5: Build production assets into server/static**

Run: `cd web && npx vite build --outDir ../server/static --emptyOutDir`
Expected: Build succeeds, `server/static/` contains updated assets.

- [ ] **Step 6: Git add everything and final commit**

```bash
git add web/index.html web/src/ server/static/
git status  # verify no unexpected changes
git commit -m "feat: add Inter font, build production assets, final polish"
```

---

### Task 10 (Optional): Backend Static Mount Verification

**Files:**
- Read only: `server/main.py`
- Read only: `server/static/`

**No changes** — verify existing static mount still serves the new frontend correctly.

- [ ] **Step 1: Check that FastAPI serves static files correctly**

Run: `python -c "from server.main import app; print('OK')"`

- [ ] **Step 2: Start the full server and verify**

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
# Open http://localhost:8000 — should load the new magic-themed frontend
# Navigate to /agent — chat UI should render
# Refresh any page directly — SPA routing should work (check if backend has catch-all)
```

- [ ] **Step 3: If SPA catch-all is missing, add to server/main.py**

Read `server/main.py` to check for catch-all route. If missing, add:

```python
from fastapi.staticfiles import StaticFiles

# After all API routes:
app.mount("/", StaticFiles(directory="server/static", html=True), name="static")
```

The `html=True` option serves `index.html` for any unmatched route, which is required for React Router client-side routing.

- [ ] **Step 4: Commit if changes made**

```bash
git add server/main.py
git commit -m "fix: add SPA catch-all static mount for React Router"
```

