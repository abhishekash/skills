# Forge build-log fixture

Synthetic build-runner data for the ingestion evaluation. It uses `job_id`,
`step`, and `status`, not Agenturm sessions or schema.

## Generate

```bash
python generate.py --output /tmp/forge
```

This writes:

- `build_log.jsonl` — a partial record at EOF plus a valid prefix.
- `build_log_mixed.jsonl` — valid, oversized, malformed, then two valid records.
- `build_backlog.jsonl` — one oversized head record followed by 40 valid records.

## Expected behavior

A bounded reader should:

- keep the partial record for the next poll;
- discard the oversized record through its newline without parsing its suffix;
- skip the malformed record and still ingest the valid tail;
- make progress past the oversized head on repeated polls, eventually reaching
  the 40 valid backlog records;
- tolerate schema v2 optional fields without requiring `duration_ms`;
- emit content-free diagnostics for skipped/oversized/schema errors.

## Suggested budgets for the task

Use small test budgets (for example 64 KiB/record, 128 KiB/poll) so the fixture
is fast. These are evaluation settings, not production recommendations.
