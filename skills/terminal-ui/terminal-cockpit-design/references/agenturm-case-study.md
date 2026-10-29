# Agenturm cockpit case study

These are Agenturm's decisions from the 2026 terminal redesign. They are
**case study**, not universal requirements. The reusable rules are in `SKILL.md`.

## Product context

Agenturm is a local, read-only monitor for Codex, Claude Code, OpenCode, Pi, and
OpenTelemetry agents. It observes sessions and evidence; it does not approve
requests, reply to agents, or launch them. That boundary was a deliberate
security/product decision and would not fit an action-capable console.

## Layout decisions

- **Three-row shell**: identity/health + working/attention counts; navigation;
  view controls. Content started by row 9 at the tested wide size.
- **Four primary views**: Agents, Activity, MCP Calls, Traces; Host, Metrics,
  Findings behind a labelled picker. `1–7` were preserved from the existing app.
- **Top overview**: after an initial attempt to cap the agent list at 8–10 rows,
  the final layout gave roughly 25% of the height to the overview and shared the
  rest between list and inspector. The list was not artificially capped.
- **Two frames**: a half-height status overview plus a separate Views panel.
- **History policy**: Agents opened in Recent (active/attention plus the latest
  finished session) because historical sessions dominated the first screen.
  Active and All remained explicit.
- **Inspector**: default was a summary (status, latest request/action, a few
  evidence lines); recorded prompts and recent actions appeared on expand.

## Responsive example targets

These were **proposed acceptance targets**, not universal breakpoints:

- ≥120×30: list + inspector, inspector about 38%, clamped 40–64 cells.
- 80×24: full-width list; expand for full-width evidence; at least six two-line
  rows.
- <60 columns or <18 rows: minimal list + single-record detail.

## Status and attention

- Agenturm used 35 s as its recent-activity window, 15 s for exact process /
  collector freshness, and 5 min before considering a possible stall. These are
  **Agenturm defaults**, centralized in one classifier; they are not universal
  thresholds.
- Attention combined explicit input waits, possible stalls, and recorded
  failures. Ordinary tool waits were not attention.
- `r` marked an item reviewed for the run; `x` dismissed a failure persistently
  by a bounded fingerprint. Dismissed items remained in All history and Traces.
- The UI distinguished a recorded failed action, aggregate telemetry, and a
  lifecycle-only error with no captured cause.

## Visual identity

- Default theme `Observation` (green-black canvas, yellow-green accent), with
  `Current`, `Bright`, `Dark`, and `Solarized` alternatives.
- Terminal identity was a one-line text wordmark. A multi-row tower logo was
  removed after it consumed too much space and could not reproduce the SVG mark
  at cell resolution.
- Essential text was checked at ≥4.5:1 contrast; status always had a text label.

## Known limits

- The numeric usability and latency targets were not fully measured against a
  multi-user study.
- Real-terminal coverage across all emulators, clipboard behavior, and
  screen-reader accessibility were not completed.
- The spec's 1,000-session stress fixture and 200-interaction latency
  distributions were not run.
