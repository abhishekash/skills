# Textual task 2 — hidden-pane resize/reflow

## Context

The `RichLog` detail pane in `order_board.py` can receive a detail response while
it is hidden or before it has a measured width. In the baseline, a hidden update
can cache one-character-wide lines; reopening at the same width may not rebuild
them.

## Goal

Make detail rendering safe when hidden/zero-width and rebuild the latest detail
when the pane becomes visible or is resized.

## Required behavior

- A render while hidden or at width 0 is deferred; nothing is written to the
  `RichLog`.
- `show_detail()` after the pane becomes visible renders the pending text.
- The rendered text is full-width readable, not one character per line.
- Re-showing an empty pane returns an explicit `empty` result.
- Resizing a visible pane refreshes/reflows the detail without losing the text.

## Checks

Use `App.run_test(size=(80,24))`. Hide `#detail`, call `apply_detail(...)`, assert
the log has no lines and the result is `deferred`; show it, call `show_detail()`,
assert the text is present and not one-character-per-line. Add a resize check.

## Deliverable

A focused patch plus tests for hidden, zero-width, show, and resize behavior.

## Completion

The baseline smoke tests still pass; the hidden/zero-width path does not mutate
the log; showing renders the latest pending detail; a resize does not corrupt it.

## Constraints

- Do not solve this by keeping the pane always visible.
- Do not write placeholder/demo text.
- Keep dependencies to Textual/Rich.
