# Status task 1 — quiet long-running work vs explicit wait

## Context

`status_kiln/scenarios.json` has a quiet unfinished turn and an explicit approval
wait. A naive 35-second timer would label both as stuck/no updates.

## Goal

Produce a state/evidence model or classifier that distinguishes quiet work from
an explicit wait.

## Required behavior

- Quiet-work scenario → Working (quiet), active.
- Explicit-wait scenario → Waiting, inactive.
- The wait subtype/reason is preserved.
- Silence alone does not produce a stall.
- The classifier exposes the evidence sentence used for the label.
- Thresholds are configurable and documented as defaults.

## Checks

Use `evals/checks/status_contract.py` from the run directory. It expects:

```python
# status_model.py
def classify(scenario, *, now_ns=None) -> dict:
    return {"state": "...", "active": bool, "evidence": "..."}
```

The check compares the `status_kiln` fixture to `expected.json` and adds an
out-of-order-turn case.

## Deliverable

A state/evidence table and/or classifier plus tests for the two scenarios and the
threshold transition.

## Completion

Both labels and active flags match; the evidence string explains why; the
threshold transition is tested.

## Constraints

- Do not use elapsed time alone as a stall signal.
- Do not collapse the explicit wait into "Working".
- Keep thresholds centralized/configurable.
