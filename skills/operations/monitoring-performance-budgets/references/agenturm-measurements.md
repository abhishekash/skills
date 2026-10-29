# Agenturm performance case study

These numbers are **Agenturm-specific measurements** from 2026-10-21 and
2026-10-24. They are context for the method, not universal targets. Read the
scope and limits with every number.

## First investigation (2026-10-21)

- Agenturm: ~121 MiB RAM, ~12–39% of one core, ~405 MB logical reads / 10 s.
- Physical disk reads: ~1.2 MB in the same sample.
- System: ~14/15 GiB RAM used, 4 GiB swap full, `kswapd0` busy, 19–20
  ChatGPT/Codex processes killed by the OOM killer in ~12 minutes.

Agenturm was not the primary cause of the system overload, but it was doing
avoidable repeated work. The machine was thrashing independently.

## Incremental-import result

| Metric | Before | After |
|---|---:|---:|
| Agenturm CPU (one core, sample) | ~37% | ~12% |
| Agenturm RAM | 106 MiB | 94 MiB |
| Terminal CPU | ~50% | ~7% |
| OpenCode poll after unrelated DB write | ~860 ms | ~8 ms |
| One changed tool record | ~852 ms | ~14 ms |

These are samples, not a controlled distribution.

## Whole-app benchmark (2026-10-24)

Python 3.13.5, Linux, synthetic data, temporary SQLite, loopback receiver, HTTP
feed, headless Textual UI, all views warmed.

| Workload | Refresh median / p95 | Idle CPU | Peak RSS | DB |
|---|---:|---:|---:|---:|
| 10 traces × 20 spans | 29.9 / 64.6 ms | 6.7% | 68.0 MiB | 0.30 MiB |
| 2 traces × 10,000 spans | 55.6 / 120.9 ms | 9.6% | 69.7 MiB | 9.34 MiB |
| 2 traces × 1,000 spans, 8 KiB payloads | 48.7 / 122.6 ms | 8.9% | 81.8 MiB | 17.42 MiB |

The prior `HEAD` large workload measured 69.1 / 180.6 ms, 11.2% idle CPU,
68.8 MiB RSS, and a 5.35 MiB database. The database grew because of a 1.45 MiB
trace-start index and a 2.54 MiB per-span statistics cache.

## Limits

- 12 refresh samples are not a reliable production p95.
- Headless UI CPU/RSS does not establish real-terminal rendering cost.
- RSS includes Python, Textual, SQLite, and temporary allocations.
- Derived refresh still scans whole traces inside SQLite and holds the writer
  lock.
- The reader microbenchmark measures only OpenCode polling, not the whole app.
- The ordered-page query measured 143.8 → 0.52 ms median over 25 repetitions on a
  synthetic 50,000-span trace; that isolates the query, not end-to-end latency.
