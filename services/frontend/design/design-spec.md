# SentinelStream Frontend Design Spec (v1)

This document defines the visual system, layout rules, component standards, and interaction patterns for SentinelStream.
Single source of truth for UI consistency. Business logic and API contracts are out of scope.

## Principles
- Institutional dark theme, high clarity, minimal decoration.
- Information hierarchy first: prioritize recency + confidence + impact.
- Consistency over novelty: spacing/typography/color must come from tokens.
- Data-dense but readable: tables and compact cards preferred.
- Edge conversions only: timestamps stored/handled in UTC; display may convert to local time if needed.

---

## Design Tokens
All colors, spacing, radii, typography, shadows, and z-index values must reference `tokens.json`.
Never hardcode arbitrary hex values in components. If a new value is needed, add it to tokens.

---

## Layout & Grid

### Breakpoints (desktop-first)
- `xl`: 1280+
- `2xl`: 1536+
Primary design baseline: **1440px wide**.

### Page container
- Max content width: 1440–1560px
- Horizontal padding: 24px (desktop), 16px (smaller)

### Grid
- 12-column grid, 24px gutter, 24px outer margins (desktop baseline)
- Monitor page uses a 2-column layout:
  - Left: 8 columns (signals)
  - Right: 4 columns (Market Pulse + System snapshot)

### Scroll behavior
- Each page scrolls vertically.
- Avoid nested scroll containers unless needed (e.g., right-side drawer body).
- Tables: allow horizontal scroll on small widths.

---

## Typography

### Font families
- UI sans: Inter (or system fallback)
- Mono: JetBrains Mono (or system fallback)

### Hierarchy (use token aliases)
- Page Title: `text.h1`
- Section Title: `text.h2`
- Card Title: `text.h3`
- Body: `text.body`
- Label: `text.label`
- Caption/Meta: `text.caption`
- Table/Numbers: use mono in dense contexts (optional)

Rules:
- Use **one** dominant title per page.
- Prefer sentence case for labels and headings.
- Numeric KPIs should be tabular/mono when possible.

---

## Color & Surfaces

### Background layers
- App background: `colors.bg.primary`
- Raised surface (cards/panels): `colors.bg.surface`
- Elevated surface (modals/drawers): `colors.bg.elevated`

### Borders & dividers
- Default border: `colors.border.default`
- Subtle divider: `colors.border.subtle`

### Text
- Primary: `colors.text.primary`
- Secondary: `colors.text.secondary`
- Muted: `colors.text.muted`
- Disabled: `colors.text.disabled`

### Semantic colors
- Positive: `colors.semantic.positive`
- Negative: `colors.semantic.negative`
- Warning: `colors.semantic.warning`
- Info: `colors.semantic.info`

### Interaction colors
- Hover overlay: `colors.state.hover`
- Active overlay: `colors.state.active`
- Focus ring: `colors.state.focusRing`

---

## Spacing & Sizing

### Spacing scale
Use token spacing values only:
- 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64

### Component paddings
- Card padding (default): 16–24
- Compact cards: 12–16
- Page section gap: 24–32
- Table cell padding: 12–16

### Corner radius
- Small: 8
- Medium: 12
- Large: 16

---

## Core Components

### 1) Top Navigation (TopNav)
Purpose: primary module navigation.

Structure:
- Left: product name/logo
- Center/Right: nav items (Monitor, Signals, Topics, Backtest, System)
- Optional right: global actions (search, settings)

States:
- Default
- Hover (background subtle)
- Active (underline or left border indicator)
- Focus-visible (focus ring)

Rules:
- Nav height: 56–64px
- Keep labels short and consistent.

---

### 2) Page Header (PageHeader)
Purpose: consistent title + filters + actions.

Includes:
- Title (H1)
- Subtitle/caption (optional)
- Filter row (search, dropdowns, date range)
- Actions (primary/secondary buttons)

Rules:
- Filters align left; actions align right.
- Sticky header is optional; if sticky, use subtle border/shadow.

---

### 3) Card (Card)
Used for panels, widgets, containers.

Variants:
- `default`: normal surface
- `compact`: smaller padding
- `highlight`: emphasized border (used for urgent items)

Specs:
- Background: `bg.surface`
- Border: `border.default`
- Radius: `radius.md`
- Shadow: subtle (`shadow.sm`) only if needed to separate layers

Header:
- Title (H3)
- Right aligned actions (icon buttons)

---

### 4) Table (DataTable)
Used for Signals history, Backtest runs, Ingestion runs.

Features:
- Sticky header (optional)
- Sort icons (caret up/down)
- Row hover highlight
- Clickable rows open details drawer (where applicable)

Row states:
- Default
- Hover (use `state.hover`)
- Selected (use `state.selected`)
- Error (optional left border in negative semantic)

Rules:
- Use mono for timestamps/IDs if needed.
- Avoid zebra by default; use subtle row dividers.

---

### 5) Chip / Tag (Chip)
Used for sentiment, status, and recency indicators.

Variants:
- Sentiment: positive/negative/neutral
- Status: running/succeeded/failed
- Recency: New (<= 30 min)

Rules:
- Always include label text (don’t rely on color only).
- Compact size for dense lists.

---

### 6) Metric Tile (MetricTile)
Small KPI display used in System snapshot.

Structure:
- Label (caption)
- Value (H2 or H3)
- Optional delta (chip)

Variants:
- default
- positive/negative/warning

Rules:
- Keep to 2 lines max; avoid paragraphs.

---

### 7) Signal Card (SignalCard)
Primary entity for Monitor Verified Signals list.

Fields:
- Ticker (mono)
- Headline/title (1–2 lines)
- Sentiment chip
- Confidence (0–100%)
- Timestamp (UTC display; optional local tooltip)
- Optional source icon/link

States:
- Default
- Hover
- High confidence (>= 0.80) → highlight border or accent line
- New (<= 30 min) → “New” chip + subtle glow

Rules:
- Make “fresh + high confidence” most visually salient.
- Keep cards compact; details go to drawer.

---

### 8) Right-side Drawer (DetailDrawer)
Used for Signal details, Backtest details.

Behavior:
- Slides in from right
- Width: 420–520px desktop
- Header fixed, body scrolls
- Close on ESC, close button

Content:
- Summary
- Entities list
- Raw output (optional collapsible)
- External links (open source article)

---

### 9) Buttons & Icon Buttons
Button variants:
- Primary (accent)
- Secondary (neutral surface)
- Ghost (icon-only / minimal)

States:
- Hover/Active overlays
- Focus ring visible
- Disabled reduces opacity + disables pointer events
- Loading shows spinner + disables click

---

## Page Specifications

### A) Monitor (Market-facing dashboard)
Layout: 8/4 columns.

Left (Verified Signals):
- Sort controls: Recency / Confidence / Impact
- Filter: ticker search (optional)
- List of SignalCards

Right:
- Market Pulse widget (themes list)
- System Snapshot widget (last ingestion run, failures, latency, backlog)

Emphasis:
- New signals and high-confidence signals stand out.
- Use timestamps prominently.

---

### B) Signals (Exploration)
- Table with filters:
  - ticker, sentiment, confidence range, date range
- Row click opens DetailDrawer
- Optional “Export CSV” action

---

### C) Topics
- Topic list (table or compact cards)
- Each row shows:
  - topic name, sentiment mix, related tickers count, last updated
- Click opens topic details (related signals/news list)

---

### D) Backtest
- Backtest runs table (status, strategy, timeframe, key metrics)
- Detail view includes:
  - equity curve placeholder
  - summary stats tiles
  - trades table

---

### E) System (Ops dashboard)
Purpose: run history + operational metrics.

Sections:
1) Ingestion Runs table:
   - started_at, duration, status, fetched/inserted/deduped, error
2) Scheduler status widget:
   - next run, lock status, last success, consecutive failures
3) LLM usage widget:
   - analyses/day, failure rate, provider/model
4) Alerts panel:
   - recent failures, rate-limit events

Actions (optional MVP):
- “Run ingestion now” button
- “Re-run analysis” (disabled until supported)

---

## Interaction Patterns

### Hover & selection
- List items/cards: subtle surface lift via `state.hover`.
- Selected rows: `state.selected` background + left accent border.

### Sorting
- Column headers show sort state.
- Sorting controls should be consistent across tables.

### Loading
- Use skeleton loaders for lists/tables.
- Avoid layout shift.

### Empty states
- Provide concise text + one suggested action (“Adjust filters”, “Run ingestion now”).

### Errors
- Show inline error banner in widgets (not only console).
- For failed runs, surface `error_message` in table row + drawer.

---

## Accessibility
- Focus-visible ring on all interactive elements.
- Ensure contrast is sufficient for text and semantic chips.
- Tables: proper semantics (header cells, aria-sort where applicable).
- Drawer: trap focus, ESC closes, restore focus to trigger.

---

## Engineering Mapping (Tailwind guidance)
- Use Tailwind theme extension for tokens (colors, spacing, radii, shadows).
- Prefer semantic class names via design tokens (e.g., `bg-bgPrimary`, `text-textPrimary`) rather than raw hex.
- Avoid inline styles except for dynamic chart sizing.

End of spec.