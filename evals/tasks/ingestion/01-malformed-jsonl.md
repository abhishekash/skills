# Ingestion task 1 — partial, oversized, and malformed JSONL

## Context

`forge/generate.py` produces `build_log.jsonl` (valid prefix + partial record at
EOF) and `build_log_mixed.jsonl` (valid, oversized, malformed, valid, valid).

## Goal

Implement a bounded reader that ingests the valid records and survives the bad
ones.

## Required behavior

- The partial record at EOF is retained for the next poll, then completed.
- The oversized record is discarded through its terminating newline; its suffix
  is not parsed as a new record.
- The malformed record is skipped; the following valid records are still
  ingested.
- The reader thread/loop stays alive after every malformed case.
- Diagnostics are content-free and report skipped/oversized counts.
- The offset advances past dropped/malformed records.

## Checks

Use `evals/checks/ingestion_contract.py` from the run directory. It expects:

```python
# reader.py
def read_once(path, *, offset=0, record_budget, poll_budget) -> dict:
    return {
        "records": [{"job_id": "...", ...}, ...],
        "offset": int,
        "diagnostics": {"skipped_oversized": int, "skipped_records": int, ...},
        "partial": bool,
    }
```

Run it with the fixture's `generate.py` in the run directory. The check uses
small budgets so the fixture is fast.

## Deliverable

A reader module/CLI and fixtures/tests. State the budgets used.

## Completion

The valid records appear; the partial record completes on the next poll; the bad
records do not kill the loop; diagnostics contain no raw content; repeated runs
are idempotent.

## Constraints

- Read-only; synthetic data only.
- No network calls.
- Do not use a real agent database.
