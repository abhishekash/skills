# Status task 3 — completed turn followed by a new turn

## Context

`status_kiln/scenarios.json` includes `old-completed-new-started`: turn 1
completed, turn 2 started recently. A session-level classifier that stores only
the last terminal outcome would hide the new work as "Completed".

## Goal

Model turn/session identity and precedence so the newest started turn wins.

## Required behavior

- A newer started turn overrides an older terminal outcome.
- The old outcome remains available as history, not as the current status.
- A completed turn with no newer turn remains Completed.
- Out-of-order timestamps or ties are handled deterministically and flagged.
- Ambiguous process evidence does not confirm a stall.
- The classifier exposes the turn ID used for the decision.

## Checks

Use `EVAL_TASK=3 evals/checks/status_contract.py` with the `status_model.classify`
contract from task 1. It covers `old-completed-new-started` and a completed-only control,
plus an out-of-order turn case.

## Deliverable

A state model/classifier with explicit turn identity and precedence, plus tests
for new-turn, completed-only, and tie/out-of-order cases.

## Completion

The new turn is active; the old outcome does not override it; completed-only is
still completed; ambiguous evidence is not a confirmed stall.

## Constraints

- Do not model status as a single session-level terminal enum.
- Do not discard turn history.
- Keep unknown/unconfirmed states.
