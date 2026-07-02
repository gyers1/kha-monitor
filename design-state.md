# Design Review State

## Inferred Brief

- Reviewed artefact: Korean Housing Association monitoring dashboard at `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/admin`.
- Captures: `kha-monitor-home-1366.png`, `kha-monitor-admin-1366.png`, `kha-monitor-home-390.png`, `kha-monitor-admin-390.png`.
- Primary task: staff quickly identify KHA-relevant press releases, legislative notices, gazette items, bills, and schedules for daily monitoring and reporting.
- Secondary task: administrator maintains monitored sites, category filters, refresh/update state, selector tests, and summary extraction diagnostics.
- Audience: KHA staff using a local Windows pywebview app, likely repeatedly during morning monitoring; includes non-technical staff and admin maintainers.
- Quality bar: operational internal tool; should be dense, calm, reliable, Korean-first, and scannable. It does not need a marketing feel.

## Reconciled Findings

### Critical

1. Mobile/narrow layout is broken.
   - Evidence: `kha-monitor-home-390.png` and `kha-monitor-admin-390.png`.
   - Impact: staff using a narrow pywebview window, laptop split view, or high zoom cannot reach the article list without fighting the layout.
   - Source: accessibility-reviewer + heuristic-evaluator.
   - Fix: at small widths, replace the sidebar with a compact top toolbar or drawer. Collapse category filters into horizontal chips or a select/menu, hide auto-refresh metadata behind status text, and remove horizontal page overflow.

### Major

1. The primary screen does not speak the user's domain clearly enough.
   - Evidence: brand and H1 are `Monitor.` and `Overview`, while the task is "오늘 협회 관련 현안 확인".
   - Impact: first-time or non-technical staff must infer what matters.
   - Source: design-critic + heuristic-evaluator H2.
   - Fix: use Korean, task-specific hierarchy: e.g. "오늘의 협회 모니터링", "현안", "분야별 전체 소식", "보지 않은 기사".

2. Staff and admin modes share too much visual structure.
   - Evidence: `/` hides admin actions but keeps the same sidebar/header model; `/admin` adds icons with little mode labeling.
   - Impact: staff see a tool shell, admins see a content dashboard first; each role pays cognitive cost.
   - Source: design-critic + heuristic-evaluator H8.
   - Fix: make staff view a reading/triage surface; make admin view a maintenance console with clearly separated Settings, Sources, Diagnostics, Updates.

3. Important relevance signals are visually weak.
   - Evidence: "현안" count is a small badge inside category headers; core items rely on a slim colored rule and ordering.
   - Impact: repeat users can miss why an item is important or what changed.
   - Source: accessibility-reviewer + design-critic.
   - Fix: add a dedicated "현안" lane or compact summary strip at the top, with source, reason matched, and unread/new state.

4. Icon-only admin navigation is under-explained.
   - Evidence: home, gear, search, back icons have accessible labels but little visible text.
   - Impact: lower-confidence maintainers must hover/guess; touch users get less help.
   - Source: accessibility-reviewer + heuristic-evaluator H6.
   - Fix: use icon + label in admin mode, or a segmented navigation with "대시보드 / 설정 / 요약점검 / 직원화면".

### Minor

1. Missing PWA icon generates console noise.
   - Evidence: `/static/icon-192.png` returns 404 while `manifest.json` references it.
   - Fix: add the icon asset or remove the manifest icon entry.

2. Visual style is more editorial than operational.
   - Evidence: serif display type, decorative gradients, large white margins, and soft shadows are used across a dense monitoring tool.
   - Fix: keep the calm palette but reduce decoration, tighten spacing rhythm, and use a utilitarian Korean UI font for core controls.

3. The filter system depends too much on color.
   - Evidence: category identity is communicated by colored dots and text.
   - Fix: pair color with stable category labels, counts, and optionally small icons.

## What Works

- The three-column desktop content area is highly scannable for repeated monitoring.
- Category counts, "more" controls, unread filtering, and per-category grouping match the operational workflow.
- The employee-mode enhancement that moves core items upward is directionally right.

## Recommendation

Revise before treating this as a polished staff tool. The best first fix is the responsive/navigation structure: it removes the largest access blocker and also forces a cleaner separation between staff triage and admin maintenance.
