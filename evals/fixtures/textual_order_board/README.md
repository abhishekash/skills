# Order Board fixture (Textual)

An independent Textual app for the evaluation suite. It uses orders, not agents.

## Tested baseline

- Python 3.13.5
- Textual 8.2.8
- Rich 15.0.0

## Run

```bash
python -m pip install textual==8.2.8 rich==15.0.0
python -m unittest -v
```

`order_board.py` exposes the contract used by the checks:

- `apply_orders(orders)` — keep the `DataTable` in sync.
- `begin_detail(order_id) -> token` — start a detail request.
- `apply_detail(token, order_id, text)` — render the current request, defer when
  hidden/zero-width, return `rendered`, `deferred`, or `stale`.
- `show_detail()` — render a deferred request after the pane is visible.

The baseline clears and rebuilds the table on every apply and ignores the detail
token. The evaluation tasks ask you to fix one behavior at a time while keeping
the contract and the existing smoke test working.
