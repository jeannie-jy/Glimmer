# Magic Theme Frontend Redesign — Design Spec

**Date**: 2026-07-16
**Status**: Approved
**Design System**: Magic Dream（纯梦幻魔法主题，明亮风格）

---

## 1. Overview

Redesign the Lite Agent Harness frontend with a dreamy "Magic" theme, inspired by Codex's structured homepage layout. Every code generation action is abstracted as a "magic spell." The design includes fairy/glitter animations, sparkle particles, and a multi-page architecture.

### Design Goals

- **Dreamy magic aesthetic**: Light lavender/pink/sky-blue gradients, golden accents, starry particles, bright and airy feel
- **Codex-style structure**: Distinct landing/home page with entry cards, plus sub-pages
- **Multi-page architecture**: React Router with 5 routes + external GitHub link
- **Rich animations**: framer-motion for UI transitions, Canvas for particle systems
- **Open Source friendly**: GitHub star count, repository links, community section
- **Preserve existing functionality**: The Agent chat interface remains but gets a magic theme overlay

---

## 2. Technology Decisions

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Routing | `react-router-dom` v6+ | Standard React SPA routing |
| UI Animations | `framer-motion` | Page transitions, hover effects, component mount/unmount |
| Particle System | Custom Canvas 2D | Fairy dust, sparkles, magic trails — full control |
| Styling | CSS Custom Properties | Replace existing dark tokens with magic light theme |
| State Management | React hooks (unchanged) | Sufficient for this scope |

### New Dependencies

```json
{
  "react-router-dom": "^7.x",
  "framer-motion": "^11.x"
}
```

---

## 3. Page Architecture

### Routes

| Path | Page | Description |
|------|------|-------------|
| `/` | Home | Landing page with hero, cards, GitHub section |
| `/about` | About | Project introduction, feature cards, tech stack |
| `/guide` | Guide | Step-by-step setup wizard with code blocks |
| `/learn` | Learn | Core concepts, documentation links, demo scripts |
| `/agent` | Agent | Existing chat interface with magic theme overlay |
| `/github` | External | Redirects to GitHub repository |

### Navigation Bar (Global)

Fixed top bar with `backdrop-filter: blur()` on scroll:

```
Logo  |  Home  ·  About  ·  Guide  ·  Learn  ·  Agent    |  ⭐ Star on GitHub
```

- Active page indicator: gold gradient underline with glow
- Mobile: hamburger menu with magic particle transition
- GitHub button shows live star count (fetched from GitHub API)

---

## 4. Magic Theme Design Tokens

**完全替换**原有的 Linear 暗色 token 系统，采用明亮梦幻配色。

### Background Colors（明亮浅色系）

```css
--color-bg-primary: #faf5ff;    /* 主背景（淡紫白） */
--color-bg-surface: #ffffff;    /* 卡片/面板背景 */
--color-bg-element: #f3e8ff;    /* 可交互元素背景 */
--color-bg-elevated: #ede9fe;   /* 弹出层背景 */
--color-bg-input: #f8f0ff;      /* 输入框背景 */
```

### Accent Colors（魔法主题色）

```css
--color-accent-primary: #8b5cf6;     /* 主色调（魔法紫） */
--color-accent-hover: #7c3aed;       /* 主色调悬停 */
--color-accent-gold: #f59e0b;        /* 金色点缀 */
--color-accent-gold-light: #fbbf24;  /* 浅金 */
--color-accent-pink: #ec4899;        /* 仙尘粉 */
--color-accent-cyan: #06b6d4;        /* 魔法青蓝 */
```

### Text Colors

```css
--color-text-primary: #1e1b4b;    /* 主文字（深紫黑） */
--color-text-secondary: #6b7280;  /* 次要文字 */
--color-text-tertiary: #9ca3af;   /* 辅助/弱化文字 */
```

### Gradients

```css
--gradient-hero: linear-gradient(180deg, #faf5ff 0%, #ede9fe 50%, #e0e7ff 100%);
--gradient-magic-primary: linear-gradient(135deg, #8b5cf6, #6d28d9, #3b82f6);
--gradient-magic-fairy: linear-gradient(135deg, #ec4899, #8b5cf6, #06b6d4);
--gradient-magic-text: linear-gradient(135deg, #8b5cf6, #ec4899, #f59e0b);
--gradient-magic-gold: linear-gradient(135deg, #f59e0b, #fbbf24);
```

### Glow Effects

```css
--glow-magic: 0 0 20px rgba(139, 92, 246, 0.3), 0 0 40px rgba(139, 92, 246, 0.15);
--glow-gold: 0 0 20px rgba(245, 158, 11, 0.3), 0 0 40px rgba(245, 158, 11, 0.15);
--glow-card: 0 0 30px rgba(139, 92, 246, 0.1), 0 8px 32px rgba(139, 92, 246, 0.08);
```

### Typography

- Hero title: `clamp(2.5rem, 6vw, 4.5rem)` with gradient text
- Headings: `--text-xl` / `--text-2xl` with purple accent
- Body: `--text-base` (15px), dark purple text on light background
- Font: Inter

### Magic Animation Tokens

```css
--magic-float-duration: 6s;
--magic-sparkle-duration: 2s;
--magic-transition: 0.6s cubic-bezier(0.16, 1, 0.3, 1);
--magic-breathe: 3s ease-in-out infinite;
```

---

## 5. Page Designs

### 5.1 Home Page (`/`)

#### Hero Section

- Full-viewport hero with light lavender-to-sky-blue gradient background (`--gradient-hero`)
- Canvas particle layer: floating fairy silhouettes (SVG) + golden sparkles + star dust against light background
- Title text: gradient animation (purple → pink → gold) with breathing glow
- Subtitle: "Where Code Becomes Magic" / "将每一次代码生成，化作魔法咒语"
- Two CTA buttons:
  - **Primary**: "✨ 开始施法" → navigates to `/agent`, hover triggers magic circle rotation
  - **Secondary**: "📖 了解更多" → smooth scrolls to card section
- Small fairy SVG floats near the title (CSS `@keyframes` float animation)

#### Magic Cards Section

Three cards in a row, each with:
- Icon on top (hover: slight bounce/rotation)
- Title + description
- CTA link → respective page
- Hover effects:
  - Card lifts up (`translateY(-8px)`)
  - Border glows with gradient animation
  - Mini sparkle burst via Canvas event trigger

```
 Card 1 (🔮)   →   "项目简介"   →   /about
 Card 2 (📜)   →   "使用指南"   →   /guide
 Card 3 (🎓)   →   "学习入口"   →   /learn
```

#### GitHub Community Section

- Background: soft lavender-to-purple gradient with subtle sparkle overlay
- Live star/fork count via GitHub API
- Two buttons: "⭐ Star on GitHub" / "📋 View Issues"
- Subtle star-field canvas effect in background

### 5.2 About Page (`/about`)

- Page heading with gradient underline
- Description paragraph
- Feature grid (6 cards): Multi-model, Guardrails, Feedback, State Machine, Credentials, Docker
- Tech stack section
- License and copyright footer

### 5.3 Guide Page (`/guide`)

- Step timeline: Step 1 → Step 2 → Step 3 → Step 4
- Each step: expandable accordion with code block
- Steps:
  1. Install dependencies (`pip install -r requirements.txt`)
  2. Configure API key
  3. Start server (`make run`)
  4. Open browser and cast your first spell
- Each step icon: 🪄 wand
- Code blocks: monospace, dark background, copy button

### 5.4 Learn Page (`/learn`)

- Core concepts section: expandable cards for State Machine, Guardrails, Feedback, LLM Adapters
- Documentation links: README, DESIGN.md, GitHub Wiki
- Demo scripts: list of runnable demos with descriptions

### 5.5 Agent Page (`/agent`)

Existing chat interface rebuilt with light magic theme:
- **Header**: Magic crystal ball 🔮 state indicator, light surface background
- **Message bubbles**: White cards with subtle purple border, soft shadow
- **Input bar**: Lavender background, magic circle glow animation on focus
- **Tool cards**: White cards with purple accent border, sparkle burst on expand
- **Guardrail modal**: Light surface with purple/gold gradient border
- **Sidebars**: Light lavender background (`--color-bg-element`)

---

## 6. Animation System

### 6.1 Canvas Particle Layer

A `<canvas>` element fixed as background across all pages.

**Particle types**:
1. **Star dust**: Small white/gold dots (0.5–2px), slow vertical float, slight horizontal drift
2. **Sparkles**: 4-point star shapes, random blink at different phases
3. **Fairy silhouettes**: Rare, larger sprite (~30px), glides across screen with bobbing motion, fades in/out
4. **Cursor trail**: 8–12 fading particles following mouse (desktop only), max trail length per particle: 400ms

**Performance**:
- Particle count: 60–100 (configurable)
- Use `requestAnimationFrame`
- Pause when tab is hidden (`visibilitychange`)

### 6.2 Framer Motion Animations

| Location | Animation |
|----------|-----------|
| Page transitions | `AnimatePresence` with magic circle wipe or fade+scale |
| Hero CTA buttons | Scale pulse, magic circle on hover |
| Feature cards | Staggered mount, lift on hover |
| Navigation links | Underline slide, glow on active |
| Code blocks | Fade in on expand |
| Modals | Scale in from center with spring |

### 6.3 CSS Animations

| Element | Animation |
|---------|-----------|
| Hero title gradient | `background-position` shift (keyframes) |
| Fairy SVG float | `translateY` oscillate + slight rotate |
| Card borders | `conic-gradient` rotation on hover |
| Breathing glow | `box-shadow` opacity pulse |
| Input focus ring | Expanding gradient ring |

---

## 7. Component Tree

```
App
├── ParticleCanvas          (global fixed background)
├── NavBar                   (global, all pages)
│   ├── Logo
│   ├── NavLinks
│   ├── MobileMenu
│   └── GitHubStarButton
├── AnimatePresence (router)
│   ├── HomePage
│   │   ├── HeroSection
│   │   │   ├── FairySprite
│   │   │   └── CTAButtons
│   │   ├── CardGrid
│   │   │   └── MagicCard (×3)
│   │   └── GitHubCommunity
│   ├── AboutPage
│   │   └── FeatureGrid
│   │       └── FeatureCard (×6)
│   ├── GuidePage
│   │   └── StepTimeline
│   │       └── StepAccordion (×4)
│   ├── LearnPage
│   │   ├── ConceptCards
│   │   └── DemoList
│   └── AgentPage
│       ├── ChatView          (refactored from existing)
│       │   ├── MessageList
│       │   │   ├── TextBubble
│       │   │   ├── ToolCard
│       │   │   └── FeedbackBanner
│       │   └── InputBar
│       ├── HistorySidebar
│       ├── SettingsPanel
│       └── GuardrailModal
```

---

## 8. File Plan

### New Files

```
web/src/
├── pages/
│   ├── HomePage.tsx
│   ├── AboutPage.tsx
│   ├── GuidePage.tsx
│   ├── LearnPage.tsx
│   └── AgentPage.tsx
├── components/
│   ├── ParticleCanvas.tsx      (Canvas particle system)
│   ├── NavBar.tsx              (Global navigation)
│   ├── MagicCard.tsx           (Reusable magic card)
│   ├── FairySprite.tsx         (Fairy SVG animation)
│   ├── GitHubStarButton.tsx    (GitHub star count)
│   ├── HeroSection.tsx         (Home hero)
│   ├── CardGrid.tsx            (Home card grid)
│   ├── GitHubCommunity.tsx     (Home GitHub section)
│   ├── FeatureGrid.tsx         (About feature cards)
│   ├── StepTimeline.tsx        (Guide steps)
│   ├── ConceptCards.tsx        (Learn concepts)
│   └── PageTransition.tsx      (Framer motion wrapper)
├── styles/
│   ├── magic-tokens.css        (Magic theme tokens)
│   ├── magic-animations.css    (CSS keyframes)
│   ├── nav.css
│   ├── home.css
│   ├── about.css
│   ├── guide.css
│   ├── learn.css
│   └── agent.css
└── hooks/
    └── useGitHubStars.ts       (GitHub API hook)
```

### Modified Files

| File | Changes |
|------|---------|
| `web/src/App.tsx` | Replace with router + layout |
| `web/src/main.tsx` | Add BrowserRouter |
| `web/src/index.css` | Replace dark tokens with magic light theme tokens |
| `web/src/App.css` | Refactor to page-level CSS files |
| `web/package.json` | Add react-router-dom, framer-motion |
| `web/src/components/ChatView.tsx` | Minor magic theme tweaks |
| `web/src/components/StateIndicator.tsx` | Crystal ball theme |
| `DESIGN.md` | Update with magic theme tokens |

### Unchanged Files

```
web/src/hooks/useWebSocket.ts
web/src/hooks/useSession.ts
web/src/services/api.ts
web/src/components/MessageList.tsx
web/src/components/TextBubble.tsx
web/src/components/ToolCard.tsx
web/src/components/FeedbackBanner.tsx
web/src/components/InputBar.tsx
web/src/components/GuardrailModal.tsx
web/src/components/HistorySidebar.tsx
web/src/components/SettingsPanel.tsx
```

---

## 9. Implementation Order

1. **Foundation**: Add dependencies, set up Router, create magic tokens CSS
2. **Particle System**: Implement `ParticleCanvas` component
3. **Navigation**: Build `NavBar`, `GitHubStarButton`, mobile menu
4. **Page Shells**: Create empty page components with `PageTransition`
5. **Home Page**: Hero → Cards → GitHub section
6. **Sub Pages**: About, Guide, Learn
7. **Agent Page**: Refactor existing chat into `/agent` route with magic theme
8. **Polish**: Cross-browser testing, performance tuning, responsive fixes

---

## 10. Constraints

- **No breaking changes** to the WebSocket protocol or backend
- **CSS tokens fully replaced** — dark theme replaced by light magic theme, existing CSS variables get new values
- **Existing component logic kept** — visual changes only, no logic/behavior changes
- **Accessibility**: `prefers-reduced-motion` disables animations, reduce particle count
- **Performance**: Canvas particles paused when tab inactive, max 100 particles
- **Mobile responsive**: Pages collapse gracefully, reduced particles on touch devices
