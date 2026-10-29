---
name: terminal-cockpit-design
description: Design or redesign a keyboard-first terminal cockpit for live operational data such as jobs, builds, traces, logs, or agents. Use when a TUI feels cluttered, when adding views or status labels, when writing a UX spec before implementation, or when users cannot tell what is working, what needs attention, or what to do next.
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

## Operating contract

**Purpose.** Produce a product and UX contract for a terminal cockpit before
implementation: information architecture, state language, interaction model,
responsive behavior, and acceptance criteria.

**Inputs.** The target users and their primary decisions; the data and evidence
available; the authority model (read-only monitor vs action-capable console);
the supported terminal sizes, platforms, and keyboard conventions; existing
architecture and tests. Inspect these first. Ask only for decisions that cannot
be inferred or discovered.

**Workflow.**

1. Write the three-question test in the user's terms and the product's authority
   model (observe only, or act with permissions/audit).
2. Inventory the records, evidence, related views, and actions. Decide what
   belongs in the default reading path vs on demand.
3. Define the screen budget and a small set of responsive breakpoints.
4. Define state/evidence language and the attention queue.
5. Define selection, live-update, navigation, and empty/error behavior.
6. Write acceptance criteria at real terminal sizes, including the core flow.
7. Hand the contract to implementation and testing; do not prescribe a renderer
   unless the constraints require it.

**Deliverable.** A spec with: audience/jobs; authority model; IA and screen
budget; list and inspector reading order; state/evidence table; interaction
table; responsive contract; visual roles; acceptance criteria; open questions.

**Completion.** A new user can identify working/attention items and explain why;
the core investigation is reachable in a few steps; every state has evidence and
a next action; the layout is specified at wide and compact sizes; acceptance
criteria are testable. A mockup alone is not completion.

## Reading this skill

- **Invariant** — required for correctness or trust: stable identity, honest
  status, evidence provenance, no stale substitution, accessible focus, clean
  exit.
- **Default** — a useful starting pattern: three-row shell, task-first rows,
  summary inspector, responsive breakpoints, key map. Adapt to the product.
- **Case study** — an Agenturm-specific decision or measurement. Context and
  limits are in [`references/agenturm-case-study.md`](references/agenturm-case-study.md).

Numbers in this skill are labeled **measured**, **example/default**, or
**proposed target** where they appear. Unlabeled examples are illustrative, not
universal requirements.

## When to use

- Designing a TUI for jobs, builds, agents, traces, queues, or infrastructure.
- The current screen "looks cluttered" and previous passes only changed colors.
- Adding a view, a filter, a status label, or an attention queue.
- Writing a spec that another agent will implement.
- Users confuse "quiet" with "stuck", or cannot explain why an item needs
  attention.
- A layout refactor is about to touch a working monitoring flow.

## The product contract

Decide the authority model before the layout:

- **Read-only monitor.** The cockpit observes and explains; it does not approve,
  reply, or launch work. This keeps the security boundary small. It is a valid
  default for monitoring, not a universal requirement.
- **Action-capable console.** If the app can mutate the observed system, the
  design must show authorization, confirmation, audit, and failure/rollback
  behavior. Do not copy a read-only interaction model into an action-capable
  product.

In both cases:

- **One source of truth.** The status classifier and collector own truth. The UI
  may shorten a label, but may not reclassify from appearance or elapsed time.
- **No invented content.** Never fabricate commands, progress, causes, timings,
  costs, or trace links.
- **Evidence before action.** Every attention item or mutation should link to
  what was observed and what will happen.

## The three-question test

A first screen passes only if a new user can do all three:

- In **5 seconds** (example target), identify which records are working and which
  need attention.
- In **30 seconds** (example target), follow the primary path
  `record → evidence → related item → back` without coaching.
- Explain **why** an item needs attention and identify one next action.

If the answer requires opening three views or reading raw output, the hierarchy
is wrong. These timings are proposed usability targets, not measurements.

## Information architecture

A three-row shell is a strong **default** for a monitoring cockpit:

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

Adapt it:

- **Navigation is not a filter.** View switching, record scope, and visibility
  filters are different concepts and belong on different controls.
- Choose the number of primary views from the user's jobs, not from Agenturm's
  four. Keep a labelled picker for secondary views when the count grows.
- Preserve the host's existing key conventions and `1–9` mappings where they
  exist. Do not invent a new keymap for a redesign.
- **One dominant list and one dominant inspector.** Do not give every panel equal
  visual weight.
- **One primary action per selection**, chosen from evidence:
  - failed action → inspect the failed action
  - explicit input wait → view the recorded request
  - linked trace → view the linked trace
  - otherwise → open activity/details
- **Remove duplicates.** One timestamp, one state, one count, one shortcut legend.

## Screen budget

Defaults for a dense monitoring TUI (adapt to the product):

- At 120×30, content should begin by row 9 so the workspace is not starved.
- At 80×24, show at least six two-line rows if rows are two lines.
- Two-cell outer gutters on wide screens; one on narrow.
- One-cell pane padding; one divider/gap per boundary.
- One border per content panel; no nested boxes around every field.
- No empty spacer rows. A control with `height: 1` plus several margin lines can
  consume four rows before content.
- If the top needs more room, take it from the **whole workspace**, not from the
  primary list.

These are example targets. Measure the actual content area after gutters and
chrome for the target terminal.

## Record list

Two-line rows are a strong default when records have a task and metadata:

```text
▸ Investigate checkout failure                    ! Failed
  Codex · checkout-api · GitHub request · 12s
```

- Line 1: selection marker, task, status aligned in a reserved right column.
- Line 2: runtime/project · latest short action · recorded age, lower contrast.
- IDs, model, token totals, and full paths belong in expanded detail.
- Title priority: meaningful source title → first nonempty user prompt →
  `Untitled <record>`. Normalize whitespace and clip by display cells.
- Do not use an LLM to name records during routine browsing unless that is an
  explicit product decision.

A default visibility policy for a monitoring cockpit is **Recent**: active or
attention records plus the single latest finished record. Offer `Active` and
`All` explicitly. This is a default, not a rule; an audit tool may need All by
default.

Ordering default:

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

Do not cap the primary list to make room for a header. Rebalance the whole
layout. If internal/review records are hidden by default, enforce that exclusion
everywhere: rows, connection counts, summaries, and traces.

## Inspector

A default reading order for a monitoring inspector (adapt the line counts and
fields to the product):

1. runtime/project breadcrumb
2. task title (at most two lines)
3. precise status + one sentence of evidence
4. latest relevant request/action + timestamp
5. up to a few preview lines of evidence, with an explicit truncation marker
6. one primary action + secondary activity/details links

The default inspector should be a **summary**. Raw commands, output, JSON, and
full transcripts belong behind an expand action or in the related view. Showing
raw evidence in the default view is a common source of "cluttered" feedback even
after spacing fixes.

Expanded detail adds:

- recorded user requests/prompts (bounded; state the order)
- recent recorded actions with timestamps and results
- full stored text, pretty-printed JSON, diffs, commands
- model/IDs/usage/provenance/analysis coverage
- explicit "Not captured" / "Not reported" when absent

Say "No linked trace recorded", not nothing. Say "Request: Not captured", not
"no request exists".

## Related-record views

Each related view owns a different question and keeps its own filters:

- **Activity/events:** chronological evidence with type, short action, and
  recorded time. Preserve filters and paged history; follow-live is explicit.
- **Tool/MCP calls:** server/tool, state, duration. Separate arguments, result,
  and error. Missing identity is "Not reported". Configured servers appear only
  after an observed call; aggregate metric counts with no per-call identity are
  shown separately.
- **Traces:** operation tree + selected-span evidence. Unknown duration stays
  unknown. A waterfall is optional only with reliable timestamps.
- **Host/processes:** process evidence, with exact record association shown
  separately. An open process is not proof of active work.
- **Metrics:** units, scope, reported coverage, missing-data labels. No invented
  price estimates or implied per-record attribution for service-wide metrics.
- **Findings/reviews:** queue with occurrence count and exact navigation to the
  source evidence.

Do not let a related view silently inherit a filter it does not show. If a
global scope is active, display it or summarize it.

## Status and trust

Present **record state** and **monitor freshness** separately. A collector delay
is not a work failure. The invariant: every status is a claim about evidence.

| Evidence | Default label |
|---|---|
| Records advancing, unfinished turn | Working |
| Exact process/children CPU or I/O progress | Processing / Tool running |
| Pending tool response during active work | Tool running |
| Unfinished turn, no recent progress, below stall criteria | Working (quiet) |
| Explicit approval/input wait | Waiting for approval / input |
| Live exact process, no progress for the stall threshold | Possibly stalled (warning, not proof) |
| Old unfinished turn, no exact live process | Unconfirmed |
| Collector backlog | Catching up; health unconfirmed |
| Collector read too old | Monitor delayed; health unconfirmed |
| Recorded completion/interruption/failure/idle/incomplete | Corresponding label |
| Insufficient lifecycle evidence | Unknown |

Rules:

- `Working` counts observed active turns, not open processes.
- `Live` describes the monitor connection, not every record.
- Silence alone is **quiet work** or **unknown**, never proof of a stall.
- Keep thresholds centralized and configurable; expose the rationale in detail.
- Every status has text as well as color.
- Unknown totals are "Not reported", never `0`/`$0`.
- An old terminal outcome must not override a newer started turn.

## Attention

An attention badge is a promise that the user can act. Each item needs:

1. **Source** — recorded failed action, aggregate telemetry, or lifecycle signal
   with no captured cause; collection issue vs tool issue.
2. **Evidence** — exact event/trace link when available.
3. **Next step** — inspect failed action, view request, open trace, or
   diagnostics.
4. **A way to clear it**:
   - **Mark reviewed** — scoped to this run/session; status/evidence unchanged.
   - **Dismiss** — persistent suppression by a bounded identity; remains in All
     history/traces; can be restored.
5. A new failure/trace/timestamp produces a new identity and may resurface.

Do not count ordinary tool waits as attention. Do not let a dismissed failure
disappear from evidence.

## Live updates

- Paint selection immediately from cached data; load detail in a worker.
- Capture selection/filter/scope **before** the read; discard stale replies by
  request generation, not only field equality.
- Never display the previous record's evidence under a new title.
- Keep existing evidence during same-record refresh; show "Refreshing" only for
  perceptible delay.
- When reading older activity, show `N new events · Latest` instead of jumping.
- Pin selected text while copying; explain when display is held.
- Distinguish `Loading`, `No records discovered`, `No matches`,
  `Source unavailable`, `Metadata-only capture`, `History truncated`, and
  `Disconnected`.
- Empty states offer the next action (diagnostics, clear search, start/connect),
  not demo data.

## Responsive contract

Use terminal **cells** (columns and rows), not pixels. The following is an
**example** contract; measure the actual child content area for the target app.

| Size | Default layout |
|---|---|
| ≥120 cols, ≥30 rows | list + right inspector (~38%, clamp 40–64 cells); two-line rows |
| 96–119 cols, ≥30 rows | split only if list ≥52 and inspector ≥36 cells fit; otherwise list/detail |
| 80–95 cols, or 18–29 rows | full-width list; Enter/expand opens full-width evidence; Esc returns |
| 60–79 cols, ≥18 rows | compact list; task/status may stack; reduced metadata; compact view switcher |
| <60 cols or <18 rows | minimal usable list + single-record detail; quiet size recommendation; search/palette/quit reachable |

- No application-level horizontal scrolling.
- Drop lowest-value columns first; keep subject and status. Full values remain in
  the inspector.
- Rewrap evidence after the actual pane width changes, not the app width.
- Resize preserves selection, expansion, query, and reading position by semantic
  anchor, not stale line offsets.
- Every essential action has a conventional-key fallback.

## Interaction model

Defaults for a keyboard-first cockpit; adapt to host conventions:

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
| 1–9 | Preserve existing view mappings |
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

## Worked example

**Input.** "Design a terminal monitor for a build farm. Operators need to see
which jobs are running, which need approval, and why a job failed. The app is
read-only. Terminals are 80×24 to 180×48."

**Output (excerpt).**

- Authority: read-only; no retry/cancel actions.
- Default view: `Recent` = running/attention jobs + latest finished job; `All`
  available.
- Rows: job name + state; project · latest step · age.
- Inspector: state + evidence; latest step; up to 6 lines; `Inspect failed step`
  or `Open log`.
- Attention: approval waits, possible stalls, recorded failures; each links to a
  step/log and can be reviewed/dismissed.
- Views: Jobs, Activity, Steps/Tools, Traces, Host, Metrics; the first four are
  primary, the rest behind a labelled picker.
- Breakpoints: side-by-side at ≥120×30; list/detail at 80–119; full-width
  evidence at <80.
- Acceptance: 3 running jobs visible at 80×24; failure → log → back in ≤3
  actions; collector delay not mistaken for job failure.

This is a complete shape for implementation; the exact keys and colors still
need validation in the target terminal.

## Acceptance criteria

- [ ] The product's authority model is explicit (read-only or action-capable).
- [ ] The three-question test passes on a real fixture.
- [ ] Content begins in the intended screen budget at the target sizes.
- [ ] Navigation, filters, and scope are separated.
- [ ] The list is task-first; the inspector is a summary; raw evidence is on demand.
- [ ] Status is evidence-based; monitor freshness is separate.
- [ ] Attention has cause, next step, review, and dismiss.
- [ ] The default history filter is deliberate, not copied by habit.
- [ ] Order freezes while navigating; selection is stable by ID.
- [ ] Responsive behavior is tested at wide, compact, and minimum sizes.
- [ ] Keyboard, mouse, copy, pause, diagnostics, export, quit work where present.
- [ ] Every status has text + color; contrast is verified.
- [ ] The core-flow regression includes all running records + evidence.
- [ ] Empty/loading/error states are honest.

## Failure modes

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Adding views to fix clutter | More surfaces, same hierarchy | Remove default information; deepen on demand |
| Restyling instead of restructuring | "Still cluttered" after every color pass | Change layout, spacing, and disclosure |
| Capping the primary list | Hides the data users came for | Rebalance global space |
| Hero logo in the header | Steals rows; terminal art rarely matches SVG | Text wordmark; logo belongs in README/site |
| Status from a timer | Long work looks stuck; stalls look finished | Evidence-based classifier |
| "Live" for every record | Implies progress that is not observed | Connection state + per-record evidence |
| `0` / `$0` for unknown | False precision | "Not reported" + completeness flag |
| Raw output in the default inspector | Dominates the screen | Summary + expand |
| Shortcut legend everywhere | Noise and contradiction | One contextual footer |
| Copying website pixels | Terminal cells cannot reproduce proportional type | Translate hierarchy, not pixels |
| Demo data in empty states | Teaches a false UI | Real empty state with next action |
| Read-only assumptions in an action UI | No authorization/audit model | Define permissions and audit first |

## Case study

Agenturm's specific decisions — read-only boundary, three-row shell, four primary
views, `1–7` keys, `Recent` default, 25% top overview, 80×24 targets, and the
exact palette/breakpoints — are recorded with context and limits in
[`references/agenturm-case-study.md`](references/agenturm-case-study.md). Use them
as an example, not as the definition of a cockpit.

The most expensive mistake was treating a layout redesign as a CSS task. It broke
the core multi-record read. The fix was a feature test, not another visual pass.

## Related skills

These are separate skills. Naming one here does **not** load it; use your host's
skill-loading mechanism.

- `textual-tui-engineering` — implement the contract in Textual.
- `tui-regression-testing` — test the contract at real sizes.
- `agent-session-status` — define the state/evidence model if the records are
  agents.

## Checklist

- [ ] Product authority model written.
- [ ] Three-question test passes on a real fixture.
- [ ] Screen budget and breakpoints are measured, not guessed.
- [ ] Navigation, filters, and scope separated.
- [ ] Task-first rows; summary inspector; raw evidence behind expand.
- [ ] Evidence-based status and separate collector health.
- [ ] Attention has cause, next step, review, and dismiss.
- [ ] Default history policy is deliberate.
- [ ] Order frozen while navigating; no list cap.
- [ ] Responsive contract tested at wide, compact, and minimum sizes.
- [ ] Keyboard/mouse/copy/pause/diagnostics/export/quit work where present.
- [ ] Every status has text + color; contrast verified.
- [ ] Core-flow regression includes all running records + evidence.
- [ ] Empty/loading/error states are honest.
