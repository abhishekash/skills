# Agenturm TUI retrospective

**What we actually did, what broke, what survived, and why the skills look the
way they do.**

- Period: 2026-10-20 → 2026-10-26 (TUI work concentrated 2026-10-21 and 10-24 → 10-26)
- Product: Agenturm — a local, terminal-first monitor for Codex, Claude Code,
  OpenCode, Pi, and OpenTelemetry agents
- Stack: Python 3.11+, Textual 8.2.x, Rich, SQLite, a loopback HTTP receiver
- Evidence: 28 OpenCode sessions, Agenturm docs/code/tests, git history, PRs #9–#30

This document is the honest narrative behind the nine skills. It deliberately
keeps the dead ends. The useful part of the record is not "we made a nice TUI";
it is why the first several attempts were not nice, and which changes actually
moved the needle.

---

## 1. Method

There was no pre-written learnings file. `agentic/learnings/` was empty.

I reconstructed the work from:

1. `~/.local/share/opencode/opencode.db` → `session_v2` + `session_message` for
   every session whose directory was `agentic/agenturm`.
2. The user messages, assistant messages, tool calls, and final summaries in
   those sessions (bulk tool output excluded).
3. Agenturm's authoritative docs, especially `docs/terminal-ux-spec.md` and
   `docs/engineering-review.md`.
4. The final implementation and its tests.
5. `git log`, merged PR titles/dates, and commit diffs.

The TUI work was not one clean project. It was four overlapping efforts:

- aesthetic/identity iterations,
- a performance investigation,
- a correctness/trust hardening pass,
- and a full UX redesign that was then corrected by user feedback.

The most valuable lessons came from the corrections, not the first designs.

---

## 2. Executive summary

Six things explain almost every TUI decision that survived:

1. **The screen was cluttered because it showed everything at once, not because
   the colors were wrong.** The fix was information hierarchy — task-first rows,
   a short inspector, raw evidence behind `e` — not another theme.
2. **The product's core feature is a live multi-agent read.** All running agents,
   their prompts, their current activity, and their MCP calls must remain visible
   through every layout change. A redesign broke this; the fix included an
   end-to-end feature test, not just CSS.
3. **Status is a claim about evidence, not a timer.** The old UI turned every
   session into "No updates" after 35 seconds. The replacement separates
   recorded lifecycle, exact process progress, collector health, explicit waits,
   quiet work, possible stalls, and unknowns.
4. **Live data requires identity, not row positions.** Selection, filters,
   pagination, and scroll must survive refreshes by stable IDs and explicit
   scopes. Stale responses must be discarded, and the row under the cursor must
   not move.
5. **Local monitoring is a resource and privacy product.** The reader was doing
   ~405 MB of logical reads in 10 seconds and rebuilding spans on every database
   change. Fixing redundant work took Agenturm from ~37% to ~12% of one CPU core.
   The machine's real problem was a separate OOM/restart cycle, not Agenturm.
6. **Tests must encode behavior at real terminal sizes.** Headless Textual tests
   at 180×48, 120×40, 100×40, 80×24, 60×18, and 50×18 caught bugs that unit
   tests and screenshots missed: stale widths, hidden-pane one-character
   wrapping, lost trace selection, focus loss, and rows dropped after an empty
   start.

---

## 3. The arc

| Phase | Date | User signal | What was actually wrong | What changed |
|---|---|---|---|---|
| A. Dense dashboard | before 10-21 | "still below par", "remove waiting on", "improve readability" | Cramped header, clipped stats, oversized scope, task/detail buried under metadata | Responsive summary, task/detail space, removed "Waiting on" column, muted missing tasks |
| B. Performance | 10-21 | "machine overloaded", "should make this in rust" | ~39% of one core; OpenCode reader reprocessed all recent records on any DB change; UI polled every second and repainted unchanged cells and hidden views | Incremental imports, 2 s polling, changed-cell updates, lazy work; ~37% → ~12% CPU, 106 → 94 MiB |
| C. Identity | 10-21 | "horrible icon", "take way too much space", "remove the logo completely" | Terminal block-art logo was malformed, inconsistent with the SVG, and consumed rows | 10 real-app header options generated, then logo removed entirely; one-line text wordmark |
| D. Hardening | 10-24 | "deep dive… find ways to improve", "fix all issues" | Full traces loaded into Python, stale filters, wrong exemplars, unbounded receiver threads, unbounded watcher reads, prune/refresh race, permissive DB umask | Exact SQL aggregates, bounded evidence, completeness flags, 32-worker bounded receiver with deadlines, 4-worker/16-prefetch feed, lazy views, diagnostics, exports, allowlisted preferences |
| E. Runtime truth | 10-24 | "running agents not shown", "should be smart enough to find if it is stuck" | OpenCode `session_message` rows had no parent `session`; `session.time_updated` was stale; Pi had no reader; 35 s silence was treated as "No updates" | OpenCode V2 + parentless-session discovery, Pi reader, first-prompt fallback, evidence-based status, separate collector health |
| F. Shutdown | 10-24 → 10-25 | repeated Ctrl-C tracebacks | Three separate unbounded joins: local-agent discovery, derived-refresh worker, HTTP server shutdown | Bounded joins, then whole-cleanup SIGINT shielding with handler restoration; real-PTY `q` + Ctrl-C test |
| G. Redesign spec | 10-25 | "serious issue with UI/UX… give a spec" | Header had competing layers; shortcuts before navigation; filters mixed with view switching; excess vertical margins | Three-row top, navigation separate from controls, task list + inspector, bottom contextual footer, responsive contract |
| H. Implementation + correction | 10-25 → 10-26 | "still cluttered", "last change was bad", "you break working feature", "is it so hard to work on spacing" | First implementation capped the list to 8–10 rows; header spacing was still wrong; default inspector still showed too much; core multi-agent flow regressed | 25% top overview, no list cap, two frames (overview + Views), Recent default, summary inspector, expanded prompts/actions, spacing pass, Enter/e/click |
| I. Attention truth | 10-26 | "needs attention — what can user do?", "hardly evidence what went wrong" | Error was inferred from lifecycle with no cause; no way to acknowledge/dismiss; same failure repeated forever | Cause source + next step + trace link; `r` mark reviewed for run; `x` persistent dismissal by bounded fingerprint; evidence retained in All/Traces |
| J. Final polish | 10-26 | "intermittently see one character per line" | Hidden inspector updated at width 0 and cached one-character lines | Skip hidden-pane renders; rebuild on activation; regression test |

---

## 4. What broke, and the fix that survived

### 4.1 Layout and rendering

| Symptom | Root cause | Fix | Regression |
|---|---|---|---|
| Header cramped; stats clipped; scope oversized | Four summary cards + tagline + status + legend all competed for one wide row | Responsive summary; details in tooltips; compact labels; remove tagline from top | Branding/resize tests at 200, 120, 80, 50 columns |
| Session rows unreadable | Four-column table buried the task under IDs and metadata | Two-line task rows: task/status first, runtime/project/action/age second | `task_rows_filters_palette...` |
| Rows still packed | Previous pass restyled, did not add separation | Blank row between sessions; deliberate control groups; inspector section spacing | `test_compact_overview...`, spacing assertions |
| "Still very cluttered" | Default inspector showed raw output, duplicate activity table, unconfigured AI button | Default inspector reduced to status + latest request/action; raw content only under `e`/Activity | `test_long_commands_and_output_are_never_in_the_default_overview` |
| Row previews wrapped at old width after resize | Table reflow used stale column widths | Set `column_widths` before rebuilding rows; recompute previews after actual width | `test_resize_rewraps_previews...` |
| Inspector stuck at one character per line | Update arrived while pane hidden; reported width 0; RichLog cached 1-cell strips | Do not render hidden panes; reflow and rebuild when visible | `test_hidden_pane...` (issue #24 / PR #30) |
| List capped to 8–10 rows | User initially asked not to see more than 8–10 agents, but the height cap reduced the agent frame; then asked for a 25% top overview instead | Remove cap; give top 25%, share remaining height between list and inspector | `test_compact_overview_leaves_full_height...` |

### 4.2 Live data, selection, and navigation

| Symptom | Root cause | Fix | Regression |
|---|---|---|---|
| A new Prompts filter switched back mid-poll | In-flight response from the old filter published after the new selection | Capture an immutable `FeedScope`; compare before publish; discard stale; show "Filtering…" | `test_prompt_toggle_during_poll_discards_old_snapshot` |
| Metric `t` opened another instrument's trace | Exemplar resolved across all metrics/history | Resolve exemplars only inside the selected instrument and loaded history | `test_metric_shortcut_ignores_other_instruments...` |
| Selected session evidence disappeared | Feed papered over missing selection with the first trace | Keep pinned selection; explicit empty/absence states; stable IDs | Trace navigation + hold-selected tests |
| Row under cursor moved during live updates | List re-sorted on every refresh | Freeze order while navigating; queue "Order changed · Apply"; apply on explicit refresh/re-entry | `test_live_priority_changes_queue_order...` |
| Rows arriving after an empty start were dropped | Order-freeze logic treated the initial empty order as authoritative | Detect empty→non-empty transition and rebuild order | `test_sessions_arriving_after_empty_start...` |
| Hidden views were rebuilt every refresh | All tabs rendered unconditionally | Render only the active tab; refresh hidden view on activation from latest snapshot | `test_hidden_views_do_no_render_work...` |
| Hidden review sessions reappeared | Stored OTLP summaries re-added reviews that the visible table filtered out | Exclude reviews consistently from rows, connections, and summaries | `test_hidden_reviews_are_not_reintroduced_from_stored_otlp_summaries` |
| Span selection lost after tab switch | Tree cursor initialized via a deferred paint callback that raced activation | Build line mapping before moving cursor; preserve selected span ID | `test_span_cursor_is_initialized...`, `test_keyboard_tab_navigation...` |

### 4.3 Truth and status

| Symptom | Root cause | Fix | Regression |
|---|---|---|---|
| "No updates" after 35 s during a long tool call | A single recency threshold was used as a status | Separate recent records, exact process progress, explicit waits, collector freshness, 5-minute stall warning | `test_quiet_processing_does_not_become_no_updates...` |
| Quiet work looked stalled | No distinction between "no new records" and "no work" | `Working (quiet)`; only warn after sustained no progress with a live exact process | `test_stall_is_a_warning...` |
| Collector delay looked like agent failure | Monitor freshness was mixed into session lifecycle | Separate `Catching up` / `Monitor delayed` from agent state | `test_collector_delay_or_backlog...` |
| OpenCode sessions missing | Reader relied on stale `session.time_updated` and required a parent `session` row | Discover from recent `session_message`; support parentless conversations; read `session_v2` | OpenCode live verification (20 sessions) + unit tests |
| Pi sessions missing | No Pi reader existed | Read `~/.pi/agent/sessions` or `$PI_CODING_AGENT_DIR/sessions` | Pi discovery tests |
| "Not reported" everywhere | Unknown metadata was rendered as a generic placeholder | Use first recorded user prompt as task fallback; keep "Not captured" only when genuinely absent | `test_default_inspector_exposes_recorded_user_request...` |
| Error label had no explanation | Lifecycle said "Error"; no recorded cause | Inspector distinguishes failed action / aggregate telemetry / lifecycle-only signal; links trace and Diagnostics | `test_running_agents...`, attention tests |
| Attention could not be cleared | No review/dismiss model | `r` mark reviewed for this run; `x` dismiss persistently by bounded fingerprint; retain evidence | `test_dismissals_persist_only_bounded_fingerprints` |

### 4.4 Performance and resources

| Symptom | Root cause | Fix |
|---|---|---|
| 12–39% of one CPU core while monitoring | OpenCode reader reread recent sessions and rebuilt spans on any DB change; UI polled every 1 s and repainted unchanged cells/hidden views | Incremental import, 2 s poll, changed-cell updates, lazy views |
| 405 MB logical reads / 10 s | Repeated full scans of recent records | Process only changed records; cache inventory/derived reads |
| Full trace processing memory spikes | `Store._refresh_summaries_locked` loaded complete traces and finding logs | Exact SQL aggregates; bounded evidence windows (256 records, 64 KiB, 2 MiB, 128 groups) |
| Receiver could be held by slow clients | Unbounded threads; socket timeout alone does not bind slow-drip bodies | 32 workers admitted before thread creation; 503 overload; absolute header/body deadlines; shutdown interrupts sockets |
| Watcher could read entire backlog | Read-to-EOF per poll | 8 MiB/poll, 2 MiB/record; discard oversized through newline across polls |
| OpenCode could starve later records | Removing an oversized revision caused the same prefix to be retried forever | 2 MiB/record, 16 MiB/poll, per-part digest + fair cursor; changed record behind cursor preserved |
| Caches retained ~1 GiB in pathological IDs | Count-only bounds | 64 KiB/entry, 1 MiB/map, tracked bytes, safe eviction |
| Prune/refresh race resurrected deleted caches | Refresh and pruning could interleave across Store instances/processes | SQLite writer lock (`BEGIN IMMEDIATE`) around read/replace; cross-Store regression |
| DB briefly world-readable | SQLite created the file before permissions were tightened | Create owner-only before SQLite opens |

### 4.5 Identity and release media

| Symptom | Root cause | Fix |
|---|---|---|
| Logo "horrible", "looks like something NSFW", "tower looks weird" | Hand-drawn terminal block art could not reproduce the SVG's circular deck and lens | Generated 10 options in the real app; then removed the logo entirely and used a one-line text wordmark |
| Logo took too much vertical space | Multi-row masthead | One content row; tagline only when space permits; no Nerd Font/image protocol |
| Demo GIF logo wrong | The malformed mark was baked into terminal captures, not GIF scaling | Remove the block-art mark; compositor renders the closing tower directly from canonical `icon.svg` |
| README demo illegible | 148-column capture was scaled down into GitHub's ~840 px content column | Capture at 100×42 and compose a README-specific frame that fills the width; link the full-resolution video |
| Demo Prompts scene empty | `FakeFeed` did not implement the new `Snapshot.activity_prompts` contract | Set it in the synthetic feed; add a media regression |
| Video stretched by one pixel | Odd-height canvas | Force even dimensions before H.264 encode |

### 4.6 Shutdown

Three tracebacks appeared at different layers:

1. `LocalAgents.close()` joined its discovery thread without a timeout; Ctrl-C
   during the join escaped.
2. `Store.close()` joined the derived-refresh thread the same way.
3. `socketserver.shutdown()` itself could be interrupted while waiting.

The durable fix was not another local `try/except`. It was
`complete_cleanup(*callbacks)`:

- run cleanup in reverse order,
- ignore SIGINT only during cleanup,
- restore the previous handler even if a closer fails,
- use bounded joins,
- keep later cleanup steps running after one fails,
- verify with a real PTY: press `q`, send Ctrl-C during blocked HTTP shutdown,
  expect exit code 0 and no traceback.

**Lesson:** interrupt safety is a property of the whole cleanup sequence, not of
each individual `join()`.

---

## 5. Design decisions that survived

### 5.1 Product boundary

Agenturm is a **monitor, not a controller**. It does not approve requests, reply
to agents, or launch them. That boundary keeps the security surface small and
the UI focused on reading evidence. Proposed chat/approval/remediation features
were explicitly deferred until monitoring was reliable.

### 5.2 Information architecture

At 120×30, content starts by row 9:

```text
row 1  identity + working/attention counts + connection/pause
row 2  navigation (Agents, Activity, MCP Calls, Traces, More/Other views)
row 3  view controls (Recent/Active/All, session scope, options)
row 4  panel border
row 5  search
row 6  column headers
row 7+ task rows
```

- Four primary views; Host/Metrics/Findings behind a visibly labelled picker.
- `1–7` shortcuts preserved.
- One dominant list + one inspector.
- Task-first two-line rows; status right-aligned; metadata lower contrast.
- One primary action chosen from evidence:
  - failed call → **Inspect failed call**
  - explicit input wait → **View recorded request**
  - linked trace → **View linked trace**
  - otherwise → **Open activity**
- Default inspector is a summary. Expanded detail is a reading surface.

### 5.3 No list cap

The first attempt to give the header more room capped the list at 8–10 agents,
following the user's "I don't want to see more than 8–10 agents" request. The
user then rejected the reduced agent frame and asked for a 25% top overview:
"I don't want to reduce the agent frame, just trade off to make space for the
top. Use 25% from top." The correct trade was global: top 25%, then list and
inspector share the remaining height to the same bottom edge. Twelve agents
remain in the scrollable table; the viewport is not artificially truncated.

**Rule:** to make room, rebalance the whole layout, never amputate the primary
data list.

### 5.4 Default view

Agents opens in **Recent**: active/attention sessions plus the single latest
finished session. `Active` and `All` are explicit alternatives. Historical
sessions do not dominate the first screen.

### 5.5 Status language

- Agent state and monitor freshness are separate.
- Working count = observed active turns, not open processes.
- "Live" describes the monitor connection, not every session.
- "Needs attention" includes explicit input waits, possible stalls, and recorded
  failures — not ordinary tool waits.
- Every status has a text label as well as color.
- No fabricated command, progress, timing, or cause.

### 5.6 Interaction

- `↑/↓` moves selection immediately from cached data; never waits for I/O.
- `Enter` and `e` both open the inspector; clicking a row also opens it.
- `Tab`/`Shift+Tab` follow spatial order.
- `/` preserves the existing query.
- `Esc` consumes one layer per press: overlay → text selection/search → expanded
  detail → linked navigation.
- `Alt+←` returns to the exact origin, including scroll and expansion.
- `p` pauses **display only**; collection continues.
- `d` opens content-free diagnostics; `x` opens a frozen export preview.
- Typing in search never triggers application shortcuts.

### 5.7 Visual system

- One border per panel; one separator per boundary.
- 2-cell outer gutters on wide screens, 1-cell on narrow.
- Bold only task titles, current view, and the most important heading.
- Sentence case for actions and labels.
- Semantic color roles, including evidence/syntax colors; theme changes must
  recolor cached Rich strips.
- ≥4.5:1 contrast for essential text; color never the sole indicator.
- Plain Unicode with ASCII fallbacks; no Nerd Font, emoji, image protocol, or
  animation required.
- Working text communicates activity without motion.

---

## 6. Decisions that were reversed

| First attempt | Why it failed | Replacement |
|---|---|---|
| Terminal tower logo in the masthead | Malformed at cell resolution, inconsistent with SVG, consumed 5–6 rows | One-line text wordmark; logo lives in README/site only |
| All shortcuts on top, then beside scope, then bottom | Duplicated keys, overcrowded the header, confused location | Context-sensitive bottom footer; top legend only after redesign exploration |
| Four metric cards + tagline + health in header | Competed with the primary task list | Compact working/attention counts; details in tooltips/Metrics |
| Cap agent list at 8–10 rows | A height cap shrinks the primary data frame even when the user still needs it | 25% top overview; no list cap; shared remaining height |
| Default inspector with raw output and duplicate activity table | "Still cluttered"; raw content dominated | Summary first; prompts/actions only on expand |
| "More" on a separate controls row | Looked like a filter, not navigation | More/Other views beside the tabs (or one labelled view picker at <76 cols) |
| Rewrite in Rust to reduce CPU | The bottleneck was redundant work, not Python | Incremental imports + polling/repaint fixes; Rust deferred until profiling justifies it |
| Treat 35 s of silence as "No updates" | Long model/tool calls are legitimately quiet | Quiet work vs possible stall vs collector delay vs unconfirmed |
| Add more tabs/features to address clutter | Increased the reading burden | Reduce default information; deepen on demand |

---

## 7. Performance: what was measured, and what it means

### 7.1 The first investigation (2026-10-21)

- Agenturm: ~121 MiB RAM, ~12–39% of one CPU core, ~405 MB logical reads in 10 s
  (only ~1.2 MB physical).
- The machine was under severe memory pressure: ~14/15 GiB used, all 4 GiB swap
  occupied, `kswapd0` busy, and 19–20 ChatGPT/Codex processes killed by the OOM
  killer in ~12 minutes.
- Agenturm was not the main cause of the system overload, but it was doing
  avoidable repeated work.

Fix and result:

| Metric | Before | After |
|---|---:|---:|
| Agenturm CPU (one core) | ~37% | ~12% |
| Agenturm RAM | 106 MiB | 94 MiB |
| Terminal CPU | ~50% | ~7% |
| OpenCode poll after unrelated DB write | ~860 ms | ~8 ms |
| OpenCode poll with one changed tool | ~852 ms | ~14 ms |

These are samples, not a controlled distribution. The win came from doing less
work, not from a faster language.

### 7.2 The whole-app benchmark (2026-10-24)

`scripts/benchmark_app.py` ran fresh processes with temporary SQLite databases,
a loopback receiver, the HTTP feed, and a headless Textual UI; all views were
warmed before measuring. Workloads: 200 spans; 20,000 spans; 2,000 spans with
8 KiB payloads.

| Workload | Refresh median / p95 | Idle CPU | Peak RSS | Database |
|---|---:|---:|---:|---:|
| 10 traces × 20 spans | 29.9 / 64.6 ms | 6.7% | 68.0 MiB | 0.30 MiB |
| 2 traces × 10,000 spans | 55.6 / 120.9 ms | 9.6% | 69.7 MiB | 9.34 MiB |
| 2 traces × 1,000 spans, 8 KiB payloads | 48.7 / 122.6 ms | 8.9% | 81.8 MiB | 17.42 MiB |

The prior `HEAD` large workload measured 69.1 / 180.6 ms, 11.2% idle CPU,
68.8 MiB RSS, and a 5.35 MiB database. The refresh improvement is modest; the
database grew because of a 1.45 MiB trace-start index and a 2.54 MiB per-span
statistics cache. That is a real storage trade, not a free optimization.

Honest limits:

- 12 refresh samples are not a reliable production p95.
- Headless UI CPU/RSS does not establish real-terminal rendering cost.
- RSS includes Python, Textual, SQLite, and temporary allocations; it is not
  telemetry size.
- Derived refresh still scans whole traces inside SQLite and holds the writer
  lock. It is bounded in Python memory, not in total database work.
- The native-reader microbenchmark measures only OpenCode polling; it is not
  whole-app performance.

### 7.3 Ordered trace page

Adding `(trace_id, start_ns, span_id)` changed a synthetic 50,000-span ordered
page from **143.8 ms → 0.52 ms median** over 25 repetitions. This isolates the
query, not HTTP latency, ingestion, or end-to-end responsiveness.

### 7.4 Deterministic budgets that replaced timing assertions

| Component | Budget |
|---|---|
| Feed reads | 4 workers, 16 prefetch slots per refresh |
| Receiver response | 16 MiB before JSON decode |
| Receiver concurrency | 32 admitted workers; immediate 503 over limit |
| Receiver deadlines | 10 s headers, 15 s body, absolute (not inactivity-only) |
| Live feed poll | 2 s |
| Inventory/findings cache | 5 s unless scope changes |
| Watched JSONL | 8 MiB/poll, 2 MiB/record |
| OpenCode payload | 2 MiB/record, 16 MiB/poll, fair resumption |
| Native lifecycle caches | 64 KiB/entry, 1 MiB/map |
| Derived evidence | 256 records, 64 KiB/record, 2 MiB window, 128 groups |
| AI summary evidence | 30 matching events |
| UI refresh timer | 0.5 s, but repaint only on change |

These are component budgets, not a fixed whole-process RSS ceiling.

---

## 8. Truth model: status, attention, and evidence

### 8.1 The classifier

Centralized in `observatory/session_status.py`:

- recent activity: 35 s
- exact process / collector freshness: 15 s
- possible-stall consideration: 5 minutes

The UI may shorten labels but may not reclassify lifecycle evidence from
appearance or elapsed time alone.

| Evidence | Presentation |
|---|---|
| Records advancing, unfinished turn | Working |
| Exact process/children CPU or I/O progress | Processing |
| Pending tool response during active work | Tool running |
| Unfinished turn, no recent progress, below stall criteria | Working (quiet) |
| Explicit approval/input wait | Waiting for approval / input |
| Live exact process, no progress for ≥5 min | Possibly stalled — warning, not proof |
| Old unfinished turn, no exact live process | Unconfirmed |
| Collector backlog | Catching up; agent health unconfirmed |
| Collector read too old | Monitor delayed; agent health unconfirmed |
| Recorded completion/interruption/failure/idle/incomplete | Corresponding explicit label |
| Insufficient lifecycle evidence | Unknown |

### 8.2 Counts

- **Working agents** = observed active turns, with runtime names.
- **Needs attention** = explicit input waits + possible stalls + recorded
  failures, excluding dismissed fingerprints and reviewed sessions.
- **Live host processes** = exact processes, shown separately in Host.
- Normal tool waits are not attention.
- Working and attention counts are not additive with total session counts.

### 8.3 Attention actions

The user's question was the design brief: "the app says needs attention — what
can user do? how can they mention that is visited? also there is hardly evidence
on what went wrong, is it collection issue or tool issue?"

The resulting model:

1. **Explain the source** of the claim: recorded failed action, aggregate run
   telemetry, or lifecycle-only signal with no captured cause.
2. **Give one next step**: inspect failed call, view recorded request, open
   linked trace, or check Diagnostics/Host.
3. **Mark reviewed** (`r`): acknowledge for this run; status and evidence
   unchanged.
4. **Dismiss** (`x`): persistent suppression by a bounded fingerprint; still
   visible in All history and Traces; can be restored.
5. A new failure/trace/timestamp produces a new fingerprint and can resurface.
6. Do not claim a cause when only a lifecycle signal exists.

Fingerprints are 64-hex hashes, capped at 100, and contain no session IDs or
search text.

---

## 9. Testing: what actually caught the bugs

The suite grew from ~142 tests at the start of the performance work to 300+
during the redesign. The valuable tests were not the count; they were the shape:

### 9.1 Core-flow test

After a layout change broke the product's main feature, the user said: "core
feature is all agents running are show with all the prompts and what is going now
with MCP etc. add a feature test."

`test_running_agents_keep_all_prompts_activity_and_mcp_calls_visible` now:

- creates three concurrently running agents (Codex ×2, OpenCode ×1),
- asserts all three appear in the default Recent view,
- asserts each inspector shows both recorded prompts and current activity,
- asserts MCP calls from all three sessions appear in MCP Calls,
- repeats the prompt/activity assertions at 80×24 after pressing Enter.

This test is the guardrail against "beautiful but useless."

### 9.2 Headless geometry

Tests assert semantic geometry, not pixel snapshots:

- results panel and inspector share `region.y` on wide screens;
- inspector width ≥ 36 cells;
- controls begin below the tabs;
- at 80×24 the inspector is hidden until `e`/Enter;
- 12 agents remain in the table and share the same bottom edge;
- resize to 70 columns drops the `Updated` column but keeps task/state;
- selection and column visibility restore on resize back.

### 9.3 Race and state tests

- Prompts toggle during an in-flight poll.
- Scope captured before HTTP reads.
- Hidden view activation uses the latest snapshot.
- Selection preserved after refresh, resize, and tab switch.
- Empty-start → rows arrive → order not frozen empty.
- Order changes queued until explicit Apply.
- Metrics exemplar restricted to selected instrument/history.
- Stale inspector never shows the previous session's evidence.

### 9.4 Resource tests

- Unchanged status cell does not request repaint.
- One changed cell does not repaint the entire row.
- Hidden views do no render work.
- Inventory queries cached between live refreshes; filter changes bypass cache.
- Feed prefetch parallel, deduplicated, bounded.
- Watcher/OpenCode/cache byte budgets.
- Derived refresh allocation bounded on a >16 MiB attribute trace.

### 9.5 Real terminal tests

Headless tests cannot prove:

- terminal restoration,
- clipboard behavior,
- Ctrl-C during shutdown,
- actual wrapping/contrast in a terminal emulator.

The shutdown fix was verified in a real PTY/subprocess: press `q`, send Ctrl-C
while HTTP shutdown is blocked, expect exit 0 and no traceback. Repeated
interrupts during cleanup were tested too.

### 9.6 Media tests

`FakeFeed` is part of the contract. When the app added
`Snapshot.activity_prompts`, the synthetic demo feed did not, so the Prompts
scene was stuck on "Filtering…". The fix was both a feed change and a media
regression. A demo that does not implement the current snapshot contract is a
false demo.

---

## 10. Privacy and local-first boundaries

What the final design does:

- Binds the receiver to `127.0.0.1` by default. `OBSERVATORY_TOKEN` is an
  optional shared secret for non-loopback/TLS-proxied use, not a login system or
  encryption.
- Creates the SQLite database with owner-only permissions before SQLite opens it.
- Redacts recognizable credentials and selected sensitive structured fields on a
  best-effort basis before storage. Excludes private/encrypted reasoning, binary
  payloads, process environments, and credential files.
- Caps captured content: 8,000 characters per activity record, 2,000 per nested
  field, at most 60 entries.
- Offers `--metadata-only` for future native ingestion and `--no-local-agents` to
  disable discovery. Neither erases already-stored content.
- Persists only an allowlist of UI preferences: theme, view, Reviews/Prompts/
  error flags, dismissed-attention fingerprints. No searches, session IDs,
  selections, endpoints, or credentials. `AGENTURM_UI_PREFERENCES=0` disables
  reads and writes.
- Shows content-free diagnostics: source paths, read counters, backlog, skipped
  records, schema errors. No raw events, credentials, or exception text.
- Exports only the selected record after a frozen privacy preview and explicit
  confirmation; creates owner-only files with `O_EXCL`; refuses overwrite;
  removes a partial file on failure.
- States that retention is logical deletion, not secure erasure; free pages,
  journals, snapshots, and backups may retain content. Native source logs are
  separate.
- Treats token/cost totals as reported telemetry, not a billing statement.
- Uses `Not reported` / `Not captured` rather than zero or an invented value.

---

## 11. What remains unvalidated

Be suspicious of any claim that the TUI is "done."

- The spec's numeric performance targets (keypress p95 ≤ 50 ms, selection to
  cached inspector ≤ 100 ms, resize ≤ 150 ms, idle CPU ≤ 1%, etc.) were
  **proposed**, not measured against 200 interactions on a reference machine.
- The 1,000-session presentation workload and multi-user usability study
  (4/5 participants, 5-second identification, 30-second investigation) were not
  run.
- Real-terminal coverage across Kitty/WezTerm/VTE, Terminal.app/iTerm2/Ghostty,
  Windows Terminal, tmux/SSH, 256-color/monochrome, and mixed-width Unicode was
  not completed.
- Clipboard behavior and screen-reader accessibility were not verified across
  platforms.
- The derived refresh still holds SQLite's writer lock and scans whole traces.
- Findings/search evidence is windowed; older evidence can be absent and is
  marked incomplete.
- Receiver limits protect a local collector; they are not internet-facing
  hardening.
- Exports are previewed but are not a redaction pass.
- Headless UI measurements do not establish real terminal rendering cost.

The skills encode the validated parts and explicitly mark these limits.

---

## 12. Reusable rules

1. **One list, one inspector, one next action.** If everything is visible,
   nothing is readable.
2. **Default to a summary; put raw evidence behind `e`.** The first screen is for
   orientation, not forensics.
3. **Task first, metadata second.** The user identifies a session by what it is
   doing, not by its ID.
4. **Never cap the primary list to make room for chrome.** Rebalance the global
   layout.
5. **Separate navigation from filters.** A view picker is not a filter.
6. **One fact, one place.** Remove duplicate timestamps, state, counts, and
   legends.
7. **Freeze order while the user is navigating.** Queue changes; apply on
   explicit refresh or re-entry; preserve selection by stable ID.
8. **Capture scope before I/O; discard stale responses.** Never let an old poll
   overwrite a new filter.
9. **Never show the previous selection's evidence under a new title.** Use a
   loading/absence state instead.
10. **Status is evidence, not elapsed time.** Silence is quiet work or unknown,
    not a stall.
11. **Separate agent health from monitor freshness.** A collector delay is not an
    agent failure.
12. **Every attention item needs a cause, a next step, and a way to clear it.**
    Review is session-scoped; dismissal is persistent and keeps the evidence.
13. **Unknown is a first-class value.** `Not reported` is better than `0`,
    `$0`, or a guess.
14. **A shortcut that silently does nothing is a bug.** Either act on every view
    or say why it cannot.
15. **Colors support labels; they never replace them.** Test contrast in every
    theme, including cached Rich strips.
16. **Measure whole-app behavior before optimizing.** Find repeated work before
    changing languages.
17. **Bound bytes, not just counts.** A single malformed record can defeat a
    count-based budget.
18. **Fairness matters in bounded readers.** A large record must not starve every
    later record forever.
19. **Interrupt safety is a whole-cleanup property.** Shield the sequence,
    restore the handler, bound every join, and test with a real SIGINT.
20. **Test the core feature through the redesign.** A layout can be beautiful
    and still break the product.

---

## 13. Source map

Key sessions (OpenCode `session_v2`; times local):

| Date | Session | What it contributed |
|---|---|---|
| 10-21 07:51 | Feedback: Results Still Below Par (`...jH55PP`) | Header crowding, removed "Waiting on", task/detail readability |
| 10-21 08:07 | Investigating Agenturm resource usage and system overload (`...AMkEjM`) | CPU/RSS measurements, OpenCode repeated work, system OOM context, Rust decision |
| 10-21 09:35 | Continuing session from saved file (`...2CE7Dt`) | 37% → 12% CPU, stale installed copy vs checkout, PR #9 |
| 10-21 12:43 | Polish Agenturm terminal logo to match GitHub README (`...D39qlH`) | Logo/space failure, 10 real-app options, text-only wordmark, `t` bug, shortcut placement |
| 10-24 12:53 | Agenturm deep dive and improvement plan (`...aTnZOu`) | Multi-agent review, hardening, lazy views, diagnostics/export, OpenCode/Pi, status, shutdown, website-inspired layout |
| 10-24 12:53 | Review terminal user experience (`...v9D1cq`) | Stale Prompts filter, wrong exemplar, stale preview widths, session activity index |
| 10-24 13:05 | Optimize terminal rendering UX (`...JgcXPn`) | Lazy views, column drop order, preferences, export, hidden-view test adjustments |
| 10-24 13:05 | Bound native session ingestion (`...uxz9Br`) | 8/2 MiB watcher, 2/16 MiB OpenCode, fair cursor, cache byte budgets, deep JSON |
| 10-24 13:05 | Bound large trace processing (`...NTErTo`) | Exact SQL aggregates, bounded evidence, completeness flags, writer lock |
| 10-24 13:05 | Harden receiver resource limits (`...1RBg5f`) | 32 workers, 503, absolute deadlines, shutdown |
| 10-25 20:35 | Agenturm terminal UI/UX redesign specification (`...iwQCyW`) | Three-row shell, bottom footer, 25% overview, two frames, core-flow test, attention UX, hidden-pane bug |
| 10-24 12:56 | Finding 10 deep developer problems in r/AI_Agents | Context only (not TUI implementation) |

Supporting documents:

- `docs/terminal-ux-spec.md` — IA, responsive contract, interaction, status/trust,
  performance acceptance, terminal coverage
- `docs/engineering-review.md` — bug catalog, measured limits, remaining
  architecture work
- `docs/performance.md` — workloads, budgets, benchmark caveats
- `docs/privacy.md` — capture, redaction, metadata-only, preferences, exports,
  retention
- `docs/branding.md` — tower identity, Alpine Ember/Observation palettes,
  text-only terminal identity
- `docs/investigation-video.md` — real-capture demo pipeline, 100-column README
  capture, synthetic data

---

## 14. How this maps to the skills

| Retrospective learning | Skill |
|---|---|
| IA, hierarchy, status language, responsive contract, attention model | `terminal-cockpit-design` |
| Textual composition, DataTable projection, lazy views, stale scopes, reflow, shutdown | `textual-tui-engineering` |
| Core-flow regression, geometry assertions, race matrix, real PTY | `tui-regression-testing` |
| Lifecycle/process/collector evidence, quiet vs stalled, runtime quirks | `agent-session-status` |
| Watcher/DB bounds, fair resumption, schema drift, diagnostics | `local-agent-ingestion` |
| SQLite indexes, derived data, writer lock, retention, DuckDB decision | `sqlite-telemetry-store` |
| Whole-app benchmark, deterministic budgets, honest reporting | `monitoring-performance-budgets` |
| Loopback, redaction, prefs, diagnostics, export, retention | `local-first-monitoring-privacy` |
| Real captures, 100-column README, canonical SVG, synthetic-data checks | `terminal-demo-media` |

The common thread: **make the UI honest about what it knows, and make the
engineering honest about what it measured.**
