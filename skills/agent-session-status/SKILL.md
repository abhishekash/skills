---
name: agent-session-status
description: Classify and display live agent session state from evidence — working, quiet, waiting, stalled, finished, failed, or unknown — without inventing status from silence. Use when building an agent monitor, debugging false "stuck"/"idle" labels, showing attention queues, or supporting multiple agent runtimes.
---

# Agent session status

The most damaging status bug in a monitor is not a wrong color. It is a **false
claim**: "stuck" when the model is thinking, "done" when the turn was interrupted,
"working" because a process is open, or "no updates" because the collector is
behind.

Status is a conclusion from evidence. Encode the evidence hierarchy first, then
the labels.

## When to use

- Showing whether Codex, Claude Code, OpenCode, Pi, or OTel agents are working.
- Users ask "is it stuck or still processing?"
- A timer turns quiet sessions into "No updates".
- An attention badge has no explanation or no way to clear it.
- Adding a new runtime/reader and its schema differs.

## Evidence hierarchy

Evaluate in this order:

1. **Recorded lifecycle outcome** — completed, interrupted, error/failed,
   incomplete, idle, waiting. This is authoritative even when old.
2. **Explicit wait subtype** — approval vs user input vs tool response. Keep the
   reason; do not collapse all waits into "Waiting".
3. **Recent recorded activity** — records advancing within the recent window.
4. **Exact process evidence** — a same-user process matched to the exact session
   file, with CPU/I/O progress (including bounded children).
5. **Collector freshness/backlog** — a stale or backlogged collector invalidates
   live inferences.
6. **Silence** — if none of the above, the answer is quiet/unknown, not stalled.

Do not infer a match from a shared project directory, process name alone, or a
generic agent process. Match the exact session identity.

## State table

Use these labels (or equivalents) consistently:

| Evidence | Label | Active? | What the UI says |
|---|---|---|---|
| Records advancing, unfinished turn | Working | Yes | "Session records are advancing; the turn has not reported completion." |
| Exact process/children show CPU or I/O progress | Processing / Tool running | Yes | "The exact session's process or its children are using CPU / I/O." |
| Pending tool response during active work | Tool running | Yes | Tool name + "tool response pending" |
| Unfinished turn, no recent progress, below stall criteria | Working (quiet) | Yes | "A quiet model or tool call is not evidence of a stall." |
| Explicit approval/input wait | Waiting for approval / input | No | "Waiting for a response; reply in the agent's terminal." |
| Live exact process, no progress for ≥ stall threshold | Possibly stalled | No | "Warning, not proof; check the agent terminal." |
| Old unfinished turn, no exact live process | Unconfirmed | No | "Cannot distinguish a slow request from an exited agent." |
| Collector backlog | Catching up | No | "Unread records; live status is not yet reliable." |
| Collector read too old | Monitor delayed | No | "Agent health is unconfirmed." |
| Recorded completion/interruption/failure/idle/incomplete | Corresponding explicit label | No | Recorded outcome |
| Insufficient lifecycle evidence | Unknown | No | "Not enough evidence to classify." |

Agenturm's centralized thresholds:

- recent activity: **35 s**
- exact process / collector freshness: **15 s**
- possible-stall consideration: **5 min**

Keep thresholds in one module. The UI may shorten labels but must not reclassify
from elapsed time alone. Expose the rationale in detail.

## Active vs finished vs live

- `active` means an observed unfinished turn with recent progress or quiet work.
  It does not mean "a process exists".
- A freshly created transcript/header with no started turn is **not active**.
- Completed/interrupted/failed/idle sessions are not active.
- "Live" describes the **monitor connection**, not every session.
- Working count = active turns, with runtime names (e.g. `Codex 2 · OpenCode 1`).
- Live host process count is a separate Host view; do not add it to working.
- Working and attention counts are not additive with total session counts.

## Attention model

Attention is a queue of things a human may need to act on:

- explicit approval/input waits,
- possible stalls,
- recorded failures,
- (optionally) policy/blocking findings.

It is **not** every pending tool call, every idle session, or every old error.

Every attention item must answer:

1. **What happened?** Latest failed action, aggregate error count, or a lifecycle
   signal with no captured cause.
2. **Where is the evidence?** Exact event/span/trace link, or "No linked trace
   recorded."
3. **Is this the agent or the collector?** Separate `Catching up`/`Monitor
   delayed` from agent failure.
4. **What can I do?** Inspect failed call, view recorded request, open activity,
   open trace, or diagnostics/host.
5. **How do I clear it?**
   - `r` / Mark reviewed — session-scoped acknowledgement for this run; status
     and evidence unchanged.
   - `x` / Dismiss — persistent suppression by a bounded failure fingerprint;
     remains in All history and Traces; can be restored.
   - A new trace/timestamp gets a new fingerprint and may resurface.

Failure fingerprint: hash the failure identity (session + trace + timestamp +
kind), not the prompt or search. Bound the list (Agenturm: 100) and store only
the hash.

## Runtime quirks and traps

### OpenCode

- V2 stores lifecycle in `session_v2`; legacy `message`/`session.time_updated`
  can be stale.
- Recent conversations can exist in `session_message` **without a parent
  `session` row**. Do not require the parent or you silently hide active work.
- If the title is empty, use the first recorded user prompt (bounded/sanitized)
  as the task fallback. Corgi uses the initial request to generate a title; using
  the prompt directly is a simpler, local alternative.
- The reader must emit captured user messages into the activity stream; a prompt
  used only for title fallback will not appear in the inspector.
- In metadata-only mode, prompt text is unavailable; say "Not captured".

### Codex

- Handle `turn_aborted` and `final_answer` explicitly.
- A 35-second silence during a long tool call is not "No updates".
- Same-user session-file match is required for process evidence.

### Pi

- Older checkouts had no native Pi reader. Logs live under
  `~/.pi/agent/sessions` or `$PI_CODING_AGENT_DIR/sessions`.
- Do not claim Pi support just because a process is running.

### Google ADK / OTel

- Tool type casing can change (`McpTool` vs `MCPTool`). Match case-insensitively.
- Newer spans may omit tool arguments/results. Do not invent them; mark missing.
- Schema drift is normal; use partial-schema fixtures and safe fallbacks.

### General

- Do not blame a recent unrelated commit without reproducing the failure. In
  Agenturm, the OpenCode regression was a stale-parent-table issue, not the ADK
  commit it looked like.
- Poll success (`last_success_ns`) does not mean new records were read. Track
  bytes/records/spans/events.

## UI copy rules

- "Request: Not captured" — not "no prompt exists".
- "No linked trace recorded" — not a silent no-op.
- "Not reported" for unknown tokens/cost/model — not `0` or `$0`.
- "Possibly stalled — warning, not proof" — not "Stuck".
- "Catching up" / "Monitor delayed" — not "Failed".
- "Unconfirmed" when the process association is missing.
- "Completed" only when recorded; do not infer completion from silence.
- Keep recorded-event time and successful-collection time distinct.

## Test matrix

| Test | Expected |
|---|---|
| 120 s of silence, no process | Working (quiet), active |
| 900 s with exact process progress | Tool running / Processing, active |
| 900 s with live process, no progress | Possibly stalled, not active |
| 900 s, no/stale process | Unconfirmed, not active |
| Backlog > 0 | Catching up, health unconfirmed |
| Last collector read > 15 s | Monitor delayed |
| Explicit approval wait, 900 s | Waiting, not active |
| Completed while process alive | Completed, not active |
| Fresh header, no turn | Unknown/not active |
| OpenCode parentless messages | Sessions discovered with metadata |
| OpenCode no title | First prompt fallback |
| ADK `McpTool` | Evidence joined; missing args stay missing |

## Failure modes

| Anti-pattern | Result |
|---|---|
| A single 35 s timer drives status | Long calls look stuck; false "No updates" |
| Open process = working | Idle terminals inflate the working count |
| Silence = stalled | False alarms; users stop trusting attention |
| Collector delay = agent failure | Wrong diagnosis and wrong next step |
| All waits = "Waiting" | Loses approval vs input vs tool response |
| Error count without cause | User cannot decide what to do |
| "Mark reviewed" persisted as status change | Corrupts recorded truth |
| Dismissing deletes evidence | Destroys auditability |
| Generic "Not reported" everywhere | Noise; no actionable distinction |
| Inferring completion from no new records | False success |

## Case study

Agenturm's early UI changed every running session to "No updates" after 35
seconds. A long model/tool call looked dead. The replacement introduced
`Working (quiet)`, exact process progress, `Possibly stalled`, `Unconfirmed`,
and separate collector health. It also discovered OpenCode V2 sessions that had
been hidden because their parent `session` rows were missing. The user's test
was concrete: three agents were running; the app had to show exactly three,
with names, prompts, and current work.

The attention redesign came from a direct question: "the app says needs
attention — what can user do? how can they mention that is visited? also there is
hardly evidence on what went wrong, is it collection issue or tool issue?" The
answer became the attention contract above.

## Checklist

- [ ] Evidence hierarchy documented and centralized.
- [ ] Recorded lifecycle outranks timers and process guesses.
- [ ] Quiet work is active; possible stall is a warning, not proof.
- [ ] Collector backlog/delay separated from agent state.
- [ ] Explicit wait subtype preserved.
- [ ] Active count excludes idle processes and fresh headers.
- [ ] Working names surfaced, not just totals.
- [ ] Attention has cause, evidence, next step, review, and dismiss.
- [ ] Dismissal keeps evidence and uses bounded fingerprints.
- [ ] Unknown values are "Not reported", never zero.
- [ ] Runtime schema quirks covered by fixtures.
- [ ] Test matrix above passes.
