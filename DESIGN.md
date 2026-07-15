# Design System

本项目使用 [Open Design](https://github.com/nexu-io/open-design) 进行界面开发。

**所选设计系统**：Linear（暗色主题）

**来源**：Open Design 内置的 Linear 设计系统（`linear` skill）

## Design Tokens

### Colors (Semantic)

| Token                    | Value       | Description               |
| ------------------------ | ----------- | ------------------------- |
| `--color-bg-app`         | `#0d1117`   | App background (deepest)  |
| `--color-bg-surface`     | `#161b22`   | Surface / card background |
| `--color-bg-element`     | `#1c2128`   | Hoverable element bg      |
| `--color-bg-elevated`    | `#2a3038`   | Elevated surface          |
| `--color-bg-input`       | `#0d1117`   | Input field background    |
| `--color-bg-success`     | rgba(...)   | Success background (10%)  |
| `--color-bg-error`       | rgba(...)   | Error background (10%)    |
| `--color-bg-warning`     | rgba(...)   | Warning background (10%)  |
| `--color-text-primary`   | `#e6edf3`   | Primary text              |
| `--color-text-secondary` | `#8b949e`   | Secondary text            |
| `--color-text-tertiary`  | `#6e7681`   | Tertiary / muted text     |
| `--color-border-base`    | `#30363d`   | Default border            |
| `--color-border-muted`   | `#21262d`   | Muted border              |
| `--color-accent-primary` | `#58a6ff`   | Primary accent (blue)     |
| `--color-accent-hover`   | `#79c0ff`   | Accent hover state        |
| `--color-status-success` | `#3fb950`   | Success / positive        |
| `--color-status-error`   | `#f85149`   | Error / danger            |
| `--color-status-warning` | `#d29922`   | Warning / attention       |

### Spacing (4px Scale)

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
- `font-family`: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`

**Font Sizes**

| Token         | Value |
| ------------- | ----- |
| `--text-xs`   | 11px  |
| `--text-sm`   | 12px  |
| `--text-base` | 14px  |
| `--text-lg`   | 16px  |
| `--text-xl`   | 18px  |

**Font Weights**

| Token             | Value | Description     |
| ----------------- | ----- | --------------- |
| `--font-regular`  | 400   | Regular         |
| `--font-medium`   | 500   | Medium          |
| `--font-semibold` | 600   | Semi-bold       |
| `--font-bold`     | 700   | Bold            |

**Line Heights**

| Token              | Value | Description |
| ------------------ | ----- | ----------- |
| `--leading-tight`  | 1.25  | Tight       |
| `--leading-normal` | 1.5   | Normal      |
| `--leading-relaxed`| 1.6   | Relaxed     |

### Radii

| Token         | Value |
| ------------- | ----- |
| `--radius-sm` | 4px   |
| `--radius-md` | 6px   |
| `--radius-lg` | 8px   |

### Shadows

| Token         | Value                                  |
| ------------- | -------------------------------------- |
| `--shadow-sm` | `0 1px 2px rgba(0, 0, 0, 0.3)`        |
| `--shadow-md` | `0 4px 12px rgba(0, 0, 0, 0.4)`       |
| `--shadow-lg` | `0 20px 60px rgba(0, 0, 0, 0.4)`      |

### Transitions

| Token                | Value   |
| -------------------- | ------- |
| `--transition-fast`  | 150ms   |
| `--transition-normal`| 250ms   |
