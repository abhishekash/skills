# Textual task 1 — incremental rows and selection

## Context

`order_board.py` is a small Textual order board. Its current `apply_orders()`
clears and rebuilds the `DataTable` on every update. Operators see flicker, lose
the selected row, and pay for full rebuilds on unchanged data.

## Goal

Implement incremental table updates without changing the public contract:
`apply_orders(orders)` must remain callable with a list of `Order`.

## Required behavior

- Empty → populated works.
- Append, removal, and reorder rebuild safely (new/removed keys must not raise).
- Unchanged data performs no cell updates.
- Changed content updates only changed cells.
- A style-only change is not missed.
- A row-height change takes the rebuild path.
- Selection is preserved by stable order ID; if the ID disappears, choose the
  nearest valid row and do not present another order's detail as if it were the
  old one.
- An explicit invalidation (theme/projection/resize) forces the next apply to
  re-evaluate.
- A failed update remains retryable.

## Checks

From the run directory:

```bash
python -m unittest -v
python - <<'PY'
# Add the task-specific checks from the rubric here if they are not in tests.
PY
```

Use headless `App.run_test()`. Do not require a real terminal.

## Deliverable

A focused patch to `order_board.py` plus tests for the behaviors above.

## Completion

The baseline smoke tests still pass; the listed behaviors are covered by tests;
unchanged data avoids updates; selection survives when possible; the app still
runs at 80×24 and 160×48.

## Constraints

- Do not add a network call or read personal data.
- Do not change the fixture's public method names.
- Keep dependencies to Textual/Rich.
