# Evaluation status: pilot executed; replication pending

A **two-pair-per-task pilot** was executed on 2026-10-29. See
[`PILOT-2026-10-29.md`](PILOT-2026-10-29.md) and the raw scores in
[`PILOT-2026-10-29.json`](PILOT-2026-10-29.json).

- All 36 task arms passed their task-scoped checks and fixture tests.
- All 12 activation decisions were correct.
- Functional delta: **zero** across both rounds (both arms solved every task).
- Patch size was mixed in round 1 and mostly larger with the skill in round 2;
  see the pilot report for the negative signals.

**This is preliminary, not a demonstrated effectiveness claim.** The pilot has
two paired runs per task, no token/time capture, and no blind human rubric review. Keep
the claim open and run repeated paired trials before describing the skills as
better, proven, or parity with another author's work.

Use [`TEMPLATE.md`](TEMPLATE.md) for replication runs. The original pre-pilot
requirements remain:

- exact model/version and harness
- task and fixture
- number of paired runs
- raw scores per run (with failures/timeouts)
- paired delta and direction
- cases where the skill performed worse
- reviewer names/independence for the rubric
- token/time data, if available
- what remains unmeasured
