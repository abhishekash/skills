# Agenturm reader case study

These are Agenturm's measured reader numbers and historical runtime observations.
They are **case study**, not universal defaults. The invariants and portable
workflow are in `SKILL.md`.

## Measured reader behavior

- Before incremental imports: a poll after an unrelated database write cost about
  **860 ms** of reader CPU; a single changed tool cost about **852 ms**.
- After incremental imports: about **8 ms** and **14 ms** respectively.
- These were synthetic reader measurements, not whole-app benchmarks. They do not
  establish UI or receiver cost.

## Example/default budgets

- Watched JSONL: **8 MiB/poll**, **2 MiB/record**.
- OpenCode payloads: **2 MiB/record**, **16 MiB/poll** before transfer into
  Python.
- Lifecycle caches: **64 KiB/entry**, **1 MiB/map**, tracked bytes.
- Unchanged database lookback: **30 s**.
- Content caps: 8,000 characters per activity record, 2,000 per nested field, at
  most 60 entries.
- Discovery: recent-file and recent-session bounds with omission counts.

These were chosen for Agenturm's local monitor. A build-log reader or a shared
collector may need very different limits.

## Fair resumption

An early bounded implementation removed an oversized revision and retried, which
could re-import the same prefix forever. The final implementation used a fixed
size per-part digest plus a cursor, so repeated polls eventually reached later
parts, messages, and sessions. The fixture included a changed record behind the
cursor.

## Schema observations

Observed during Agenturm compatibility work on **2026-10-24**; these are
historical observations, not stable APIs:

- OpenCode V2 lifecycle in `session_v2`; legacy `session.time_updated`/`message`
  could be stale.
- Recent `session_message` rows could exist without a parent `session` row.
- Empty titles could fall back to the first recorded user prompt.
- User prompts had to be emitted as activity; title fallback alone did not put
  them in the inspector.
- Pi logs were observed under `~/.pi/agent/sessions` or
  `$PI_CODING_AGENT_DIR/sessions`; an earlier checkout had no Pi reader.
- Google ADK **2.13** used `McpTool` and omitted some tool arguments/results.
- Deep JSON and extreme timestamps could raise `RecursionError`/`OverflowError`,
  not only `ValueError`; the reader had to continue after them.

Recreate a synthetic fixture for the actual version under test. Do not use a
personal agent database as a fixture.
