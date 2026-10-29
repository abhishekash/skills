# Textual task 3 — stale asynchronous detail responses

## Context

`begin_detail(order_id)` returns a token and `apply_detail(token, order_id, text)`
renders detail. The baseline ignores the token. A slow response for order A can
arrive after the operator has selected B and then A again, overwriting the new A
detail with stale text.

## Goal

Bind each response to its request generation and reject obsolete responses.

## Required behavior

- `A → B → A` rejects the first A response even though its fields match the
  current scope again.
- A response for a different order is stale.
- The latest response renders normally.
- A rejected response does not clear or overwrite current detail.
- The token/generation logic is independent of Textual so it can be unit-tested.

## Checks

From the run directory, call the controller directly and/or use
`App.run_test()`. Assert the final detail is the latest A text and the old A text
never appears.

## Deliverable

A generation/scope gate wired into `begin_detail`/`apply_detail`, plus tests for
A→B→A and mismatched scope.

## Completion

The stale cases above pass; the current response still renders; the baseline
smoke tests still pass.

## Constraints

- Do not use a simple equality check on `order_id` as the only guard; A→B→A would
  pass it.
- Do not add a network dependency.
- Keep dependencies to Textual/Rich.
