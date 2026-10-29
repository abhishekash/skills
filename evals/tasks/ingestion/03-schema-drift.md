# Ingestion task 3 — schema variation and unchanged-source aging

## Context

`forge/schema_v2.json` describes a v2 build log with optional `attempt` and
`elapsed_ms`; the legacy `duration_ms` may be absent. Separately, an unchanged
source must still age out old records rather than requiring a new write.

## Goal

Handle optional/schema-drift fields safely and implement a timed lookback refresh
for an unchanged source.

## Required behavior

- A record missing optional fields is ingested without a crash.
- A record with `elapsed_ms` but no `duration_ms` is normalized correctly (or
  reported as missing, not fabricated).
- A partial/legacy schema does not break discovery.
- An unchanged source still refreshes after the lookback interval, so old
  records age out.
- Diagnostics distinguish "poll succeeded" from "new records read."

## Checks

Use `evals/checks/ingestion_contract.py` with the `read_once` contract from task
1. It includes a v2 record with optional `elapsed_ms` and no `duration_ms`.
Add the unchanged-source lookback test separately (fake clock or an injected
interval).

## Deliverable

A schema-tolerant reader plus tests for optional fields, legacy fields, unchanged
source aging, and diagnostics counters.

## Completion

Both schema variants ingest; missing optional values stay missing/unknown; the
lookback refresh runs without a source write; counters distinguish poll success
from new data.

## Constraints

- Do not require optional columns.
- Do not fabricate `0` for a missing duration/cost.
- Synthetic fixtures only.
