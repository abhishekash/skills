---
name: sqlite-telemetry-store
description: Design or repair a local SQLite store for live agent telemetry — spans, logs, metrics, sessions, findings, usage, retention. Use for slow trace pages, memory blowups during summaries, prune/refresh races, unknown totals, database permissions, or deciding whether DuckDB is justified.
---

# SQLite telemetry store

SQLite is an excellent live store for a local monitor: embedded, transactional,
portable, and fast for short upserts and indexed reads. It is a poor place to
materialize every trace in Python, and it is not a secure-erasure tool.

## Operating contract

**Purpose.** Design or repair a local telemetry store that supports live writes,
bounded reads, exact totals, retention, and honest completeness.

**Inputs.** The record types and query patterns; expected write/read rates;
retention policy; concurrency model; existing schema/indexes; product claims about
totals/unknowns; backup/export needs. Profile existing queries before adding an
engine.

**Workflow.**

1. Inventory writes, reads, retention, and concurrency.
2. Choose the live store; keep analytics separate unless measured otherwise.
3. Define keys, upserts, and the indexes matching ordered reads.
4. Move aggregates to SQL; bound evidence and propagate completeness.
5. Serialize derived-cache replacement with retention.
6. Set owner-only creation and retention semantics.
7. Add index-use, race, unknown-total, and growth tests.
8. Report measured query numbers with their scope.

**Deliverable.** A schema/index plan or patch, bounded derived queries,
completeness semantics, retention/concurrency rules, permissions, and tests.

**Completion.** Ordered pages use an index; derived refresh does not load whole
traces into Python; unknown totals remain unknown; retention cannot be undone by
an in-flight refresh; a new DB is owner-only; query benchmarks state their scope.

## Reading this skill

- **Invariant** — exact totals or explicit unknowns; bounded evidence; stable
  identity; retention/refresh consistency; owner-only storage; no fabricated zero.
- **Default** — Agenturm's schema, budgets, and retention choices. Adapt them.
- **Case study** — Agenturm's exact index, budgets, and measurements are in
  [`references/agenturm-schema.md`](references/agenturm-schema.md).

Numbers are **measured**, **example/default**, or **proposed target** as labeled.
A query microbenchmark is not end-to-end latency.

## When to use

- Building a local-first store for agent runs/traces/logs/metrics.
- A dashboard refresh loads entire traces or finding logs into memory.
- Ordered trace pages are slow.
- Unknown usage/cost is rendered as zero.
- Retention and derived refresh race, or a concurrent process recreates deleted
  caches.
- A new database file is briefly world-readable.
- Someone proposes DuckDB or a dual-write analytics path.

## Fit

Keep SQLite for the live store when the workload is:

- frequent small inserts/upserts (spans, logs, native records)
- dedupe by `(trace_id, span_id)` / stable record ID
- recent-session and paginated history reads
- concurrent reader/writer threads in one process
- a single-user local database

Use DuckDB only for a **separate analytics** workload over a consistent snapshot
or bounded Parquet exports: large historical group-bys, percentiles, month-over-
month comparisons. Do not make ingestion depend on analytics and do not dual-write.

DuckDB's embedded mode allows concurrent writer threads within one process, but
conflicting updates need retries. Multi-process writes (Quack/DuckLake) add
coordination. Its SQLite extension still uses SQLite locking, so it does not
remove write contention. Benchmark before adding it.

## Schema and indexes

Minimum patterns:

```sql
-- stable identity; upsert on repeat
CREATE TABLE spans (
  trace_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  parent_span_id TEXT,
  start_ns INTEGER,
  end_ns INTEGER,
  status TEXT,
  name TEXT,
  attributes TEXT,
  PRIMARY KEY (trace_id, span_id)
);

-- ordered trace pages without a temp sort
CREATE INDEX spans_trace_start
  ON spans (trace_id, start_ns, span_id);

-- recent session/history reads
CREATE INDEX spans_trace_time ON spans (trace_id, end_ns);
CREATE INDEX logs_session_time ON logs (session_id, time_ns);
```

- Add the index that matches the actual `ORDER BY`/pagination query.
- Verify index use in a regression (`EXPLAIN QUERY PLAN` assertion), not a
  machine-specific timing.
- Measure the query in isolation if you quote a number; do not present it as
  end-to-end latency.

Agenturm's ordered 50,000-span page went from **143.8 ms → 0.52 ms median** over
25 repetitions after adding `(trace_id, start_ns, span_id)`. That isolates the
query only.

## Derived summaries without memory blowups

Do not load the whole trace into Python to count spans, sum tokens, or find the
latest error. Use SQL for exact aggregates:

- counts, min/max timestamps
- token/cost totals
- distinct services/models/tasks (with group budgets)
- ancestry deduplication for parent/child rollups where needed

For evidence (findings, sample events, AI context), use bounded windows and
advertise incompleteness. These are Agenturm's **example/default** budgets:

```text
256 records
64 KiB per record
2 MiB window
128 label groups
```

- Return exact totals for fields you can aggregate exactly.
- If a payload shape is unsupported or oversized, return `null` + `complete=false`.
- Never fabricate `0`, `$0`, or "no errors" outside the window.
- Propagate completeness flags to sessions, metrics, usage series, AI evidence, and
  the UI.
- A bounded sample is evidence, not proof of absence.

Agenturm's 20k-span synthetic database grew from 14.6 MiB (intermediate) to
9.3 MiB after omitting all-zero per-span statistics, but still grew from 5.35 MiB
at `HEAD` because of the trace-start index and per-span statistics cache. State
the trade.

## Incremental derived caches

- Cache compact per-span statistics, keyed by `(trace_id, span_id)` + revision.
- Invalidate/recompute when the source span changes.
- Preserve ancestry-sensitive deduplication for late children/reparenting.
- Replace a derived cache only inside the same transaction as the read that
  produced it.
- Do not let a background refresh resurrect rows deleted by retention.

## Concurrency and retention

SQLite gives you serialized writers; use them.

- Keep transactions short.
- For refresh + prune, acquire the writer lock explicitly
  (`BEGIN IMMEDIATE`) around the read/recheck/replace sequence.
- A per-`Store` lock is not a cross-process guarantee by itself; SQLite locking
  is. Test with two `Store` instances/processes.
- Retention is **logical deletion**, not secure erasure. Deleted content may
  remain in free pages, journals, snapshots, and backups. Say so.
- Run pruning in a bounded batch; do not hold the writer lock for a whole vacuum.
- Native source logs are separate; pruning telemetry does not delete them.

A regression test should pause a refresh, prune, resume, and prove the deleted
cache is not recreated. If the implementation changes the pause hook, adapt the
test to the new boundary without weakening the race assertion.

## Permissions

Create the database with owner-only permissions **before SQLite opens it**:

```python
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
os.close(fd)
# then connect
```

If the file already exists, verify/tighten permissions rather than assuming the
umask. A new database that briefly inherits group/world read is a privacy bug,
not a cosmetic one.

## Pagination

- Use a cursor (opaque `next_cursor`), not offset pages, for live data.
- Reset history when the filter/scope changes; otherwise old pages leak into a
  new query.
- Cap page size and total response bytes before decode.
- Keep an explicit "loaded N of M" / completeness note for derived views.

## Retention and backup

- Retention is a policy, not a compliance promise. Explain free pages/journals/
  backups.
- Back up with SQLite's backup API, not by copying an active database file.
- For analytics, export a consistent snapshot to Parquet or a backup DB, run
  DuckDB in a separate process, and display the snapshot timestamp.
- Never let an analytics read block or write the live store.

## Benchmarking

Compare on the same machine/OS/Python, fresh processes, temporary databases:

- small: 10 traces × 20 spans
- large: 2 traces × 10,000 spans
- payload-heavy: 2 traces × 1,000 spans, 8 KiB payloads

Report:

- ingestion + derived time
- ordered page / summary query latency (median and spread)
- peak RSS (whole process, including Python/SQLite/temp allocations)
- database size and growth cause
- concurrent update/crash/restart behavior

State sample count and limits. Twelve samples are not a production p95. Do not
claim a whole-process RSS cap from component budgets.

## Failure modes

| Anti-pattern | Result |
|---|---|
| Load full trace to count/sum | Memory spike; slow refresh; holds writer lock |
| Fabricate zero for unknown usage | False dashboards and billing confusion |
| Sample evidence without a completeness flag | "No errors" claim from a partial window |
| Count-only group budgets | Huge payloads blow the budget |
| Refresh/cache write outside the prune transaction | Deleted caches resurrect |
| Copy an active DB file for backup | Corrupt/inconsistent snapshot |
| Dual-write to SQLite + DuckDB | Double failure modes; reconciliation bugs |
| Add DuckDB before profiling SQLite | New dependency with no measured benefit |
| Assume retention = secure erase | Data remains in free pages/backups |
| Create DB with default umask | Brief world-readable telemetry |
| Timing assertion on CI | Flaky; does not prove index use |

## Case study

Agenturm's store was mixing normalization, persistence, derived analysis, and
query APIs in one module. A review pass found full-trace processing, a missing
ordered-page index, a prune/refresh race, and a permissive database creation
window. The fix was not a rewrite: exact SQL aggregates, a new derived helper,
bounded evidence, writer-lock serialization, owner-only creation, and index-use
tests. DuckDB was evaluated and deliberately deferred; the live workload favored
SQLite, and no measured analytical gain justified a second engine.

The exact index, budgets, database sizes, and query measurements are in
[`references/agenturm-schema.md`](references/agenturm-schema.md). They are a case
study, not universal schema requirements.

## Related skills

These are separate skills. Naming one here does **not** load it; use your host's
skill-loading mechanism.

- `local-agent-ingestion` — normalizes the records stored here.
- `monitoring-performance-budgets` — measures the whole system, not just SQL.
- `tui-regression-testing` — protects index use and unknown-total behavior.

## Checklist

- [ ] Live store is SQLite; analytics is separate/snapshot-based.
- [ ] Stable primary keys and upserts.
- [ ] Indexes match ordered pages and session/time reads.
- [ ] Derived totals use SQL, not Python object graphs.
- [ ] Evidence is bounded with completeness flags.
- [ ] Unknown values are null, never zero.
- [ ] Derived caches transactional and invalidated on change.
- [ ] Prune/refresh serialized with the writer lock; cross-process test.
- [ ] DB created/verified owner-only before open.
- [ ] Pagination resets on scope/filter change; response bytes capped.
- [ ] Retention documented as logical deletion.
- [ ] Backup uses SQLite backup API; analytics reads a snapshot.
- [ ] Benchmarks report hardware, samples, RSS, DB size, and limits.
- [ ] DuckDB considered only after measured SQLite profiling.
