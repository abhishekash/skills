# Status task 2 — stale collector vs agent failure

## Context

`status_kiln/scenarios.json` includes a `collector-delay` scenario: the agent's
last record is old and the collector's last successful read is 60 s old. A naive
classifier may call the agent failed or stalled.

## Goal

Separate monitor freshness from agent state and avoid a false failure claim.

## Required behavior

- Collector delay/backlog → `Monitor delayed` or `Catching up`; agent health
  explicitly unconfirmed.
- The label is not `Failed`, `Error`, or `Possibly stalled` on collector evidence
  alone.
- The evidence sentence names the collector issue.
- A recorded agent failure with fresh collection still produces the failure
  label.
- The model distinguishes "poll succeeded" from "new records read."

## Checks

Use `evals/checks/status_contract.py` with the `status_model.classify` contract
from task 1. It compares the collector-delay scenario to `expected.json`; add a
control scenario with fresh collection plus a recorded failure.

## Deliverable

A classifier/model change plus tests for collector delay, backlog, fresh failure,
and the evidence text.

## Completion

Collector delay is not reported as agent failure; a real failure is still
reported; the evidence explains the distinction.

## Constraints

- Do not merge collector health into the session status.
- Do not use "Live" to imply agent progress.
- Keep the unknown/unconfirmed state.
