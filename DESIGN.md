# Design System

**主题**：Fairy-Tale Dream（西方梦幻童话风格）

明亮柔美、轻盈闪粉、粉白配色。将代码生成抽象为"魔法咒语"概念，界面充满小仙女、闪粉粒子和手写艺术字。

> 设计规范详见：[Fairy-Tale Theme Redesign Spec](docs/superpowers/specs/2026-07-16-fairy-tale-theme-redesign.md)

---

## Design Tokens

### Colors — Backgrounds

| Token                 | Value     | Description            |
| --------------------- | --------- | ---------------------- |
| `--color-bg-primary`  | `#fefaf5` | 主背景（白米色）         |
| `--color-bg-surface`  | `#ffffff` | 卡片/面板背景           |
| `--color-bg-element`  | `#fff0f5` | 可交互元素背景（极淡粉）  |
| `--color-bg-elevated` | `#ffeef2` | 弹出层背景（淡粉白）      |
| `--color-bg-input`    | `#fff5f7` | 输入框背景（微粉白）      |

### Colors — Accent

| Token                  | Value     | Description    |
| ---------------------- | --------- | -------------- |
| `--color-accent`       | `#f8a4c8` | 主色调（玫瑰粉） |
| `--color-accent-hover` | `#f595b8` | 主色调悬停       |

### Colors — Glow & Sparkle

| Token             | Value     | Description       |
| ----------------- | --------- | ----------------- |
| `--color-glow`    | `#ffd6e8` | 光晕色（桃色）     |
| `--color-sparkle` | `#ffe4ec` | 闪粉粒子色（极浅粉）|

### Colors — Text

| Token                   | Value     | Description |
| ----------------------- | --------- | ----------- |
| `--color-text-primary`  | `#3d2c2c` | 主文字（暖深棕）|
| `--color-text-secondary`| `#8c7575` | 次要文字（暖灰棕）|
| `--color-text-tertiary` | `#b8a0a0` | 辅助文字（浅暖灰）|

### Colors — Status

| Token                    | Value     | Description |
| ------------------------ | --------- | ----------- |
| `--color-status-success` | `#7ecb9a` | 成功（薄荷绿）|
| `--color-status-error`   | `#e88b8b` | 错误（柔和红）|
| `--color-status-warning` | `#e8c48b` | 警告（柔和金）|

### Colors — Borders

| Token                | Value     | Description      |
| -------------------- | --------- | ---------------- |
| `--color-border-base`| `#f0e6e8` | 默认边框（暖灰粉） |

### Gradients

| Token                    | Value                                                            | Usage     |
| ------------------------ | ---------------------------------------------------------------- | --------- |
| `--gradient-hero`        | `linear-gradient(180deg, #fefaf5 0%, #fff0f3 40%, #ffeef2 100%)`| Hero 背景  |
| `--gradient-title`       | `linear-gradient(135deg, #e8879b, #f8a4c8, #d4859e)`            | 标题渐变文字|
| `--gradient-fairy`       | `linear-gradient(135deg, #f8a4c8, #ffd6e8)`                     | 仙女/闪粉   |
| `--gradient-card-glow`   | `radial-gradient(circle at center, rgba(248,164,200,0.15) 0%, transparent 70%)` | 卡片光晕 |

### Shadows

| Token           | Value                                              |
| --------------- | -------------------------------------------------- |
| `--shadow-sm`   | `0 1px 3px rgba(61, 44, 44, 0.04)`                |
| `--shadow-md`   | `0 4px 16px rgba(61, 44, 44, 0.06)`               |
| `--shadow-lg`   | `0 12px 40px rgba(61, 44, 44, 0.08)`              |
| `--shadow-glow` | `0 8px 30px rgba(248, 164, 200, 0.2)`             |

### Spacing（4px Scale）

| Token        | Value |
| ------------ | ----- |
| `--space-1`  | 4px   |
| `--space-2`  | 8px   |
| `--space-3`  | 12px  |
| `--space-4`  | 16px  |
| `--space-5`  | 20px  |
| `--space-6`  | 24px  |
| `--space-7`  | 28px  |
| `--space-8`  | 32px  |

### Typography

**Font Families**

| Token           | Font                                                      | Role     |
| --------------- | --------------------------------------------------------- | -------- |
| `--font-display`| `'Great Vibes', cursive`                                  | 标题手写体 |
| `--font-tagline`| `'Noto Serif SC', serif`                                  | 中文艺术斜体|
| `--font-body`   | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` | 正文/UI  |

**Font Sizes**

| Token              | Value                         |
| ------------------ | ----------------------------- |
| `--text-xs`        | 11px                          |
| `--text-sm`        | 13px                          |
| `--text-base`      | 15px                          |
| `--text-lg`        | 18px                          |
| `--text-xl`        | 22px                          |
| `--text-2xl`       | 28px                          |
| `--text-hero`      | `clamp(2.5rem, 6vw, 4.5rem)`  |
| `--text-tagline-en`| `clamp(1.2rem, 2.5vw, 1.8rem)`|
| `--text-tagline-zh`| `clamp(1rem, 1.5vw, 1.3rem)`  |

**Font Weights**

| Token             | Value | Description |
| ----------------- | ----- | ----------- |
| `--font-regular`  | 400   | Regular     |
| `--font-medium`   | 500   | Medium      |
| `--font-semibold` | 600   | Semi-bold   |
| `--font-bold`     | 700   | Bold        |

**Line Heights**

| Token               | Value | Description |
| ------------------- | ----- | ----------- |
| `--leading-tight`   | 1.25  | Tight       |
| `--leading-normal`  | 1.5   | Normal      |
| `--leading-relaxed` | 1.6   | Relaxed     |

### Radii

| Token           | Value  |
| --------------- | ------ |
| `--radius-sm`   | 8px    |
| `--radius-md`   | 12px   |
| `--radius-lg`   | 20px   |
| `--radius-full` | 9999px |

### Animation Timings

| Token                      | Value                                    | Description    |
| -------------------------- | ---------------------------------------- | -------------- |
| `--magic-float-duration`   | `8s`                                     | 仙女轨道周期    |
| `--magic-sparkle-duration` | `2s`                                     | 闪粉闪烁        |
| `--magic-sweep-interval`   | `6s`                                     | 闪粉掠过间隔    |
| `--magic-sweep-duration`   | `1.5s`                                   | 闪粉掠过时长    |
| `--magic-breathe`          | `3s ease-in-out infinite`                | 呼吸光晕        |

### Transitions

| Token                 | Value   |
| --------------------- | ------- |
| `--transition-fast`   | 150ms   |
| `--transition-normal` | 250ms   |

---

## Typography System

| 元素 | 字体 | 字重 | 样式 |
|------|------|------|------|
| 主标题 "Glimmer" | Great Vibes | 400 | 粉色渐变 + 光晕阴影 |
| 英文副标题 "Where Code Becomes Magic" | Great Vibes | 400 | 浅棕 |
| 中文 tagline "每一次编码，都是一场施法" | Noto Serif SC | 400 | italic, 暖灰棕 |
| 所有正文 / UI | Inter | 400–700 | normal |

---

## Animation System

### 技术栈

| 层面     | 技术                     |
| -------- | ------------------------ |
| UI 动效  | `framer-motion` v11      |
| 粒子系统 | Canvas 2D（自建）         |
| CSS 动画 | `@keyframes` + CSS 变量   |

### Canvas 粒子类型

| 粒子         | 大小        | 行为                          | 颜色                  |
| ------------ | ----------- | ----------------------------- | --------------------- |
| 背景闪粉     | 0.3–1px     | 缓慢上浮 + 水平漂移 + 透明度闪烁| `#ffe4ec`, `#fff`, `#ffd6e8` |
| 仙女挥棒 burst| 0.5–2px    | 棒尖爆发，弧形扩散，1s 消散    | `#f8a4c8`, `#fff`     |
| 闪粉掠过     | 0.3–1.5px   | 从左扫到右，曲线路径，1.5–2s   | `#ffe4ec` → `#f8a4c8` |
| 掠过残留     | 0.2–0.8px   | 缓慢飘散，2–3s 消散           | `#ffe4ec`             |

### Framer Motion 动画

| 元素       | 动画                              |
| ---------- | --------------------------------- |
| 小仙女 SVG | 椭圆轨道运动 + 上下 bobbing         |
| 魔法卡片   | hover 上浮 + 光晕扩散 + 交错入场    |
| 页面过渡   | `AnimatePresence` fade + slide    |
| 步骤展开   | `AnimatePresence` height 动画     |

### CSS 关键帧

| 动画       | 描述                         |
| ---------- | ---------------------------- |
| 标题渐变   | `background-position` shift  |
| 魔法棒闪烁 | `sparkle-blink` 透明度脉冲    |
| 呼吸光晕   | `box-shadow` 透明度脉冲       |
| 输入框光环 | `expand-ring` 粉色版          |

### 性能约束

- 背景粒子 50–60 个，峰值 ≤ 120
- Tab 隐藏时暂停（`visibilitychange`）
- 移动端粒子减半 + 禁用掠过 + 禁用仙女
- 尊重 `prefers-reduced-motion`

---

## Page Architecture

| Path     | Page  | Description              |
| -------- | ----- | ------------------------ |
| `/`      | Home  | 童话主页（仙女 + 闪粉 + 卡片）|
| `/about` | About | 项目简介                  |
| `/guide` | Guide | 使用指南（Step by Step）   |
| `/learn` | Learn | 学习入口                  |
| `/agent` | Agent | 聊天界面（代码生成"施法"）  |

---

## References

- [Fairy-Tale Theme Redesign Spec](docs/superpowers/specs/2026-07-16-fairy-tale-theme-redesign.md)
- [Great Vibes — Google Fonts](https://fonts.google.com/specimen/Great+Vibes)
- [Noto Serif SC — Google Fonts](https://fonts.google.com/specimen/Noto+Serif+SC)
- [framer-motion](https://www.framer.com/motion/)
