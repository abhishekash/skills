# Agenturm SQLite case study

These are Agenturm's concrete schema and measurement choices. They are **case
study**, not universal requirements. The portable rules are in `SKILL.md`.

## Live store

SQLite remained the live store for short upserts, dedupe, recent-session reads,
and paginated history. DuckDB was considered for separate historical analytics
but not adopted; no measured analytical gain justified a second engine and
snapshot pipeline.

## Ordered-page index

Added:

```sql
CREATE INDEX spans_trace_start
  ON spans (trace_id, start_ns, span_id);
```

A synthetic 50,000-span ordered page measured **143.8 → 0.52 ms median** over 25
repetitions. This isolates the query; it is not HTTP, ingestion, or end-to-end UI
latency.

## Bounded derived evidence

Agenturm's example/default budgets:

- 256 records
- 64 KiB per record
- 2 MiB window
- 128 label groups
- exact SQL counts/timestamps/usage/cost where supported
- `null` + `complete=false` for oversized/unsupported usage, never fabricated
  zero

The 20k-span synthetic database grew from 14.6 MiB (intermediate implementation)
to 9.3 MiB after omitting all-zero per-span statistics, but was still larger than
the 5.35 MiB `HEAD` because of a 1.45 MiB trace-start index and a 2.54 MiB
per-span statistics cache. This was a deliberate storage/refresh tradeoff.

## Concurrency and retention

- Refresh and pruning held SQLite's writer lock (`BEGIN IMMEDIATE`) around the
  read/recheck/replace sequence.
- A second `Store` instance was used to test the cross-instance race.
- Retention was logical deletion, not secure erasure.
- The database was created owner-only before SQLite opened it.

## Limits

- Derived refresh still performed whole-trace SQL scans and held the writer lock.
- Findings/search evidence was windowed; older evidence could be absent and was
  marked incomplete.
- A process that edits the database while ignoring SQLite locking, or a
  filesystem snapshot/backup, remained outside the guarantee.
- No whole-process RSS or fixed-latency guarantee was claimed.
