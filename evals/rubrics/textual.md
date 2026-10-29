# Textual rubric

Independent scoring for `textual-tui-engineering` tasks. Primary = functional
correctness and regressions; secondary = unnecessary changes, effort/time, tokens.

## Functional gates (must pass)

| Check | Pass condition |
|---|---|
| Empty → populated | Table has expected rows and keys |
| Append / removal / reorder | No `KeyError`; rows/keys match; stale row heights never accessed |
| Unchanged data | No `update_cell`/rebuild; result is `unchanged` |
| Changed content | Only changed cells update; values correct |
| Style-only change | Base style and spans update; no false no-op |
| Row-height change | Rebuild path; row height matches content |
| Invalidation | Theme/projection/resize invalidation forces re-evaluation |
| Selection | Stable key survives; missing key falls back predictably |
| Failed update | Signature not recorded; retry succeeds |
| Hidden/zero-width detail | No write; pending text renders on show |
| Stale async detail | `A → B → A` rejects the old A; latest A renders |
| Scroll | Valid offset after rebuild; no crash |

## Regressions

- Baseline fixture smoke tests still pass.
- The app still composes at 80×24 and 160×48.
- No private data, network calls, or extra services.
- Existing public method names/contract preserved unless the task says otherwise.

## Secondary

- Unnecessary files/dependencies/rewrites (lower is better).
- Completion time and token usage when available.
- Blind rubric: clarity of the small patch, tests actually exercise the bug,
  no solution-by-prose.

## Scoring

- Functional: 12 gates, each pass = 1, fail = 0. A task is **functionally
  complete** only if all gates for that task pass.
- Regressions: all must pass; any regression = task failure regardless of gates.
- Secondary: record, do not use to excuse a functional failure.
- Report per-run raw counts and the paired delta.

## Blind review

The reviewer must not know which arm produced a patch. Score tests and behavior
first; then optional readability. Do not reward copying the skill's terminology.
