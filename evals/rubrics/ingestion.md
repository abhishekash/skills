# Ingestion rubric

Independent scoring for `local-agent-ingestion` tasks. Primary = functional
correctness and regressions.

## Functional gates (must pass)

| Check | Pass condition |
|---|---|
| Partial record | Kept across polls, completed later; suffix not misparsed |
| Oversized record | Discarded through newline; counted; no suffix parse |
| Malformed record | Skipped; following valid record ingested; loop alive |
| Deep JSON / extreme timestamp | Contained; loop alive; valid tail ingested |
| Fair backlog | Repeated polls reach all tail records; head cannot starve forever |
| Changed record behind cursor | Detected/ingested on a later poll |
| Schema drift | Optional/renamed fields handled or reported missing; no crash |
| Unchanged-source aging | Timed lookback refresh runs without a new write |
| Diagnostics | Content-free; skipped/oversized/schema counters present |
| Bounded state | Cache/cursor budgets explicit; no unbounded history |
| Idempotence | Repeated polls do not duplicate records |
| Privacy | Read-only; synthetic fixtures only; no real DB/log |

## Regressions

- Existing reader tests pass.
- The reader does not write to the source.
- No network dependency for local reading.
- No raw content/credentials in diagnostics.

## Secondary

- Unnecessary dependencies/files/rewrites.
- Completion time/tokens.
- Blind rubric: explicit budgets, resumable state, tests that fail on the baseline.

## Scoring

- Functional: 12 gates, each pass = 1. Task complete only if all gates for that
  task pass.
- Regressions: any failure = task failure.
- Record secondary separately; do not use it to excuse functional failure.

## Blind review

Reviewer does not know the arm. Prefer executable checks; use judgment only for
design clarity and test quality.
