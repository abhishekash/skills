# Agenturm TUI skills

[![CI](https://github.com/abhishekash/skills/actions/workflows/ci.yml/badge.svg)](https://github.com/abhishekash/skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills: 9](https://img.shields.io/badge/skills-9-ffbd69)](skills)
[![Terminal UI: 4](https://img.shields.io/badge/terminal%20UI-4-dceb5a)](skills/terminal-ui)

**Four terminal UI skills, plus five supporting layers.**

Nine production skills extracted from the six-day effort to turn **Agenturm** — a
local, terminal-first monitor for Codex, Claude Code, OpenCode, Pi, and
OpenTelemetry agents — from a cluttered dashboard into a calm, evidence-first
cockpit.

The terminal UI is the point of this pack. The other skills exist to make what
the UI says **true**, affordable, and private.

The full story, including what failed and why, is in
**[docs/agenturm-tui-retrospective.md](docs/agenturm-tui-retrospective.md)**.

## Install

Fastest path, for any harness supported by the open skills CLI:

```bash
npx skills add abhishekash/skills
```

From a checkout, use the dependency-free installer (Python 3.10+; the skills
themselves are plain markdown):

```bash
git clone https://github.com/abhishekash/skills.git
cd skills
./install.sh --target opencode        # or claude-code, codex, cursor, gemini-cli, agents
```

By default the installer **copies** each skill directory and writes a
`.agenturm-skill` marker so `--remove` can identify what it owns. Use `--link` to
symlink, so `git pull` updates the installed skills in place.

| Command | Purpose |
|---|---|
| `./install.sh --target opencode` | Install to `~/.config/opencode/skills` |
| `./install.sh --target claude-code` | Install to `~/.claude/skills` |
| `./install.sh --all` | Install to every known target |
| `./install.sh --dest ./.agents/skills` | Install to an explicit directory |
| `./install.sh --target opencode --link` | Symlink instead of copy |
| `./install.sh --target opencode --force` | Replace existing destinations |
| `./install.sh --target opencode --dry-run` | Show the plan, change nothing |
| `./install.sh --list` | List skills and target paths |
| `./install.sh --target opencode --remove` | Remove installed copies/symlinks |

Claude Code can also install it as a plugin marketplace:

```text
/plugin marketplace add abhishekash/skills
/plugin install agenturm-tui@agenturm-skills
```

Codex plugin metadata is included at `.codex-plugin/plugin.json`; use your Codex
plugin/marketplace flow, or install directly to the shared `~/.agents/skills`
directory with the installer.

Manual fallback (copies each skill directory, not the category READMEs):

```bash
find skills -mindepth 2 -maxdepth 2 -type d \
  -exec cp -r {} ~/.config/opencode/skills/ \;
```

Restart the agent after installing so it discovers the new skills.

## Terminal UI

> **Start here if you are building a TUI.** These four skills cover the whole
> loop: design it, build it, test it, show it.

| Skill | What it gives you |
|---|---|
| **[terminal-cockpit-design](skills/terminal-ui/terminal-cockpit-design/SKILL.md)** | The product and UX contract: three-row shell, task-first rows, a summary inspector, evidence-based status, attention that can be cleared, responsive breakpoints, keyboard model, and acceptance criteria. |
| **[textual-tui-engineering](skills/terminal-ui/textual-tui-engineering/SKILL.md)** | The Textual implementation: `DataTable` projection, lazy tabs, stale-scope rejection, selection preservation, inspector reflow, evidence rendering, theme changes, and interrupt-safe shutdown. |
| **[tui-regression-testing](skills/terminal-ui/tui-regression-testing/SKILL.md)** | How to trust a TUI: core-flow tests, geometry assertions at real terminal sizes, keyboard/focus matrices, race tests, resource budgets, real-PTY shutdown, and demo-media checks. |
| **[terminal-demo-media](skills/terminal-ui/terminal-demo-media/SKILL.md)** | How to show it honestly: real captures, synthetic data, GitHub-legible sizing, canonical logo rendering, reproducible storyboards, and visual QA. |

Suggested order:

```text
terminal-cockpit-design
        ↓
textual-tui-engineering
        ↓
tui-regression-testing
        ↓
terminal-demo-media
```

The first two are the design/implementation pair. The third is not optional: the
Agenturm redesign looked better and silently broke the core multi-agent read. The
fourth is how the demo stays honest after the layout changes.

## Supporting layers

These make the terminal UI truthful, affordable, and private.

### Agent truth and data

The UI can only show what the reader and classifier can prove.

| Skill | What it gives you |
|---|---|
| **[agent-session-status](skills/agent-observability/agent-session-status/SKILL.md)** | Working vs quiet work vs waiting vs possible stall vs unconfirmed vs collector delay. Never infer a stall from silence; every attention item has a cause, next step, review, and dismiss. |
| **[local-agent-ingestion](skills/agent-observability/local-agent-ingestion/SKILL.md)** | Safe local readers: byte budgets before decode, fair resumption, oversized-record handling, deep-JSON containment, schema drift, parentless OpenCode sessions, and content-free diagnostics. |
| **[sqlite-telemetry-store](skills/agent-observability/sqlite-telemetry-store/SKILL.md)** | SQLite for live telemetry: indexes, exact aggregates, bounded evidence with completeness flags, incremental caches, writer-lock retention, and when DuckDB is not justified. |

### Operations

The monitor has to earn its place on the machine and respect what it sees.

| Skill | What it gives you |
|---|---|
| **[monitoring-performance-budgets](skills/operations/monitoring-performance-budgets/SKILL.md)** | Whole-app benchmarks, deterministic work limits, idle CPU/RSS/database reporting, and an honest answer to "should we rewrite it in Rust?" |
| **[local-first-monitoring-privacy](skills/operations/local-first-monitoring-privacy/SKILL.md)** | Loopback boundaries, owner-only files, redaction, metadata-only capture, allowlisted preferences, content-free diagnostics, previewed exports, and retention that admits it is logical deletion. |

## How the pack fits together

```text
TERMINAL UI
  terminal-cockpit-design      what the user sees and decides
  textual-tui-engineering      how it is built
  tui-regression-testing       how it stays correct
  terminal-demo-media          how it is shown

AGENT TRUTH AND DATA
  agent-session-status         what state can be claimed
  local-agent-ingestion        what evidence can be read
  sqlite-telemetry-store       what evidence can be kept

OPERATIONS
  monitoring-performance-budgets   what it costs
  local-first-monitoring-privacy   what it must not leak
```

A typical sequence:

1. Use **terminal-cockpit-design** to write the IA, state language, and
   acceptance criteria before touching CSS.
2. Use **textual-tui-engineering** to build the shell, tables, inspector, and
   live-update path.
3. Add **tui-regression-testing** from the first vertical slice — especially the
   core-flow test (all running agents + prompts + activity + MCP).
4. Use **agent-session-status**, **local-agent-ingestion**, and
   **sqlite-telemetry-store** for the data and truth layer.
5. Use **monitoring-performance-budgets** and
   **local-first-monitoring-privacy** before shipping.
6. Use **terminal-demo-media** only after the real UI is worth recording.

## What the pack optimizes for

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

## Pack layout

```text
skills/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── install.sh
├── skills.json
├── package.json
├── .claude-plugin/
├── .codex-plugin/
├── docs/
│   └── agenturm-tui-retrospective.md
├── scripts/
│   ├── install.py
│   └── validate_skills.py
└── skills/
    ├── terminal-ui/
    │   ├── README.md
    │   ├── terminal-cockpit-design/SKILL.md
    │   ├── textual-tui-engineering/SKILL.md
    │   ├── tui-regression-testing/SKILL.md
    │   └── terminal-demo-media/SKILL.md
    ├── agent-observability/
    │   ├── README.md
    │   ├── agent-session-status/SKILL.md
    │   ├── local-agent-ingestion/SKILL.md
    │   └── sqlite-telemetry-store/SKILL.md
    └── operations/
        ├── README.md
        ├── monitoring-performance-budgets/SKILL.md
        └── local-first-monitoring-privacy/SKILL.md
```

The installer flattens the categories into `<target>/<skill-name>/SKILL.md`,
because most agents expect a flat skills directory. The repository keeps the
categories for browsing; `skills.json` is the source of truth for paths and
featured status.

Each skill has flat `name` / `description` frontmatter written as a routing
trigger, so progressive disclosure works across harnesses. The nine skills are
intentionally separate: an agent loads only the skill relevant to the task, not a
3,000-line monolith.

## Packaging

| File | Purpose |
|---|---|
| `skills/<category>/<name>/SKILL.md` | The nine skills, in the portable Agent Skills format |
| `skills.json` | Manifest: version, categories, featured layer, skills, install targets |
| `install.sh` / `scripts/install.py` | Zero-dependency installer with copy/link, target detection, dry-run, force, remove |
| `.claude-plugin/plugin.json` | Claude Code plugin metadata |
| `.claude-plugin/marketplace.json` | Claude Code marketplace entry (`agenturm-tui@agenturm-skills`) |
| `.codex-plugin/plugin.json` | Codex plugin metadata and skill root |
| `package.json` | Repo metadata, validation/install scripts, Pi skill path |
| `CHANGELOG.md` | Versioned release notes |
| `scripts/validate_skills.py` | Frontmatter, naming, routing, links, categories, manifest consistency |
| `.github/workflows/ci.yml` | Validation, installer smoke test, real `npx skills` discovery |
| `.github/workflows/release.yml` | Builds and attaches a clean zip on `v*` tags |

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
./install.sh --target opencode --dest /tmp/skills-smoke --dry-run
```

The validator checks frontmatter, name/directory agreement, routing language,
required sections, cross-skill links, category/featured metadata, manifest and
version consistency, plugin skill lists, and target paths. CI also installs into
a temporary directory and verifies that the real open skills CLI discovers all
nine.

## License

MIT. Agenturm itself is MIT-licensed; these skills are an independent synthesis
of its engineering record.
