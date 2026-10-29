# Kiln batch-job status fixture

Synthetic batch-job scenarios for the status evaluation. It uses `job_id`,
`turn_id`, collector freshness, and process progress, not Agenturm's session
objects or schema.

## Scenarios

- `quiet-work` — recent records, unfinished turn, no process. Expected:
  Working (quiet), active.
- `explicit-wait` — approval wait for 900 s. Expected: Waiting, inactive.
- `collector-delay` — agent records old, collector read 60 s old. Expected:
  Monitor delayed, not Failed/Stalled.
- `old-completed-new-started` — turn 1 completed, turn 2 started recently.
  Expected: the new turn is Working (quiet); the old outcome must not win.
- `process-progress` — old records, but exact process progress 2 s ago. Expected:
  Processing/Tool running, active.
- `unconfirmed` — old records, stale process observation, no exact live match.
  Expected: Unconfirmed, inactive.

`expected.json` is a reference for the evaluator. The agent should produce a
classifier or written state model that matches the evidence rules, not hard-code
the fixture IDs.
