# Runtime notes and Agenturm status case study

These notes are **observations and case-study defaults**, not stable schemas or
universal thresholds. A runtime can change its storage at any release. Add a
versioned fixture before relying on any claim here.

## Agenturm's status defaults (case study)

Agenturm used one centralized classifier with:

- recent activity: **35 s** — a chosen default for its polling cadence, not a
  universal "working" threshold.
- exact process / collector freshness: **15 s** — chosen default.
- possible-stall consideration: **5 min** — chosen default.

It separated agent state from collector freshness, and required exact
session-to-process association before confirming a possible stall. These are
implementation choices; adapt them to the target runtime and product.

## Attention (case study)

- Attention included explicit input/approval waits, possible stalls, and recorded
  failures. Ordinary tool waits were not attention.
- `r` marked an item reviewed for the run; `x` dismissed a failure persistently by
  a bounded fingerprint. Dismissed items remained in All history and Traces.
- The failure fingerprint was a 64-hex hash over failure identity (session, trace,
  timestamp, kind), capped at 100 entries. It contained no prompt/search text.
- A new trace/timestamp produced a new fingerprint and could resurface.

## OpenCode

Observed during Agenturm compatibility work on **2026-10-24** against a local
OpenCode database. This was an observed historical schema, not a contract:

- V2 lifecycle lived in `session_v2`; legacy `session.time_updated` and the
  legacy `message` table could be stale.
- Recent conversations existed in `session_message`, including rows with **no
  matching parent `session` row**. A reader that required a parent silently hid
  active work.
- A session title could be empty; the first recorded user prompt was usable as a
  bounded task fallback.
- User prompt text had to be emitted into the activity stream; using it only for
  title fallback made the inspector claim "No user prompts."
- Metadata-only mode makes prompt text unavailable; say "Not captured."

Before using these claims, capture a synthetic fixture for the actual OpenCode
version under test. Do not open a developer's personal database in tests.

## Codex

Observed in Codex session JSONL during the same period; no stable versioned
schema was asserted:

- Handle `turn_aborted` and `final_answer` explicitly.
- Silence during a long tool call is not "No updates."
- Exact same-user session-file matching is required for process evidence.

## Pi

At the time of the work, Pi logs were observed under
`~/.pi/agent/sessions` or `$PI_CODING_AGENT_DIR/sessions`. Agenturm did not have a
native Pi reader in the earlier checkout; do not claim Pi support because a
process is running. Add a fixture for the Pi version under test.

## Google ADK / OpenTelemetry

Observed with Google ADK **2.13** during Agenturm CI:

- Tool type casing changed (`McpTool` vs `MCPTool`); match case-insensitively.
- Newer `execute_tool` spans omitted tool arguments/results. Do not invent them;
  mark them missing.
- The compatibility test asserted absence rather than fabricating content.

These are version-specific observations. Re-run the interoperability test against
the ADK release in use.

## Tie-break and identity notes

- Prefer an explicit monotonic turn/run sequence or start timestamp. If timestamps
  tie or arrive out of order, keep the newest started turn and record the
  ambiguity in diagnostics rather than silently picking one.
- A process match must include the exact session/run identity; a shared project
  directory or generic process name is insufficient.
- A collector's `last_success` only proves the poll succeeded. Track bytes,
  records, spans, and events to distinguish "poll succeeded" from "new data
  arrived."
