# KHA Monitoring Dashboard Design System

## 1. Atmosphere & Identity

A quiet operations desk for Korean Housing Association monitoring. The interface should feel precise, calm, and repeatable: dense enough for morning scanning, restrained enough for daily use. The signature is functional minimalism: Korean-first headings, disciplined dividers, small accent signals, and article content as the visual priority.

## 2. Color

### Palette

| Role | Token | Light | Usage |
|------|-------|-------|-------|
| Surface/base | `--bg-primary` | `#F7F8F6` | App background |
| Surface/panel | `--bg-secondary` | `#EEF1EE` | Subtle bands, chip wells |
| Surface/card | `--bg-card` | `#FFFFFF` | Content sections and controls |
| Surface/header | `--bg-header` | `rgba(255,255,255,0.94)` | Sticky header and compact top bars |
| Text/primary | `--text-primary` | `#151716` | Headings and article titles |
| Text/secondary | `--text-secondary` | `#6D7773` | Metadata and helper text |
| Text/tertiary | `--text-tertiary` | `#A1AAA5` | Disabled and quiet chrome |
| Border/default | `--border` | `#DDE3DF` | Dividers and control outlines |
| Border/subtle | `--border-subtle` | `#EEF1EE` | List separators |
| Accent/primary | `--color-accent` | `#0A7C72` | Primary action and active state |
| Accent/soft | `--color-accent-soft` | `rgba(10,124,114,0.10)` | Active chip surface |
| Alert | `--dot-alert` | `#D94A38` | New/unread signal |

### Rules

- Use accent only for active controls, focus, and high-relevance signals.
- Category colors are secondary cues; labels and counts must work without color.
- Prefer tonal separation and dividers over decorative shadows.

## 3. Typography

### Scale

| Level | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| H1 | `24px` | 700 | 1.25 | 0 | Page title |
| H2 | `18px` | 700 | 1.35 | 0 | Category title |
| H3 | `15px` | 650 | 1.45 | 0 | Article title emphasis |
| Body | `14px` | 500 | 1.55 | 0 | Article rows |
| Body/sm | `13px` | 500 | 1.45 | 0 | Controls, metadata |
| Caption | `11px` | 700 | 1.35 | `0.08em` | Section labels |

### Font Stack

- Primary: `Pretendard`, `Apple SD Gothic Neo`, `Malgun Gothic`, system sans-serif.
- Mono/numeric: `ui-monospace`, `SFMono-Regular`, `Consolas`, monospace for dates and counts when needed.
- Serif is not used in core UI chrome.

## 4. Spacing & Layout

### Base Unit

All spacing derives from 4px.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | `4px` | Dot-to-label, tight gaps |
| `--space-2` | `8px` | Compact row spacing |
| `--space-3` | `12px` | Control padding |
| `--space-4` | `16px` | Section padding |
| `--space-5` | `20px` | Card padding |
| `--space-6` | `24px` | Header and page padding |
| `--space-8` | `32px` | Desktop page rhythm |

### Grid

- Desktop content uses a 12-column scan grid. Large-volume categories may span 6-8 columns and display their article rows in 2-3 internal columns so the first viewport reads horizontally, not as four tall silos.
- The default dashboard is an issue board: each category shows only `is_core` items first. Non-core items are not expanded in-card; the call to action transitions into the category focus view so the first viewport remains a situation board.
- Issue board cards use equal-width responsive columns. Importance changes content hierarchy, not card width; the grid must not look like mismatched masonry.
- Staff view prioritizes a top command band and article sections.
- Admin view keeps maintenance controls visible, but with text labels where possible.
- Under 720px, the app becomes a single column with a top toolbar and horizontal filter chips. No horizontal page scroll.

## 5. Components

### Top Rail
- **Structure**: brand, nav actions, category filter chips, refresh metadata.
- **States**: active page, hover, focus.
- **Accessibility**: visible labels or tooltips for non-obvious actions; no icon-only critical admin navigation on narrow screens.

### Category Chip
- **Structure**: dot, label, count.
- **Variants**: all, category, active.
- **States**: default, hover, active, focus.
- **Accessibility**: label and count remain visible without color.

### Issue Board Section
- **Structure**: category heading, core count badge, total count, core article list, focus-view call to action.
- **Variants**: has-core, no-core.
- **States**: default, hover, focus-visible.
- **Accessibility**: semantic section labels and sufficient touch target for category focus transition.
- **Desktop layout**: cards use a uniform responsive grid. Do not use duplicate vertical colour rails; status is communicated by text, count chips, and typography.
- **Header band**: only the top header area carries a very subtle category-tinted gradient. The article body stays neutral for readability.
- **Issue label**: place a compact "주요 현안" label between the header and the issue list so the first cards read as current association issues, not a generic feed.
- **CTA copy**: use "{category} 전체 보기({count}건)" for category transitions; avoid vague "flow" wording.
- **No-core state**: show an explicit text state such as "협회 관련 주요 현안 없음"; never rely on faded colour alone.

### Category Focus View
- **Structure**: category title, issue/total summary, source selector, article list panel.
- **Variants**: has selected source, empty selected source.
- **States**: entering, source selected, article hover/focus.
- **Interaction**: category chips, sidebar filters, and issue-board calls to action all use the same in-place transition. The sidebar Dashboard item returns to the issue board so users have one predictable home action.
- **Accessibility**: source selectors are buttons with active state, and focus is preserved in DOM order.

### Command Button
- **Structure**: compact text or icon+text button.
- **Variants**: primary, secondary, accent, danger.
- **States**: default, hover, active, focus, disabled.

## 6. Motion & Interaction

- Micro transitions: 140ms ease-out for hover/active.
- Standard transitions: 220ms ease-in-out for panels and in-place category transitions.
- Animate only `transform`, `opacity`, `background`, `border-color`, and `box-shadow`.
- Respect `prefers-reduced-motion`; reveal animations must not block content visibility.

## 7. Depth & Surface

Strategy: tonal-shift with restrained border support.

- Page background is warm off-white.
- Cards use white surfaces with subtle dividers, not heavy shadows.
- Hover elevation is a tiny translate plus softened border, never dramatic lift.
- Modals and drawers may use stronger shadows because they are temporary layers.
