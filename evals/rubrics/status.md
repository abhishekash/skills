# Agent status rubric

Independent scoring for `agent-session-status` tasks. Primary = functional
correctness and regressions.

## Functional gates (must pass)

| Check | Pass condition |
|---|---|
| Quiet work | Working (quiet), active; not stalled from silence |
| Explicit wait | Waiting, inactive; subtype/reason preserved |
| Collector delay/backlog | Monitor delayed/Catching up; not Failed/Stalled |
| New turn vs old outcome | Newer started turn wins; old outcome retained as history |
| Completed-only control | Completed, inactive |
| Process progress | Processing/Tool running, active |
| No process evidence | Unconfirmed, not confirmed stall |
| Evidence text | Explains the label without inventing a cause |
| Attention | Cause + next step + review/dismiss; evidence retained |
| Unknown values | "Not reported"/unknown, never zero/fabricated |
| Tie/out-of-order | Deterministic handling, ambiguity flagged |
| Thresholds | Centralized/configurable; not elapsed-time-only |

## Regressions

- Existing classifier tests pass.
- No false stall/completion introduced.
- No fabricated totals/causes.
- Attention does not delete evidence.

## Secondary

- Unnecessary changes/files.
- Completion time/tokens.
- Blind rubric: state table clarity, precedence tests, honest uncertainty.

## Scoring

- Functional: 12 gates, each pass = 1. Task complete only if all gates for that
  task pass.
- Regressions: any failure = task failure.
- Record secondary separately.

## Blind review

Reviewer does not know the arm. Judge the state model and tests, not the amount
of prose.
