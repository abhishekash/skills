---
name: tui-regression-testing
description: Test terminal UIs without trusting screenshots — headless Textual Pilot tests, geometry and keyboard assertions, stale-data race tests, resource budgets, real-PTY shutdown checks, and core-flow regressions. Use after any TUI layout, focus, filtering, or live-update change.
---

# TUI regression testing

A TUI is a stateful, asynchronous, geometry-dependent program. Screenshots prove
almost nothing, and unit tests miss the failures users actually see: a row moving
under the cursor, the previous session's evidence under a new title, a filter
overwritten by an old poll, or text wrapped one character per line.

Test behavior, geometry, and invariants — not pixels.

## Operating contract

**Purpose.** Produce a test plan and regression suite that proves a TUI's core
flow, geometry, focus, live-update races, and shutdown behavior at real terminal
sizes.

**Inputs.** The target IA and acceptance criteria; the supported sizes/themes;
the core data flow; the test seams (fake feed, stable IDs, headless app); the
platform/PTY support. Inspect the existing tests before adding a new harness.

**Workflow.**

1. Write the core-flow test in product terms before the layout change.
2. Add semantic geometry assertions at the target sizes.
3. Add keyboard/focus/Esc/typing tests.
4. Add stale-response, selection, hidden-view, resize, and empty-start races.
5. Add deterministic resource-budget tests.
6. Add a real-PTY shutdown test when cleanup/terminal restoration is involved.
7. Keep the demo harness on the same data contract as production.
8. Report what was tested and what remains unverified.

**Deliverable.** A test plan or patch: core-flow tests, size/theme matrix, race
tests, budget tests, real-PTY checks, and a verification report.

**Completion.** The core flow is covered at wide and compact sizes; race tests
would fail on the known bug; shutdown exits cleanly; fake feeds match the current
snapshot contract; unverified platform behavior is stated.

## Reading this skill

- **Invariant** — test the core feature, stable identity, real geometry, stale
  evidence, clean shutdown; do not weaken a behavior assertion to fit a layout.
- **Default** — Agenturm's size matrix, fake feed, 80×24 target, and test names.
  Adapt them to the app.
- **Case study** — Agenturm's exact regression list is in
  [`references/agenturm-test-matrix.md`](references/agenturm-test-matrix.md).

Numbers are **example targets** or **measured** as labeled; they are not a
universal test matrix.

## When to use

- Before and after any layout, focus, filtering, or live-update change.
- A redesign "looks better" but may have broken the core flow.
- A bug only appears after resize, tab switch, or rapid refreshes.
- You need confidence in shutdown, clipboard, or terminal restoration.
- A demo/media pipeline claims to exercise the real UI.

## Test pyramid

| Layer | What it proves | Speed |
|---|---|---|
| Pure view-model/unit | status classification, column budgeting, fingerprints, prefs, export allowlist, trace resolution | ms |
| Headless Textual (`app.run_test`) | composition, geometry, focus, keys, selection, lazy views, resize | 100 ms–2 s |
| Feed/race tests | scope capture, stale snapshot discard, prefetch bounds, pagination reset | ms |
| Real PTY/subprocess | SIGINT during cleanup, exit code, terminal restoration | seconds |
| Media/visual checks | captures contain the right scene, logo, prompts, indentation | seconds–minutes |

Headless tests do **not** prove real-terminal rendering, clipboard integration,
contrast in a user's emulator, or screen-reader behavior. Say so.

## Start with the core flow

Write this test before the redesign, not after it breaks:

> All concurrently running agents appear in the default view; each selected
> agent shows its recorded prompts and current activity; MCP calls from every
> running session appear in MCP Calls; the same assertions pass at 80×24.

Agenturm's layout refactor silently broke this. The user had to point it out.
The regression test now uses three running agents (two Codex, one OpenCode),
asserts all three rows, both prompts per agent, current activity, and all three
MCP calls, then repeats the prompt/activity checks after `Enter` at 80×24.

If a redesign cannot pass this, stop redesigning.

## Geometry tests

Assert semantic relationships, not exact screenshots:

```python
async with app.run_test(size=(180, 48)) as pilot:
    await pilot.pause()
    results = app.query_one("#results-agents")
    inspector = app.query_one("#agent-bottom")
    assert results.region.y == inspector.region.y
    assert inspector.region.x >= results.region.right
    assert inspector.size.width >= 36
    assert app.query_one("#controls").region.y >= app.query_one("#pages > Tabs").region.bottom
    assert results.region.y == 9          # content starts by row 9 at 120x30+
```

Useful assertions:

- content start row and panel bottom alignment
- list/inspector width split
- header content fits without clipping
- ≥6 two-line rows at 80×24
- 12 agents remain in the scrollable table; no artificial cap
- footer/picker/back button visible and not covered
- column visibility after resize (`visible_columns`)
- selection key preserved across resize
- theme colors resolved to expected semantic roles

Avoid brittle pixel coordinates unless the layout contract names them (e.g.
"content starts by row 9").

## Size and theme matrix

At minimum, use an example matrix like this (adapt to the app's target sizes):

- **Wide:** 180×48, 160×48
- **Standard:** 140×42, 120×40, 120×30
- **Narrow:** 100×30, 96×30
- **Compact:** 80×24
- **Small:** 60×18, 50×18
- **Height stress:** 120×18, 80×18

Exercise:

- all themes (including light/bright and monochrome/`NO_COLOR` if supported)
- long task titles, long commands, unbroken tokens, mixed-width Unicode
- empty → populated transitions
- 12+ agents in the scrollable list
- loading, no matches, source unavailable, metadata-only, truncated history

## Keyboard and focus tests

```python
await pilot.press("down")
assert app.selected_source == "source-2"
await pilot.press("tab")
assert app.focused is not table
await pilot.press("shift+tab")
assert app.focused is table
await pilot.press("enter")
assert inspector.display
await pilot.press("escape")
assert results.display
```

Test:

- arrows move rows without waiting for I/O
- `Tab`/`Shift+Tab` move through visible controls in spatial order
- `Enter` and `e` both open; `Esc` returns one layer
- clicking a row selects and opens
- `/` focuses search; typing does not trigger shortcuts
- `t` works on every view or reports no linked trace
- `p` pauses display but collection continues
- `d` diagnostics and `x` export return to the prior context
- focus is restored after a modal closes

## Race and state tests

These are the highest-value tests in a live cockpit:

| Scenario | Expected |
|---|---|
| Toggle Prompts while a poll is in flight | Old response discarded; "Filtering…" until matching data |
| Select session A, then B before A's detail returns | A's evidence never appears under B |
| Refresh while a row is selected | Same stable ID selected; scroll preserved |
| Hidden view receives new data | No render work; latest data on activation |
| Empty start, then rows arrive | Order rebuilds; rows are not dropped |
| Priority change while navigating | Order frozen; Apply control appears; selection preserved |
| Resize while expanded | Text rewraps at new width; selection/expansion preserved |
| Metric selected, `t` pressed | Exemplar resolved only within that instrument/history |
| Tab switch after trace selection | Same span selected after return |
| Pagination + filter change | Cursor resets; old page cannot leak |

Use a `ManualFeed`/`FakeFeed` with deterministic synthetic records and a way to
stop the refresh timer.

## Resource-budget tests

Deterministic assertions beat machine-dependent timings:

- unchanged status text does not request a repaint
- one changed cell does not repaint the whole row
- hidden view performs no render work
- inventory queries are cached across refreshes; filter change bypasses cache
- feed prefetch is parallel, deduplicated, and capped
- response size is rejected before JSON decode
- watcher/OpenCode/cache budgets are enforced
- derived refresh stays below an allocation bound on a large fixture

Do not assert "refresh is under 50 ms" on CI. Assert work limits and index use.

## Real-PTY tests

Headless mode cannot prove shutdown or clipboard. Use a subprocess/PTY test:

1. launch the app from the checkout;
2. wait for the UI;
3. press `q`;
4. send Ctrl-C while HTTP shutdown is blocked;
5. assert exit code 0, no traceback, terminal restored.

Also test repeated interrupts during cleanup and normal `q` without Ctrl-C.

## Media tests

The demo is another client of the UI contract. Test it:

- `FakeFeed` implements every `Snapshot` field the app reads (a missing
  `activity_prompts` left the Prompts scene stuck on "Filtering…");
- captures contain the expected prompts, MCP evidence, and indented JSON;
- closing logo is the canonical asset, not terminal block art;
- video dimensions are even (odd height caused a one-pixel H.264 stretch);
- duration, frame count, resolution, and file size are in range;
- README capture is legible at GitHub's content width.

## CI shape

- run the pure/unit and headless suites on every change;
- run integration/interop jobs separately;
- run the full suite with a generous timeout (discovery can exceed two minutes);
- run `git diff --check` and `compileall`;
- keep a real-PTY shutdown job if the platform allows it;
- do not let a flaky visual test mask a behavioral failure.

## Failure notes

- **Don't weaken a behavior assertion to fit a lazy-render change.** If a hidden
  view is now empty by design, activate it first; do not remove the assertion
  that its selected span survives.
- **A headless pass is not a terminal pass.** Report what was not verified.
- **Verify the artifact under test.** Agenturm's "old logo" was a stale global
  `uv tool` install pinned to an older commit; restarting the app was not enough.
  Run from the checkout (or reinstall and confirm the version) before diagnosing
  a UI regression.
- **Screenshots are evidence, not tests.** They cannot catch stale data or focus
  loss.
- **A fake feed is a contract.** When the real `Snapshot` changes, update every
  fake and demo harness.
- **Timing tests are flaky.** Assert budgets and indexes, not wall-clock p95.
- **A layout test that only checks "things fit" misses meaning.** Assert the
  core data is still visible.

## Case study

Agenturm's exact regression list, sizes, and failure modes are in
[`references/agenturm-test-matrix.md`](references/agenturm-test-matrix.md). They
are an example suite, not a required template.

## Related skills

These are separate skills. Naming one here does **not** load it; use your host's
skill-loading mechanism.

- `terminal-cockpit-design` — the acceptance criteria to test.
- `textual-tui-engineering` — the implementation patterns under test.
- `monitoring-performance-budgets` — the resource claims the tests protect.

## Checklist

- [ ] Core multi-agent flow test exists and passes at wide + 80×24.
- [ ] Geometry assertions for content start, split, alignment, and visibility.
- [ ] Size/theme matrix exercised.
- [ ] Keyboard/focus/Esc/typing/Enter/e/click tests.
- [ ] Stale-filter, selection, hidden-view, empty-start, reorder, resize races.
- [ ] Trace/exemplar identity tests.
- [ ] Repaint/resource-budget tests.
- [ ] Real-PTY `q` + Ctrl-C shutdown test.
- [ ] Fake feed matches the current Snapshot contract.
- [ ] Media frames visually verified and synthetic data labeled.
- [ ] Full suite + diff/compile checks run.
- [ ] Unverified real-terminal/clipboard/a11y items stated honestly.
