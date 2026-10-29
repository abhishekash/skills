# Agenturm implementation notes (case study)

These notes record decisions from the 2026 Agenturm Textual cockpit. They are
**case study**, not universal requirements. The portable invariants and defaults
live in `SKILL.md`; the runnable examples live in `examples/`.

## Tested environment

Agenturm's work was validated on Python 3.11–3.14; the focused UI runs used
Python 3.13.5, Textual **8.2.8**, and Rich **15.0.0**. The skill's runnable
examples were verified with that same Textual/Rich pair. This is not a claim that
every Textual 8.x release behaves identically.

## Measured or observed numbers

- Agenturm's `terminal_ui.py` grew to roughly 160 KB. That size was a reason to
  extract boundaries, not a target for another app.
- The feed used four read workers and sixteen prefetch slots, a two-second live
  poll, a five-second inventory/findings cache, and a 0.5-second UI refresh
  timer. These are **configurable defaults chosen for Agenturm**, not universal
  budgets.
- Receiver responses were capped at 16 MiB before JSON decode.
- Evidence rendering depth was capped at 64; content caps were 8,000 characters
  per activity record, 2,000 per nested field, and 60 entries.
- The suite grew through the work and finished above 300 tests. Test counts are
  context, not a quality target.
- The first `fill()` implementation accessed `table.rows[k].height` for incoming
  keys before checking that the keys existed, and its signature used only
  `str(value)`. New rows could raise `KeyError`, and style-only changes could be
  skipped. The portable fix is in
  `examples/incremental_table/table_projection.py`.

## Decisions that were product-specific

- A three-row shell (identity/health, navigation, view controls) fit Agenturm's
  read-only monitoring brief and 120×30 target. It is a default, not a rule.
- Four primary views and `1–7` shortcuts came from Agenturm's existing keymap.
  Another app may need a different count or keymap.
- Agents opened in `Recent` (active/attention plus the latest finished session)
  because the historical list dominated the first screen. This is a default
  history policy, not a requirement.
- The 25% top overview, the two-frame overview/Views layout, and the 80×24
  acceptance targets were responses to Agenturm's specific user feedback.
- The monitor stayed read-only. An authorized action-capable TUI would need a
  different permission and audit model; the TUI invariants here still apply, but
  the product boundary does not.

## Reproduction and limits

- The original code is MIT-licensed at
  <https://github.com/abhishekash/agenturm>.
- Agenturm's tests and docs are the source for the case-study claims. They are
  not bundled here, and this pack does not depend on them.
- Headless Textual tests do not establish real-terminal rendering, clipboard
  behavior, or every platform's shutdown semantics.
