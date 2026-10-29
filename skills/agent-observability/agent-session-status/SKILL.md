---
name: agent-session-status
description: Classify and display live agent session state from evidence — working, quiet, waiting, stalled, finished, failed, or unknown — without inventing status from silence. Use when building an agent monitor, debugging false "stuck"/"idle" labels, showing attention queues, or supporting multiple agent runtimes.
---

# Agent session status

The most damaging status bug in a monitor is not a wrong color. It is a **false
claim**: "stuck" when the model is thinking, "done" when the turn was interrupted,
"working" because a process is open, or "no updates" because the collector is
behind.

Status is a conclusion from evidence. Encode the evidence hierarchy, identity,
and precedence first — then the labels.

## Operating contract

**Purpose.** Produce a state/evidence model (and, when asked, its implementation)
that classifies agent work honestly across quiet periods, explicit waits,
collector delays, process evidence, and multiple runtimes.

**Inputs.** The runtime and schema(s) to support; session/turn identifiers; the
lifecycle events available; process/collector evidence (if any); the product's
attention policy; fixtures for ambiguous cases. Inspect the existing data before
inventing new fields.

**Workflow.**

1. Define session, turn/run, and process identity. State which ID owns which
   outcome.
2. List the recorded lifecycle evidence and its precedence.
3. Add freshness windows for records, exact process evidence, and the collector.
   Mark them configurable defaults, not universal truths.
4. Build the state table with an explicit uncertainty state.
5. Define attention: what qualifies, what evidence explains it, and how a user
   clears it without deleting evidence.
6. Write fixtures for the ambiguous transitions: quiet vs stalled, collector vs
   agent failure, old outcome vs new turn.
7. Implement the classifier once, expose its evidence string, and test the
   precedence rules.

**Deliverable.** A state/evidence model with precedence, identity, freshness,
uncertainty, attention behavior, and a test matrix; optionally a classifier and
its tests.

**Completion.** Every state maps to recorded evidence; silence never becomes a
stall by itself; collector delay is separate from agent failure; a newer started
turn overrides an older terminal outcome; attention has a cause, a next step, and
a clear action; ambiguous fixtures pass.

## Reading this skill

- **Invariant** — required for trust: identity, precedence, uncertainty, honest
  labels, no stale evidence, no fabricated totals/causes.
- **Default** — a starting point: labels, freshness windows, active-turn rules,
  attention composition. Adapt to the runtime and product.
- **Case study** — Agenturm's specific thresholds, labels, runtime observations,
  and attention fingerprint. See [`references/runtime-notes.md`](references/runtime-notes.md).

Numbers in this skill are **example/configurable defaults** unless explicitly
marked measured. They are not universal truth.

## When to use

- Showing whether Codex, Claude Code, OpenCode, Pi, or OTel agents are working.
- Users ask "is it stuck or still processing?"
- A timer turns quiet sessions into "No updates".
- An attention badge has no explanation or no way to clear it.
- Adding a new runtime/reader and its schema differs.
- A completed session is reappearing as running, or a new turn is being hidden by
  an old outcome.

## Identity: session, turn, process

Before classifying, define:

- **Session ID** — the conversation/workspace identity.
- **Turn/run ID** — the unit that starts, finishes, fails, or is interrupted. A
  session can contain many turns.
- **Process identity** — a same-user process (and bounded children) matched to
  the exact session file/record, with an observation timestamp.

Rules:

- A terminal outcome belongs to the turn it describes. **An old terminal outcome
  must not override a newer started turn.**
- A process match needs the exact session identity, not a shared project
  directory or a generic agent process.
- A fresh transcript/header is not an active turn.
- Session-level status is a rollup; do not let a completed old turn hide a new
  active one.

## Evidence hierarchy

Evaluate in this order:

1. **Newest recorded lifecycle transition** — started, waiting, completed,
   interrupted, error/failed, incomplete, idle, unknown. Apply it to its turn.
2. **Explicit wait subtype** — approval vs user input vs tool response. Keep the
   reason; do not collapse all waits into "Waiting".
3. **Recent recorded activity** — records advancing within the freshness window.
4. **Exact process evidence** — a same-user process matched to the exact
   session/turn, with CPU/I/O progress (including bounded children).
5. **Collector freshness/backlog** — a stale or backlogged collector invalidates
   live inferences.
6. **Silence** — if none of the above, the answer is quiet/unknown, not stalled.

Do not infer a match from a shared project directory, process name alone, or a
generic agent process.

## State model

These are **default labels**; adapt names to the product while keeping the
evidence distinctions.

| Evidence | Label | Active? | What the UI says |
|---|---|---|---|
| Newest turn started; records advancing | Working | Yes | "Session records are advancing; the turn has not reported completion." |
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

## Precedence rules

These are **invariants**:

1. **Newest turn wins.** A newer started turn resets the active state even if an
   older turn completed/failed.
2. **Recorded outcome beats inference.** A recorded completion is not overridden
   by an open process; an explicit wait is not turned into a stall by silence.
3. **Collector health is not agent health.** Backlog/delay produces `Catching up`
   or `Monitor delayed`, not `Failed`/`Stalled`.
4. **Process evidence is necessary for a confirmed stall.** No exact process
   association → `Unconfirmed`, not `Possibly stalled`.
5. **Silence is uncertainty.** Quiet work is active until the stall threshold and
   still requires process evidence to become a possible stall.
6. **Active means observed work.** An open process, a fresh header, or a
   completed turn is not active.
7. **Unknown is a valid answer.** Never fill a gap with a plausible label.

## Freshness windows

The following are **example/configurable defaults** from Agenturm, centralized in
one classifier:

- recent activity: **35 s**
- exact process / collector freshness: **15 s**
- possible-stall consideration: **5 min**

Adapt them to the runtime's polling cadence and the user's patience. Do not
derive status from elapsed time alone. Expose the rationale in detail.

## Attention

Attention is a queue of things a human may need to act on:

- explicit approval/input waits,
- possible stalls,
- recorded failures,
- optionally policy/blocking findings.

It is **not** every pending tool call, idle session, or old error.

Every attention item must answer:

1. **What happened?** Latest failed action, aggregate error count, or a lifecycle
   signal with no captured cause.
2. **Where is the evidence?** Exact event/span/trace link, or "No linked trace
   recorded."
3. **Is this the agent or the collector?** Separate `Catching up`/`Monitor
   delayed` from agent failure.
4. **What can I do?** Inspect failed action, view recorded request, open
   activity, open trace, or diagnostics.
5. **How do I clear it?**
   - **Mark reviewed** — scoped acknowledgement; status/evidence unchanged.
   - **Dismiss** — persistent suppression by a bounded identity; remains in All
     history/traces; can be restored.
   - A new failure/trace/timestamp gets a new identity and may resurface.

Fingerprint the failure identity (session + trace + timestamp + kind), not the
prompt or search. Bound the list and store only the hash. These are defaults; an
audit product may require explicit acknowledgement instead of dismissal.

## Runtime notes

Runtime schemas are observations, not stable APIs. Tested/observed version notes
live in [`references/runtime-notes.md`](references/runtime-notes.md). Read that
file before adding a reader for OpenCode, Codex, Pi, or Google ADK. Do not copy a
schema claim into a universal rule.

## Worked example

**Input.** A fixture has:

- session `job-7`, turn `turn-2` started 10 s ago;
- an older `turn-1` completed 5 min ago;
- no process evidence for `turn-2`;
- collector read succeeded 2 s ago, no backlog.

**Output.** `Working (quiet)` for `turn-2`, active. The old `Completed` for
`turn-1` is not the session's current state. The UI says "Records for the current
turn are recent; no completion has been reported." It does not say "Completed"
and does not say "Stalled."

**Second input.** `turn-2` has no records for 6 min, but an exact process is
alive with CPU/I/O progress 2 s ago. **Output.** `Processing`/`Tool running`,
active. Silence plus exact progress is not a stall.

**Third input.** `turn-2` has no records for 6 min, the collector's last read is
30 s old, and there is no exact process match. **Output.** `Monitor delayed` or
`Unconfirmed`; never `Failed`.

## Tests for ambiguous cases

| Test | Expected |
|---|---|
| Newer started turn + older completed turn | Newer turn active; old outcome ignored |
| Quiet 120 s, no process | Working (quiet), active |
| Long tool call with exact process progress | Tool running/Processing, active |
| 900 s, live process, no progress | Possibly stalled, not active |
| 900 s, no/stale process | Unconfirmed, not active |
| Backlog > 0 | Catching up, health unconfirmed |
| Collector read older than freshness window | Monitor delayed |
| Explicit approval wait, 900 s | Waiting, not active |
| Completed while process alive | Completed, not active |
| Fresh header, no turn | Unknown/not active |
| Two turns with out-of-order timestamps | Newest start wins; test the tie-break |
| Process visible for another session | Not matched; no confirmed stall |

## Failure modes

| Anti-pattern | Result |
|---|---|
| A single timer drives status | Long work looks stuck; false "No updates" |
| Open process = working | Idle terminals inflate the working count |
| Silence = stalled | False alarms; users stop trusting attention |
| Collector delay = agent failure | Wrong diagnosis and wrong next step |
| Old outcome overrides new turn | Completed session hides active work |
| All waits = "Waiting" | Loses approval vs input vs tool response |
| Error count without cause | User cannot decide what to do |
| "Mark reviewed" persisted as status change | Corrupts recorded truth |
| Dismissing deletes evidence | Destroys auditability |
| Generic "Not reported" everywhere | Noise; no actionable distinction |
| Inferring completion from no new records | False success |

## Case study

Agenturm's 35 s/15 s/5 min thresholds, labels, attention fingerprint (64-hex,
cap 100), and runtime observations are in
[`references/runtime-notes.md`](references/runtime-notes.md). They are a concrete
implementation, not a universal contract.

## Related skills

These are separate skills. Naming one here does **not** load it; use your host's
skill-loading mechanism.

- `terminal-cockpit-design` — decide how status and attention appear in the UI.
- `local-agent-ingestion` — produce the bounded evidence this classifier reads.
- `tui-regression-testing` — test the ambiguous transitions and stale responses.

## Checklist

- [ ] Session, turn, and process identity defined.
- [ ] Newest turn overrides older terminal outcome.
- [ ] Evidence hierarchy and precedence documented.
- [ ] Quiet work is active; possible stall requires process evidence.
- [ ] Collector backlog/delay separated from agent state.
- [ ] Explicit wait subtype preserved.
- [ ] Active count excludes idle processes and fresh headers.
- [ ] Working names surfaced, not just totals.
- [ ] Attention has cause, evidence, next step, review, and dismiss.
- [ ] Dismissal keeps evidence and uses a bounded identity.
- [ ] Unknown values are "Not reported", never zero.
- [ ] Runtime schema quirks are versioned fixtures, not universal claims.
- [ ] Ambiguous test matrix passes.
