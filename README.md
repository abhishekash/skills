# Agenturm TUI skills

Nine production skills extracted from the six-day effort to turn **Agenturm** — a
local, terminal-first monitor for Codex, Claude Code, OpenCode, Pi, and
OpenTelemetry agents — from a cluttered dashboard into a calm, evidence-first
cockpit.

These are not generic "write a TUI" notes. They encode the specific failures,
reversals, measurements, tests, and design rules that came out of the work:
stale filters, false stall labels, hidden-pane reflow bugs, a logo that ate the
screen, a 25%-header change that was misunderstood, and a layout refactor that
silently broke the product's core feature.

The full story, including what failed and why, is in
**[docs/agenturm-tui-retrospective.md](docs/agenturm-tui-retrospective.md)**.

## The skills

| Skill | Use when |
|---|---|
| [terminal-cockpit-design](skills/terminal-cockpit-design/SKILL.md) | Designing or redesigning a keyboard-first TUI for live operational data: information hierarchy, status language, responsive layout, trust, and acceptance criteria |
| [textual-tui-engineering](skills/textual-tui-engineering/SKILL.md) | Implementing the cockpit in Textual: composition, `DataTable` projection, lazy views, stale-response invalidation, selection preservation, inspector reflow, shutdown |
| [tui-regression-testing](skills/tui-regression-testing/SKILL.md) | Testing a TUI without trusting screenshots: headless Pilot tests, core-flow regressions, resize/keyboard/race matrices, real-PTY shutdown tests |
| [agent-session-status](skills/agent-session-status/SKILL.md) | Showing whether agent sessions are working, waiting, stalled, finished, or unknown without inventing state from silence |
| [local-agent-ingestion](skills/local-agent-ingestion/SKILL.md) | Tailing local agent logs and reading agent databases safely: byte budgets, fair resumption, schema drift, content-free diagnostics |
| [sqlite-telemetry-store](skills/sqlite-telemetry-store/SKILL.md) | Storing live agent telemetry in SQLite: indexes, incremental derived data, exact aggregates, retention, and when not to add DuckDB |
| [monitoring-performance-budgets](skills/monitoring-performance-budgets/SKILL.md) | A local monitor feels heavy: whole-app benchmarks, deterministic budgets, and honest resource reporting before considering a rewrite |
| [local-first-monitoring-privacy](skills/local-first-monitoring-privacy/SKILL.md) | Designing capture, diagnostics, preferences, exports, and retention for a local monitor that sees prompts, tool output, and secrets |
| [terminal-demo-media](skills/terminal-demo-media/SKILL.md) | Producing an honest README/site/profile demo GIF or MP4 from the real TUI, including legibility and synthetic-data checks |

## How they fit together

```text
terminal-cockpit-design        product + UX contract
        │
        ├── textual-tui-engineering     implementation
        │           │
        │           └── tui-regression-testing
        │
        ├── agent-session-status        truth about session state
        ├── local-agent-ingestion       bounded data acquisition
        ├── sqlite-telemetry-store      durable local state
        ├── monitoring-performance-budgets
        ├── local-first-monitoring-privacy
        └── terminal-demo-media         honest release artifacts
```

A typical sequence:

1. Use **terminal-cockpit-design** to write the IA, state language, and
   acceptance criteria before touching CSS.
2. Use **textual-tui-engineering** to build the shell, tables, inspector, and
   live-update path.
3. Add **tui-regression-testing** from the first vertical slice — especially the
   core-flow test (all running agents + prompts + activity + MCP).
4. Use **agent-session-status**, **local-agent-ingestion**, **sqlite-telemetry-store**,
   and **local-first-monitoring-privacy** for the data and truth layer.
5. Use **monitoring-performance-budgets** before optimizing or rewriting.
6. Use **terminal-demo-media** only after the real UI is worth recording.

## What these skills optimize for

- **Truth over polish.** A status is a claim about evidence. Silence is not a
  stall; a poll success is not a new record; an unknown cost is not `$0`.
- **Reading surface over dashboard.** One list, one inspector, one next action.
  Raw output belongs behind `e`, not in the default view.
- **Space is global.** Do not cap the list to make room for chrome. Trade space
  between the header and the whole workspace.
- **Stable under live data.** Freeze order while navigating, preserve selection
  by stable ID, discard stale responses, and never move the row under the
  cursor.
- **Test the feature, not the layout.** Layout refactors broke multi-agent
  prompts and MCP visibility. The regression test is part of the design.
- **Measure the right thing.** Component budgets are not an RSS cap; a
  microbenchmark is not the app; 12 samples are not a production p95.

## Using the skills

Each skill is a `SKILL.md` with flat `name` / `description` frontmatter and a
routing-oriented description. Point any compatible harness at `skills/`, or copy
the directories into your skills path:

```bash
git clone https://github.com/abhishekash/skills.git
cp -r skills/skills/* ~/.config/opencode/skills/
```

With a skills installer that supports GitHub sources:

```bash
npx skills add abhishekash/skills
```

## Provenance and method

This repository was reconstructed on **2026-10-29** from:

- The OpenCode session database (`session_v2` + `session_message`) for the
  `agentic/agenturm` working directory: 28 sessions from 2026-10-21 to
  2026-10-29, with the TUI arc concentrated in ten of them (2026-10-21 and
  2026-10-24 → 2026-10-26).
- Agenturm's own authoritative docs: `docs/terminal-ux-spec.md`,
  `docs/engineering-review.md`, `docs/performance.md`, `docs/privacy.md`,
  `docs/branding.md`, and `docs/investigation-video.md`.
- The implementation and tests in `observatory/terminal_ui.py`,
  `observatory/terminal.py`, `observatory/feed_requests.py`,
  `observatory/session_status.py`, `observatory/ui_layout.py`,
  `observatory/ui_preferences.py`, `observatory/ui_export.py`,
  `observatory/ui_diagnostics.py`, and `observatory/shutdown.py`.
- Git history and merged PRs #9–#30.

There was no pre-existing `learnings/` file to import; the directory was empty.
The retrospective states which claims are measured, which are source-based, and
which remain unvalidated.

## Validation

```bash
python3 scripts/validate_skills.py
```

The validator checks frontmatter, name/directory agreement, routing language,
required sections, and cross-skill links. CI runs it on every push.

## License

MIT. Agenturm itself is MIT-licensed; these skills are an independent synthesis
of its engineering record.
