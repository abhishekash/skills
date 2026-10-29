---
name: monitoring-performance-budgets
description: Diagnose and budget a local monitor's CPU, memory, refresh, and database cost. Use when a TUI or collector feels heavy, before optimizing or rewriting in another language, when adding a benchmark, or when reporting p95/RSS claims that need honest limits.
---

# Monitoring performance budgets

A monitor is judged by what it costs while someone else works. A fast inspector
is irrelevant if idle polling burns a core, hidden views repaint, or a 2 MiB
record is decoded into 100 MiB of Python objects.

Measure first. Then remove work. Only then consider a faster runtime.

## When to use

- "Why is the monitor using so much CPU/RAM?"
- The machine feels overloaded but the app is not obviously at fault.
- A benchmark is about to be added or quoted.
- Someone proposes Rust/Go/a rewrite.
- A performance change needs regression protection.
- A p95/RSS/database-growth claim is going into a README.

## Step 1: separate app cost from system pressure

Agenturm's first investigation is the template:

- Agenturm: ~121 MiB RAM, ~12–39% of one core, ~405 MB logical reads / 10 s.
- Physical disk reads: only ~1.2 MB.
- System: ~14/15 GiB RAM used, 4 GiB swap full, `kswapd0` busy, 19–20
  ChatGPT/Codex processes OOM-killed in 12 minutes.

The system was thrashing; Agenturm was doing avoidable work but was not the
primary cause. A monitor must not be blamed for a machine that is already
overloaded.

Collect:

- process RSS and CPU as % of one core
- system available RAM, swap, `kswapd0`, major faults, disk read/write
- logical vs physical I/O
- the largest memory groups, noting shared memory double-counting
- kernel OOM/restart events

Do not sum per-process RSS and call it total memory; shared pages are counted
multiple times. Do not infer a leak from one sample.

## Step 2: find repeated work

Look for:

- full-file/database rescans on every change
- rebuilding spans/derived records for unchanged source rows
- polling every second when 2 s is enough
- repainting every cell when one changed
- rendering hidden tabs
- loading full traces to compute counts
- re-reading inventory/configuration when scope did not change
- unbounded concurrency and queues

Agenturm's biggest wins were all **doing less**:

| Fix | Before | After |
|---|---:|---:|
| Incremental OpenCode import after unrelated DB write | ~860 ms CPU | ~8 ms |
| One changed tool record | ~852 ms | ~14 ms |
| Agenturm CPU (sample) | ~37% | ~12% |
| Terminal CPU (sample) | ~50% | ~7% |
| RAM (sample) | 106 MiB | 94 MiB |

## Step 3: whole-app benchmark

A microbenchmark is not the app. Build a fresh-process harness that includes:

- the actual receiver
- the actual feed/HTTP polling
- the actual SQLite database
- a headless UI
- all views warmed before measuring

Workloads:

- small: 10 traces × 20 spans
- large: 2 traces × 10,000 spans
- payload-heavy: 2 traces × 1,000 spans with 8 KiB payloads

Measure:

- ingestion + derived time
- refresh median / p95 (and sample count)
- idle CPU over a meaningful window
- peak RSS (whole process)
- database size
- any per-view timing if useful

Run each workload in a fresh process and temporary directory. No personal data,
paid models, or external network.

Agenturm's final numbers (Python 3.13.5, Linux, synthetic, headless):

| Workload | Refresh median / p95 | Idle CPU | Peak RSS | DB |
|---|---:|---:|---:|---:|
| 200 spans | 29.9 / 64.6 ms | 6.7% | 68.0 MiB | 0.30 MiB |
| 20,000 spans | 55.6 / 120.9 ms | 9.6% | 69.7 MiB | 9.34 MiB |
| 2,000 spans, 8 KiB payloads | 48.7 / 122.6 ms | 8.9% | 81.8 MiB | 17.42 MiB |

State the limits:

- 12 samples are not a reliable production p95.
- Headless UI CPU/RSS does not prove real-terminal rendering cost.
- RSS includes Python, Textual, SQLite, and temp allocations.
- Derived refresh still scans traces inside SQLite and holds the writer lock.
- Database growth from indexes/statistics is a trade, not free speed.

## Step 4: deterministic budgets

Protect work limits in tests, not machine-dependent timings.

Agenturm's budgets:

| Component | Budget |
|---|---|
| Feed reads | 4 workers, 16 prefetch slots |
| Receiver response | 16 MiB before JSON decode |
| Receiver concurrency | 32 workers, immediate 503 over limit |
| Receiver deadlines | 10 s headers, 15 s body, absolute |
| Live poll | 2 s |
| Inventory/findings cache | 5 s unless scope changes |
| Watched JSONL | 8 MiB/poll, 2 MiB/record |
| OpenCode payload | 2 MiB/record, 16 MiB/poll |
| Native caches | 64 KiB/entry, 1 MiB/map |
| Derived evidence | 256 records, 64 KiB/record, 2 MiB window, 128 groups |
| AI evidence | 30 matching events |
| UI refresh | 0.5 s; repaint only on change |

These are component budgets, **not** a fixed whole-process RSS ceiling.

Test examples:

- unchanged status does not request a repaint
- one changed cell does not repaint a row
- hidden views do no render work
- inventory query cache is used across refreshes; filter changes bypass it
- prefetch is parallel, deduplicated, and capped
- a response over 16 MiB is rejected before decode
- derived refresh stays below an allocation bound on a large fixture
- index use is asserted via query plan

## Step 5: latency, not just averages

If the UI promises input latency:

- use at least 200 measured interactions after warmup
- report p50/p95/p99, not one mean
- combine headless Pilot tests with real terminal/PTY measurements
- separate keypress→visible selection from collection→display freshness
- state the hardware, OS, terminal, Python/runtime, and workload

Agenturm's spec proposed p95 ≤ 50 ms keypress→selection, ≤ 100 ms selection→cached
inspector, ≤ 150 ms resize, ≤ 1% idle CPU, ≤ 1 s shell, ≤ 2 s populated view, and
≤ 2 s clean exit. These were **proposed acceptance targets, not measurements**.
Do not present them as achieved.

## Rust / rewrite decision

Do not rewrite to hide redundant work. At ~121 MiB and 12–39% CPU, Agenturm's
problem was repeated scans, repaints, and hidden-view rendering. Incremental
imports and changed-cell updates delivered a large win in Python.

Consider a lower-level rewrite only if, after removing redundant work and
profiling:

- a measurable CPU/memory/latency gate is still missed,
- the bottleneck is in the language/runtime, not I/O or algorithm,
- packaging, distribution, terminal lifecycle, and platform coverage are
  funded,
- a controlled comparison meets the same correctness gates,
- and the replacement shows a meaningful win (Agenturm's spec used ≥20% median
  investigation-time reduction, or a reproducible blocker), not just a prettier
  sample.

A framework change is a product migration, not an optimization.

## Reporting template

```text
Machine: <CPU/RAM/OS/terminal>
Runtime: <Python/Node version>
Workload: <small/large/payload, synthetic>
Samples: <N, warmup>
Refresh: median <x> ms, p95 <y> ms
Idle CPU: <z>% of one logical core over <window>
Peak RSS: <r> MiB (whole process)
Database: <d> MiB
What this measures: <...>
What it does not measure: <real terminal rendering, production p95, ...>
```

If you cannot state the last two lines, you do not have a benchmark; you have a
number.

## Failure modes

| Anti-pattern | Why it misleads |
|---|---|
| Benchmarking only the reader loop | Ignores UI, receiver, SQLite, and rendering work |
| Quoting 12 samples as p95 | Statistically meaningless |
| Summing RSS | Double-counts shared memory |
| Logical reads as disk I/O | 405 MB logical was ~1.2 MB physical |
| Calling component budgets an RSS cap | They bound work, not total memory |
| Optimizing hidden views by not rendering them, then claiming UI speed | Hidden work still needs a test |
| Adding concurrency without bounds | More threads = worse under load |
| Rust rewrite before profiling | New language, same redundant scans |
| Benchmarking on a thrashing machine | Measures the OOM killer, not the app |
| Claiming end-to-end from a query microbenchmark | Ignores HTTP/ingestion/UI |

## Case study

The user's first report was "seems my machine is overloaded". The honest answer
was: Agenturm uses ~121 MiB and 12–39% of one core, but the machine is thrashing
because of a Codex desktop OOM/restart cycle, browsers, and stale dev services.
Agenturm still had real waste: the OpenCode reader rebuilt spans on any DB change,
and the UI polled every second and updated hidden views/all cells. Removing that
work cut Agenturm CPU by roughly two-thirds. The Rust question was answered with
profiling, not ideology.

## Checklist

- [ ] App cost separated from system pressure.
- [ ] Repeated-work hotspots identified before optimization.
- [ ] Whole-app benchmark in fresh processes with synthetic data.
- [ ] Workloads include small, large, and payload-heavy cases.
- [ ] Sample count and spread reported.
- [ ] Peak RSS is whole-process and clearly scoped.
- [ ] Database growth and its cause reported.
- [ ] Deterministic budgets tested.
- [ ] Latency targets use ≥200 interactions and percentiles.
- [ ] Rust/rewrite decision tied to measured gates.
- [ ] Report states what was and was not measured.
