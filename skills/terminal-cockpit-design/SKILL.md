---
name: terminal-cockpit-design
description: Design or redesign a keyboard-first terminal cockpit for live operational data such as agents, jobs, traces, logs, or a fleet. Use when a TUI feels cluttered, when adding views or status labels, when writing a UX spec before implementation, or when users cannot tell what is working, what needs attention, or what to do next.
---

# Terminal cockpit design

A terminal cockpit is a **reading surface for live evidence**, not a dashboard.
The user is usually watching work they did not start from this app, and needs to
answer three questions without leaving the terminal:

1. What is working?
2. What needs my attention?
3. What happened, and where is the evidence?

If a layout change makes those questions harder to answer, it is not a redesign.
It is decoration.

## When to use

- Designing a TUI for agents, jobs, builds, traces, queues, or infrastructure.
- The current screen "looks cluttered" and previous passes only changed colors.
- Adding a view, a filter, a status label, or an attention queue.
- Writing a spec that another agent will implement.
- Users confuse "quiet" with "stuck", or cannot explain why an item needs
  attention.
- A layout refactor is about to touch a working monitoring flow.

## The product contract

State it before designing:

- **Monitor, not controller.** The cockpit observes and explains; it does not
  approve actions, reply to agents, or launch work. This keeps the security
  boundary and the UI small.
- **Read-only by default.** The core workflow is
  `list → select → evidence → related record → back`.
- **One source of truth.** The status classifier and collector own truth. The UI
  may shorten a label, but may not reclassify from appearance or elapsed time.
- **No invented content.** Never fabricate commands, progress, causes, timings,
  costs, or trace links.

Write this contract into the first paragraph of the spec. It prevents feature
creep from being mistaken for polish.

## The three-question test

A first screen passes only if a new user can do all three:

- In **5 seconds**, identify which sessions are working and which need attention.
- In **30 seconds**, follow `session → failed call → trace → back` without
  coaching.
- Explain **why** an item needs attention and identify one next action.

If the answer requires opening three tabs or reading raw output, the hierarchy is
wrong.

## Information architecture

Use a three-row application shell, then content:

```text
row 1   identity / health / working + attention counts / connection + pause
row 2   navigation: primary views, secondary views, active destination
row 3   view controls: filter, scope, options
row 4   panel border
row 5   search
row 6   column headers
row 7+  primary rows
footer  contextual keys + freshness / collection problem
```

Rules:

- **Navigation is not a filter.** View switching, session scope, and visibility
  filters are three different concepts and belong on different controls.
- **Four primary views, the rest behind a labelled picker.** Keep `1–7`
  shortcuts if they already exist. At narrow widths, one labelled view picker is
  better than clipped tabs.
- **One dominant list and one dominant inspector.** Do not give every panel equal
  visual weight.
- **One primary action per selection**, chosen from evidence:
  - failed call → **Inspect failed call**
  - explicit input wait → **View recorded request**
  - linked trace → **View linked trace**
  - otherwise → **Open activity**
- **Remove duplicates.** One timestamp, one state, one count, one shortcut legend.

## Screen budget

At 120×30, content must begin by row 9. At 80×24, show at least six two-line
session rows. Chrome must not consume the workspace.

- Two-cell outer gutters on wide screens; one on narrow.
- One-cell pane padding; one divider/gap per boundary.
- One border per content panel; no nested boxes around every field.
- No empty spacer rows. `#controls` with three lines of vertical margin was a
  real cause of "cluttered" feedback.
- If the top needs more room, take it from the **whole workspace**, not from the
  primary list.

## Session list

Default to two-line task rows:

```text
▸ Investigate checkout failure                    ! Failed
  Codex · checkout-api · GitHub request · 12s
```

- Line 1: selection marker, task, status aligned in a reserved right column.
- Line 2: runtime · project · latest short action · recorded age, lower contrast.
- IDs, model, token totals, and full paths belong in expanded detail.
- Title priority: meaningful source title → first nonempty user prompt →
  `Untitled session · <runtime>`. Normalize whitespace and clip by display cells.
- Do not use an LLM to name sessions during routine browsing.

Default visibility: **Recent** = active/attention sessions + the single latest
finished session. Offer `Active` and `All` explicitly. Do not open on a wall of
history.

Ordering:

1. needs attention
2. working
3. other
4. completed history
5. newest recorded activity
6. stable ID

While the user is navigating, **freeze the order** and update cells in place.
Queue additions/reordering behind `List changed · Refresh order`. Apply on
explicit refresh or re-entry, preserving selection by stable ID. Never move the
row under the cursor.

**Never cap the list** to make room for a header. In Agenturm, capping the agent
list at 8–10 rows was rejected immediately; the correct fix was a 25% top
overview with list and inspector sharing the remaining height.

If internal review sessions are hidden by default, enforce that exclusion
everywhere: session rows, connection counts, summaries, and traces. Filtering
only the visible table is not enough; stored telemetry can reintroduce the same
session through another path.

## Inspector

Default reading order:

1. runtime / project breadcrumb
2. task title (at most two lines)
3. precise status + one sentence of evidence
4. latest relevant request/action + timestamp
5. up to six preview lines of evidence, with an explicit truncation marker
6. one primary action + secondary Activity/Details links

The default inspector is a **summary**. Raw commands, output, JSON, and full
transcripts belong behind `e` or in Activity. Showing raw evidence in the default
view was repeatedly described as "cluttered" even after spacing fixes.

Expanded detail adds:

- recorded user prompts (bounded, newest last or first — state which)
- recent recorded actions with timestamps and results
- full stored text, JSON pretty-printing, diffs, commands
- model, IDs, usage, provenance, analysis coverage
- explicit "Not captured" / "Not reported" when absent

Say "No linked trace recorded", not nothing. Say "Request: Not captured", not
"no prompt exists".

## Status and trust

Present **agent state** and **monitor freshness** separately. A collector delay
is not an agent failure.

| Evidence | Label |
|---|---|
| Records advancing, unfinished turn | Working |
| Exact process/children CPU or I/O progress | Processing |
| Pending tool response during active work | Tool running |
| Unfinished turn, no recent progress, below stall criteria | Working (quiet) |
| Explicit approval/input wait | Waiting for approval / input |
| Live exact process, no progress for the stall threshold | Possibly stalled (warning, not proof) |
| Old unfinished turn, no exact live process | Unconfirmed |
| Collector backlog | Catching up; agent health unconfirmed |
| Collector read too old | Monitor delayed; agent health unconfirmed |
| Recorded completion/interruption/failure/idle/incomplete | Corresponding label |
| Insufficient lifecycle evidence | Unknown |

Rules:

- `Working` counts observed active turns, not open processes.
- `Live` describes the monitor connection, not every session.
- Silence alone is **quiet work** or **unknown**, never proof of a stall.
- Keep thresholds centralized and explain them in detail.
- Every status has text as well as color.
- Unknown totals are "Not reported", never `0`/`$0`.

## Attention

An attention badge is a promise that the user can act. Each item needs:

1. **Source** — recorded failed action, aggregate telemetry, or lifecycle signal
   with no captured cause; collection issue vs tool issue.
2. **Evidence** — exact event/trace link when available.
3. **Next step** — inspect failed call, view request, open trace, or diagnostics.
4. **A way to clear it**:
   - **Mark reviewed** (`r`): session-scoped; status/evidence unchanged.
   - **Dismiss** (`x`): persistent suppression by a bounded fingerprint; remains
     in All history/Traces; can be restored.
5. A new failure/trace/timestamp produces a new identity and may resurface.

Do not count ordinary tool waits as attention. Do not let a dismissed failure
disappear from evidence.

## Live updates

- Paint selection immediately from cached data; load detail in a worker.
- Capture selection/filter/scope **before** the read; discard stale replies.
- Never display the previous session's evidence under a new title.
- Keep existing evidence during same-record refresh; show "Refreshing" only for
  perceptible delay.
- When reading older activity, show `N new events · Latest` instead of jumping.
- Pin selected text while copying; explain when display is held.
- Distinguish `Loading`, `No sessions discovered`, `No matches`,
  `Source unavailable`, `Metadata-only capture`, `History truncated`, and
  `Disconnected`.
- Empty states offer the next action (Diagnostics, Clear search, Start an agent),
  not demo data.

## Responsive contract

Use terminal **cells** (columns and rows), not pixels. Measure the actual child
content area after gutters.

| Size | Layout |
|---|---|
| ≥120 cols, ≥30 rows | list + right inspector (~38%, clamp 40–64 cells); two-line rows |
| 96–119 cols, ≥30 rows | split only if list ≥52 and inspector ≥36 cells fit; otherwise list/detail |
| 80–95 cols, or 18–29 rows | full-width list; Enter/`e` opens full-width evidence; Esc returns |
| 60–79 cols, ≥18 rows | compact list; task/status may stack; reduced metadata; compact view switcher |
| <60 cols or <18 rows | minimal usable list + single-record detail; quiet size recommendation; search/palette/quit reachable |

- No application-level horizontal scrolling.
- Drop lowest-value columns first; keep subject and status. Full values remain in
  the inspector.
- Rewrap evidence after the actual pane width changes, not the app width.
- Resize preserves selection, expansion, query, and reading position by semantic
  anchor, not stale line offsets.
- At 80×24, the identity, navigation, filters, headings, and status together use
  at most eight rows.

## Interaction model

| Action | Behavior |
|---|---|
| ↑/↓ | Move selection immediately; never wait for I/O |
| Enter | Open/focus selected evidence; compact layouts open full-screen detail |
| e | Toggle expanded detail and return to origin |
| Tab / Shift+Tab | Cycle visible controls in spatial order; clear focus cue |
| / | Focus search; preserve existing query |
| Ctrl+P | Fuzzy palette with current state and shortcuts |
| Esc | Consume one layer: overlay → text selection/search → expanded detail → linked nav |
| Alt+Left | Return to previous investigation location |
| 1–7 | Preserve existing view mappings |
| p | Freeze display; collection continues; show "Display paused" |
| c | Copy selection, otherwise current evidence |
| d | Diagnostics; return to original context |
| q | Exit through complete cleanup |

- Every advertised shortcut must work on every view where it is shown. A silent
  no-op is a bug; if no linked trace exists, say so.
- Typing in an input must never trigger application shortcuts.
- Pasted text is one input operation, not navigation.
- Mouse selection/wheel/click complement the keyboard; clicking a row selects it,
  opening detail uses a visible action or double-click.
- Preserve text selection while live data arrives.

Investigation history entries carry: view, scope, filters, selected stable ID,
pagination cursor, scroll anchor, focus target, and expansion state. Return
restores them even if new records arrived. If a record expired, explain its
absence and keep the closest valid context.

## Visual system

- Semantic roles, not raw colors: canvas, surface, panel, text, muted, primary,
  success, info, error, border, selection, focus.
- One accent for active navigation and focus; semantic colors for health/state.
- ≥4.5:1 contrast for essential text in every supplied theme; check ANSI fallback
  separately.
- Status identity must survive selection, monochrome, and theme changes.
- Bold only task titles, current view, and the most important evidence heading.
- Sentence case for actions/labels.
- Plain Unicode with ASCII alternatives; essential functions require no Nerd
  Font, emoji, graphics protocol, or custom font.
- Static "Working" text must communicate activity fully. No pulsing panels or
  continuous repaint.
- On theme change, recolor cached Rich strips and syntax backgrounds too.

## When taste is the blocker

Do not argue about a mark or header in the abstract. Render **10 options in the
real app**, at real terminal sizes, with real themes and fonts, and compare them
side by side. Agenturm's header-options generator produced wordmark, stacked,
caps, left-aligned, spaced-caps, wordmark-only, italic-tagline, amber-name,
prompt, and lavender-underline variants. The outcome was not one of the ten: the
user removed the logo entirely and kept a one-line wordmark. That decision was
only obvious after seeing the space cost in the real UI.

Rules for option reviews:

- use the real widget/theme/font, not a mock;
- include the compact and wide layouts;
- keep synthetic data identical across options;
- measure rows consumed and contrast, not just appearance;
- let the user pick by number, then wire the chosen option.

## Acceptance criteria

- [ ] At 120×30, content begins by row 9.
- [ ] At 80×24, ≥6 two-line rows are visible and search/palette/quit work.
- [ ] At 50×18, the list, detail, and view picker remain keyboard-accessible.
- [ ] Three concurrently running agents all appear with prompts, activity, and MCP
      calls at wide and 80×24 sizes.
- [ ] Twelve agents remain in the scrollable table; no artificial cap.
- [ ] Working/attention counts and the list agree.
- [ ] A quiet unfinished turn is "Working (quiet)", not "No updates".
- [ ] Collector delay is separate from agent failure.
- [ ] Every attention item explains cause + next step and can be reviewed or
      dismissed.
- [ ] Selection, scroll, and filters survive refresh, resize, and tab switch.
- [ ] No stale evidence under a new title.
- [ ] Every shortcut works or explains why it cannot.
- [ ] Contrast and status text pass in every theme.
- [ ] The demo uses synthetic data and matches the live UI.

## Failure modes

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Adding tabs to fix clutter | More surfaces, same hierarchy | Remove default information; deepen on demand |
| Restyling instead of restructuring | "Still cluttered" after every color pass | Change layout, spacing, and disclosure |
| Capping the primary list | Hides the data users came for | Rebalance global space |
| Hero logo in the header | Steals rows; terminal art rarely matches SVG | Text wordmark; logo belongs in README/site |
| Status from a timer | Long calls look stuck; stalls look finished | Evidence-based classifier |
| "Live" for every session | Implies progress that is not observed | Connection state + per-session evidence |
| `0` / `$0` for unknown | False precision | "Not reported" + completeness flag |
| Raw output in the default inspector | Dominates the screen | Summary + expand |
| Shortcut legend everywhere | Noise and contradiction | One contextual footer |
| Copying website pixels | Terminal cells cannot reproduce proportional type | Translate hierarchy, not pixels |
| Demo data in empty states | Teaches a false UI | Real empty state with next action |

## Case study

Agenturm's TUI went through five visible stages: dense table, polished header,
website-inspired split view, spec-driven three-row shell, then a corrected
25%-overview/two-frame layout. The changes that survived were not the prettiest
first drafts. They were the ones tied to a user question ("what is the agent
doing?", "is it stuck or processing?", "what can I do about attention?") and a
regression test.

The most expensive mistake was treating a layout redesign as a CSS task. It broke
the core multi-agent read. The fix was a feature test, not another visual pass.

## Checklist

- [ ] Product boundary written (monitor, not controller).
- [ ] Three-question test passes on a real fixture.
- [ ] Three-row shell with content starting by row 9 at 120×30.
- [ ] Navigation, filters, and scope separated.
- [ ] Task-first rows; summary inspector; raw evidence behind `e`.
- [ ] Evidence-based status and separate collector health.
- [ ] Attention has cause, next step, review, and dismiss.
- [ ] Recent default; no list cap; order frozen while navigating.
- [ ] Responsive contract tested at 180×48, 120×40, 100×30, 80×24, 60×18, 50×18.
- [ ] Keyboard, mouse, copy, pause, diagnostics, export, quit all work.
- [ ] Every status has text + color; contrast verified.
- [ ] Core-flow regression test includes all running agents + prompts + MCP.
- [ ] Empty/loading/error states are honest.
