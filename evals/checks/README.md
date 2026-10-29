# Executable checks

These scripts are independent of Agenturm and run against a **run directory**
prepared by `evals/harness.py`:

- `textual_contract.py` — expects `order_board.py` and Textual 8.2.8.
- `ingestion_contract.py` — expects `reader.py` with the `read_once` contract and
  the Forge fixture generator.
- `status_contract.py` — expects `status_model.py` with `classify`.

All three are expected to fail on the untouched fixtures (the baseline is
intentionally naive) and pass only after the task's behavior is implemented. They
are **not** run by the repository's packaging CI, because they require an agent's
solution in the run directory.

Run from the run directory:

```bash
python /path/to/evals/checks/textual_contract.py -v
python /path/to/evals/checks/ingestion_contract.py -v
python /path/to/evals/checks/status_contract.py -v
```

The checks are deliberately behavioral, not a style test. A passing check does
not prove the patch is good; use the rubric for regressions and unnecessary
changes.
