# Agenturm TUI test matrix (case study)

These are Agenturm's regression tests and target sizes. They are **examples**,
not a required template. The portable rules are in `SKILL.md`.

## Sizes used

- 180×48, 160×48, 140×42, 120×40, 120×30
- 100×30, 96×30
- 80×24
- 60×18, 50×18
- 120×18, 80×18

At 80×24 the suite required at least six two-line rows, a usable inspector on
demand, and reachable search/palette/quit.

## Core flow

`test_running_agents_keep_all_prompts_activity_and_mcp_calls_visible` created
three concurrent sessions (two Codex, one OpenCode), asserted all three in the
default Recent view, both prompts and current activity per inspector, all three
MCP calls, then repeated the prompt/activity assertions at 80×24 after `Enter`.

## Geometry

- Results and inspector share `region.y` on wide screens.
- Inspector width ≥36 cells.
- Controls begin below tabs.
- Inspector hidden at 80×24 until expand; full-width evidence after.
- 12 agents remain in the scrollable table; no artificial cap.
- Resize to 70 columns drops the `Updated` column but keeps task/state; resize
  back restores columns and the selected key.

## Races and state

- Prompts toggle during an in-flight poll.
- Scope captured before HTTP reads.
- Hidden view activation uses the latest snapshot.
- Selection preserved after refresh, resize, and tab switch.
- Empty start → rows arrive → order not frozen empty.
- Priority change queued until explicit Apply.
- Metrics exemplar restricted to selected instrument/history.
- A → B → A stale response rejected by generation.
- Hidden pane at width 0 does not cache one-character lines.

## Resource budgets

- Unchanged status does not request repaint.
- One changed cell does not repaint a row.
- Hidden views do no render work.
- Inventory cache used across refreshes; filter change bypasses it.
- Prefetch is parallel, deduplicated, and capped.
- Response cap rejected before JSON decode.
- Watcher/OpenCode/cache budgets.
- Derived refresh allocation bounded on a >16 MiB attribute fixture.

## Shutdown and media

- Real PTY: `q`, then Ctrl-C during blocked HTTP shutdown → exit 0, no traceback.
- Repeated interrupts during cleanup.
- `FakeFeed` implements every `Snapshot` field, including `activity_prompts`.
- Closing logo from canonical SVG; Prompts scene populated; even video
  dimensions; duration/size/frame count within budget.
