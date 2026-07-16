# Fairy-Tale Dream Theme — Design Spec

**Date**: 2026-07-16
**Status**: Approved
**Design Style**: Western fairy-tale dreamy aesthetic（西方梦幻童话风格）

---

## 1. Overview

彻底重构前端视觉风格，从暗色 Linear 主题转向童话梦幻风格。核心元素：轻盈闪粉粒子、小仙女环绕标题、手写艺术字体、粉白渐变配色。

### Design Goals

- **童话梦幻感**：白米色背景 + 玫瑰粉点缀，禁用紫/金色
- **花体艺术字**：Great Vibes 手写体作为标题字体
- **轻盈闪粉**：Canvas 细碎圆点粒子（0.3–1.5px），布林布林闪烁
- **仙女动画**：framer-motion 椭圆轨道环绕标题，魔法棒挥动触发闪粉
- **闪粉掠过**：每 6–8s 粒子束从左扫过标题文字
- **全局统一**：所有页面（Home/About/Guide/Learn/Agent）统一粉白风格

### 禁用颜色

- ❌ 紫色系（原 `--color-accent-primary: #8b5cf6`）
- ❌ 黄色/金色系（原 `--color-accent-gold: #f59e0b`）
- ❌ 暗色背景（原 `#0d1117` 系列）

---

## 2. New Color Palette

### Background Colors

```css
--color-bg-primary: #fefaf5;    /* 白米色主背景（warm ivory） */
--color-bg-surface: #ffffff;    /* 纯白卡片/面板 */
--color-bg-element: #fff0f5;    /* 极淡粉（lavender blush） */
--color-bg-elevated: #ffeef2;   /* 淡粉白弹出层 */
--color-bg-input: #fff5f7;      /* 微粉白输入框 */
```

### Accent Colors

```css
--color-accent: #f8a4c8;        /* 玫瑰粉主色调 */
--color-accent-hover: #f595b8;  /* 深玫瑰粉悬停 */
```

### Glow & Sparkle

```css
--color-glow: #ffd6e8;          /* 桃色光晕 */
--color-sparkle: #ffe4ec;       /* 极浅粉（粒子色） */
```

### Text Colors

```css
--color-text-primary: #3d2c2c;    /* 暖深棕 */
--color-text-secondary: #8c7575;  /* 暖灰棕 */
--color-text-tertiary: #b8a0a0;   /* 浅暖灰 */
```

### Status Colors

```css
--color-status-success: #7ecb9a;  /* 薄荷绿 */
--color-status-error: #e88b8b;    /* 柔和红 */
--color-status-warning: #e8c48b;  /* 柔和金 */
```

### Borders

```css
--color-border-base: #f0e6e8;  /* 暖灰粉边框 */
```

### Gradients

```css
--gradient-hero: linear-gradient(180deg, #fefaf5 0%, #fff0f3 40%, #ffeef2 100%);
--gradient-title: linear-gradient(135deg, #e8879b, #f8a4c8, #d4859e);
--gradient-fairy: linear-gradient(135deg, #f8a4c8, #ffd6e8);
--gradient-card-glow: radial-gradient(circle at center, rgba(248,164,200,0.15) 0%, transparent 70%);
```

### Shadows

```css
--shadow-sm: 0 1px 3px rgba(61, 44, 44, 0.04);
--shadow-md: 0 4px 16px rgba(61, 44, 44, 0.06);
--shadow-lg: 0 12px 40px rgba(61, 44, 44, 0.08);
--shadow-glow: 0 8px 30px rgba(248, 164, 200, 0.2);
```

### Typography

```css
--font-display: 'Great Vibes', cursive;     /* 标题手写体 */
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-tagline: 'Great Vibes', cursive;      /* 英文副标题 */
```

**Font Sizes** (keep existing tokens, add):
```css
--text-hero: clamp(2.5rem, 6vw, 4.5rem);
--text-tagline-en: clamp(1.2rem, 2.5vw, 1.8rem);
--text-tagline-zh: clamp(1rem, 1.5vw, 1.3rem);
```

### Radii

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 20px;
--radius-full: 9999px;
```

### Transitions & Animation Timings

```css
--transition-fast: 150ms;
--transition-normal: 250ms;
--magic-float-duration: 8s;
--magic-sparkle-duration: 2s;
--magic-sweep-interval: 6s;       /* 闪粉掠过间隔 */
--magic-sweep-duration: 1.5s;    /* 闪粉掠过时长 */
--magic-breathe: 3s ease-in-out infinite;
```

---

## 3. Typography

### Font Stack

| Role | Font | Source |
|------|------|--------|
| 主标题 "Lite Agent Harness" | **Great Vibes** (cursive, 400) | Google Fonts |
| 英文副标题 "Where Code Becomes Magic" | **Great Vibes** (cursive, 400) | Google Fonts |
| 中文 tagline "每一次编码，都是一场施法" | **Noto Serif SC** (serif, 400 italic) | Google Fonts |
| 正文 / UI 所有文字 | **Inter** (400/500/600/700) | Google Fonts |

### Title Display

```css
.hero__title {
  font-family: var(--font-display);
  font-size: var(--text-hero);
  background: var(--gradient-title);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 5s ease infinite;
  text-shadow: 0 2px 20px rgba(248, 164, 200, 0.3);
}
```

---

## 4. Home Page — Hero Section

### Layout

```
        ┌─────────────────────────────────────┐
        │     (Canvas 闪粉粒子飘浮层)           │
        │                                     │
        │    🧚‍♀️  ── ✨ ── 🧚‍♀️                │
        │    (framer-motion 椭圆轨道)          │
        │                                     │
        │   ℒ𝒾𝓉𝑒 𝒜𝑔𝑒𝓃𝓉 𝐻𝒶𝓇𝓃𝑒𝓈𝓈           │
        │   Where Code Becomes Magic          │
        │   每一次编码，都是一场施法            │
        │                                     │
        │   [✨ 开始施法]   [📖 了解更多]       │
        │              ↓                      │
        └─────────────────────────────────────┘
```

### Fairy Animation (framer-motion)

- SVG 小仙女 (~40px)，手持魔法棒
- 椭圆轨道：以标题文字为几何中心
  - `rx: 180px`, `ry: 40px`（水平宽椭圆）
  - 轨道周期 8 秒，`ease: linear`
  - 叠加轻微上下 bobbing（±6px，周期 3s，`ease: easeInOut`）
- 魔法棒尖端：CSS `@keyframes sparkle-blink` 闪烁小星点
- 每 6–8 秒随机触发"挥棒"——Canvas 在棒尖坐标生成小粒子 burst（~15 个粒子）

### Glitter Sweep (Canvas)

- 触发间隔：每 6–8 秒（随机）
- 粒子束：30–50 个 0.3–1.5px 圆点
- 颜色：`#ffe4ec` 到 `#f8a4c8`
- 路径：从标题文字左侧边缘扫入，弧形轨迹掠过文字区域，右侧渐隐
- 持续 1.5–2 秒
- 粒子束经过后残留 ~10 个微粒缓慢飘散（持续 2–3s）

### Background Sparkles (Canvas)

- 持续渲染 50–60 个极小圆点（0.3–1px）
- 透明度 0.1–0.5，`sin(time + perParticlePhase)` 缓慢闪烁
- 上浮速度 0.1–0.3px/frame，轻微水平漂移
- 颜色混合：`#ffe4ec`、`#ffffff`、`#ffd6e8`
- **没有**四角星形、仙子轮廓——只保留圆点
- 粒子直径 ≤ 1.5px，确保轻盈纤细

---

## 5. Home Page — Cards Section

### Magic Cards (×3)

```css
.magic-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-base);
  border-radius: 20px;
  padding: var(--space-6) var(--space-5);
  text-align: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.magic-card::before {
  /* 居中柔和粉色光晕 */
  content: '';
  position: absolute;
  inset: 0;
  background: var(--gradient-card-glow);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.magic-card:hover::before { opacity: 1; }
.magic-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-glow);
  border-color: var(--color-accent);
}
```

- 图标：Lucide 图标，`color: #f8a4c8`，size={28}
- 标题：Inter 600，`--text-lg`
- 描述：Inter 400，`--text-sm`，`--color-text-secondary`
- CTA：`探索 →` 用 `ArrowRight` 图标，粉色

### GitHub Community

- 背景：`#fefaf5 → #fff0f3` 渐变
- 标题：Great Vibes 手写体
- 按钮：玫瑰粉填充 + 白字
- 布局简洁，大面积留白

---

## 6. Sub-Page Designs

### About Page
- 特性卡片：纯白 + 粉色边框 + 20px 圆角
- 图标：Lucide 粉色系
- 技术栈标签：粉边框 + `#fff0f5` 背景
- 移除以紫色系为主的装饰元素

### Guide Page
- 步骤气泡：未展开 → 淡粉边框，展开 → `#f8a4c8` 填充
- 代码块：`#fdf6f8` 暖灰粉背景（不是深紫 `#1e1b2e`）
- 代码文字：`#3d2c2c` 暖深棕
- 连接线：粉色虚线

### Learn Page
- 概念卡片：悬停时左侧粉色边框高亮
- 展开区域：`#fff0f5` 淡粉背景
- 文档链接：粉色 hover
- Demo 列表：图标改为粉色 Lucide 图标

---

## 7. Agent Chat Page

- 三栏布局不变
- 侧栏背景：`#fff0f5`
- 消息气泡：纯白 + `1px solid #f0e6e8`，hover 时 `border-color: #f8a4c8`
- 输入框聚焦：粉色光晕（`expand-ring` 动画用粉色 `rgba(248,164,200,0.4)`）
- 状态指示器水晶球：粉色系光晕替换紫色
- 发送按钮：`linear-gradient(135deg, #f8a4c8, #f595b8)`
- Guardrail 弹窗：粉白背景 + 粉色边框

---

## 8. Animation System

### Canvas Particle System (rebuilt)

| 粒子类型 | 大小 | 行为 | 颜色 |
|---------|------|------|------|
| 背景闪粉 | 0.3–1px | 缓慢上浮 + 水平漂移 + 透明度闪烁 | `#ffe4ec`, `#fff`, `#ffd6e8` |
| 仙女挥棒 burst | 0.5–2px | 从棒尖爆发，弧形扩散，1s 消散 | `#f8a4c8`, `#fff` |
| 闪粉掠过 | 0.3–1.5px | 从左扫到右，曲线路径，1.5–2s | `#ffe4ec` → `#f8a4c8` |
| 掠过残留 | 0.2–0.8px | 缓慢飘散，2–3s 消散 | `#ffe4ec` |

**性能**：
- 背景粒子 50–60 个
- 掠过事件临时添加 30–50 个，结束后移除
- 总粒子数峰值 ≤ 120
- Tab 隐藏时暂停
- 移动端粒子减半，禁用掠过和仙女

### Framer Motion Animations

| 元素 | 动画 |
|------|------|
| 仙女 SVG | 椭圆轨道 `motion.div` + `useMotionValue` 计算 x/y |
| 魔法卡片 | `whileHover: { y: -8 }`, `staggerChildren` 入场 |
| 页面过渡 | `AnimatePresence` fade + slide（保留现有） |
| 步骤展开 | `AnimatePresence` height 动画（保留现有） |

### CSS Animations

| 元素 | 动画 |
|------|------|
| 标题渐变 | `background-position` shift (5s) |
| 魔法棒闪烁 | `sparkle-blink` (2s) |
| 背景光晕呼吸 | `magic-breathe` (3s) |
| 输入框聚焦环 | `expand-ring` (粉色版, 1.5s) |

---

## 9. Implementation Scope

### Mount of Changes

| 类别 | 文件数 | 说明 |
|------|--------|------|
| CSS tokens | 1 | `index.css` 全部重写（粉白色系） |
| CSS animations | 1 | `magic-animations.css` 重写（去掉紫色相关 keyframes） |
| Canvas 粒子 | 1 | `ParticleCanvas.tsx` 重写（细碎圆点 + 掠过 + 仙女挥棒） |
| Framer 仙女 | 1 | `FairySprite.tsx` 重写（轨道运动 + 魔法棒） |
| Hero 区 | 1 | `HeroSection.tsx` 重写（新字体 + 3 行文字） |
| 卡片区 | 3 | `CardGrid.tsx`, `MagicCard.tsx`, `GitHubCommunity.tsx` 改色 |
| 子页面 | 6 | About/Guide/Learn 页面 + CSS 改色 |
| Agent 页 | 2 | `agent.css`, `ChatView.tsx`, `StateIndicator.tsx` 改色 |
| 导航栏 | 2 | `nav.css`, `NavBar.tsx` 改色 |
| HTML | 1 | `index.html` 添加 Great Vibes + Noto Serif SC 字体 |
| **总计** | **~18** | |

### Files NOT Touched

- 所有 hooks（useWebSocket, useSession, useGitHubStars）
- services/api.ts
- MessageList, TextBubble, ToolCard, FeedbackBanner, InputBar, GuardrailModal, HistorySidebar, SettingsPanel 组件逻辑
- Python 后端所有文件
- DESIGN.md（在 plan 阶段更新）

---

## 10. Constraints

- 零紫色、零黄色在所有 UI 中出现
- 标题用 Great Vibes 手写体，正文保留 Inter
- Canvas 粒子只保留细碎圆点（≤1.5px），无四角星、无仙子轮廓
- 粒子峰值 ≤120，Tab 隐藏暂停
- 尊重 `prefers-reduced-motion`
- 不改变任何组件逻辑 / WebSocket / 后端
