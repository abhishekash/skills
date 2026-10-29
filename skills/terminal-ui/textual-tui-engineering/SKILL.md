---
name: textual-tui-engineering
description: Implement or repair a Textual TUI for live operational data, especially multi-pane cockpits with DataTables and RichLog inspectors. Use for layout/focus problems, resize reflow, stale rows, lost selection, hidden-tab rendering, repaint budgets, or clean shutdown in a Textual app.
---

# Textual TUI engineering

The hard part of a Textual cockpit is not composing widgets. It is keeping a
mutable live feed, a cursor, a scroll position, filters, and expensive evidence
rendering consistent while the user navigates.

This skill is the implementation counterpart to `terminal-cockpit-design`. It
assumes the IA and status language are decided.

## When to use

- Building a multi-pane Textual app with `DataTable`, `RichLog`, `Tabs`, and
  background polling.
- The screen rebuilds all hidden tabs on every refresh.
- Selection jumps, evidence from the previous row appears under a new title, or
  resize reflows with old widths.
- A filter change is overwritten by an in-flight response.
- Ctrl-C during quit prints a traceback.
- A layout change breaks a working feature.

## Architecture split

Keep four boundaries:

```text
collector / receiver      owns telemetry and status truth
        │  HTTP / local data
feed                      owns polling, scopes, immutable Snapshot
        │  Snapshot + stable IDs
view models               pure functions from records to display rows
        │
Textual app               owns composition, focus, navigation, rendering
```

- The feed thread performs I/O and publishes a whole `Snapshot`. Workers never
  mutate widgets or publish partial state.
- The UI thread consumes snapshots; it does not block on network or disk.
- View-model functions (`sources()`, `task_text()`, `agent_status()`,
  `attention_evidence()`) are testable without an app.
- Navigation state is explicit: page, scope, filters, selected stable ID,
  pagination cursor, scroll anchor, focus target, expansion.

If all of this lives in one 160 KB file, extract at the seams that change for
different reasons, not in one rewrite.

## App shell and tabs

A three-row shell beats a stack of nested containers:

```python
def compose(self):
    with Horizontal(id="masthead"):
        yield Static(masthead(), id="brand")
        yield Static("", id="stat-sessions")
        yield Static("", id="stat-attention")
        yield Static("○ Connecting", id="connection")
    with Horizontal(id="navigation"):
        with CockpitTabs(initial="agents", id="pages"):
            ...
        yield Select(..., id="more-views")
    yield Static("", id="health")
```

**Textual constraint:** `TabbedContent` requires its `Tabs` widget to remain a
direct child. Do not wrap or replace it to force a one-row navigation bar; the
first attempt broke tab activation. Dock the secondary-view picker alongside it
and keep `Tabs` intact.

For a shared control row under the tabs, subclass `TabbedContent` and inject it
after the `Tabs` child:

```python
class CockpitTabs(TabbedContent):
    def compose(self):
        for widget in super().compose():
            yield widget
            if isinstance(widget, Tabs):
                yield self.app.scope_controls()
```

CSS is part of behavior. Keep one border per panel, one-cell padding, and no
unexplained spacer rows. A control with `height: 1` plus multiple margin lines
can consume four rows before content.

## DataTable projection

Do not let `DataTable` own column layout. Build a projection layer:

- `column_specs`: `(title, width, flex_weight)`
- `DROP_ORDER[table_id]`: lowest-value columns disappear first
- `column_layout(table_id, specs, width)` returns visible original indices and
  widths
- `full_rows[key]`: complete logical row, independent of visible columns
- `visible_columns`: tuple of original indices
- `preview_height(values)`: recompute wrapped height from current widths

Drop order should preserve subject and status. In Agenturm:

```python
DROP_ORDER = {
    "agent-table": (2,),                  # drop Updated, keep Task/State
    "activity-table": (1, 0),             # drop Type, Time before Action
    "mcp-servers": (4, 3, 1, 2),
    "trace-table": (3, 2),
}
```

The resizing algorithm:

1. Remove columns in drop order until `sum(width + 2) + 1 <= width`.
2. Shrink the widest remaining columns until they fit.
3. Distribute spare cells by flex weight.
4. Set the new widths **before** rebuilding rows, so previews wrap against the
   new geometry.
5. Preserve cursor row and scroll offset by stable row key.

```python
def fit_columns(self):
    visible, widths = column_layout(self.id, self.column_specs, self.scrollable_content_region.width)
    if widths == self.column_widths and visible == self.visible_columns:
        return
    rows = list(self.full_rows.items())
    selected = self.cursor_row
    scroll = self.scroll_offset
    self.clear(columns=True)
    for index, width in zip(visible, widths):
        self.add_column(self.column_specs[index][0], width=width, key=str(index))
    self.column_widths = widths          # before add_row, so previews rewrap
    self.visible_columns = visible
    for key, values in rows:
        self.add_row(*values, key=key)
    if rows:
        self.move_cursor(row=min(selected, len(rows) - 1), scroll=False)
    self.scroll_to(x=0, y=scroll.y, animate=False)
```

Two-line rows: a single cell renderable with `Text` containing `\n`, and a
`preview_height` that measures the wrapped lines. Do not put the second line in a
separate hidden column.

## Incremental fill

Repainting the whole table on every refresh causes flicker, loses selection, and
shows up as high CPU. Keep a signature of the logical rows; if unchanged, return.
If keys and row heights match, update only changed cells.

```python
def fill(self, name, rows, preserve=None):
    signature = tuple((key, tuple(str(v) for v in values)) for key, values, _ in rows)
    if self.table_signatures.get(name) == signature:
        return
    self.table_signatures[name] = signature
    table = self.query_one("#" + name, DataTable)
    selected = preserve or current_key(table)
    scroll, old_index = table.scroll_offset, table.cursor_row

    with table.prevent(DataTable.RowHighlighted):
        keys_match = [k.value for k in table.rows] == [k for k, _, _ in rows]
        heights_match = all(table.rows[k].height == table.preview_height(v) for k, v, _ in rows)
        if keys_match and heights_match:
            for key, values, _ in rows:
                table.full_rows[key] = values
                for column, value in zip(table.columns, table.project(values)):
                    previous = table.get_cell(key, column)
                    if previous != value or getattr(previous, "style", None) != getattr(value, "style", None):
                        table.update_cell(key, column, value)
        else:
            table.clear()
            for key, values, _ in rows:
                table.add_row(*values, key=key)
        if rows:
            index = next((i for i, (k, _, _) in enumerate(rows) if k == selected), 0)
            table.move_cursor(row=index, scroll=False)
            table.scroll_to(x=scroll.x, y=max(0, scroll.y + index - old_index), animate=False)
```

**Rich Text equality excludes its base style.** Compare `previous.style` too, or
a theme change will not recolor otherwise identical cells.

## Inspector and reflow

`RichLog` caches rendered strips. A width change must invalidate those strips,
and a theme change must translate the cached styles.

- Give the inspector a signature `(title, fields, sections, overview)`; skip
  identical writes.
- Only clear/write when the signature changes.
- On resize, save scroll offsets, clear selection, invalidate signatures, refresh,
  then restore scroll after the next refresh.
- Reflow after the **actual pane width** changes, not the app width. `App.on_resize`
  fires before child layout.
- Use `call_after_refresh` for work that needs final geometry.

```python
def schedule_inspector_reflow(self):
    if self.inspector_reflow_pending:
        return
    self.inspector_reflow_pending = True
    self.call_after_refresh(self.finish_inspector_reflow)

def reflow_inspectors(self):
    positions = {log.id: log.scroll_offset for log in self.query(SelectableRichLog)}
    self.screen.clear_selection()
    self.inspector_signatures.clear()
    self.last_update = -1
    self.refresh_data()
    self.call_after_refresh(lambda: [
        self.query_one("#" + name).scroll_to(x=p.x, y=p.y, animate=False)
        for name, p in positions.items()
    ])
```

**The hidden-pane bug:** an inspector update can arrive while the pane is hidden
and reports width 0. Rich caches one-character-wide lines; reopening at the same
width does not rebuild them. Guard against rendering when width is invalid, and
force a rebuild when the pane becomes visible.

```python
if self.size.width <= 0:
    self.pending_rebuild = True
    return
```

## Evidence rendering

Evidence is not plain text. Tool results arrive as nested JSON, JSON-encoded
strings, shell-wrapped heredocs, diffs, and one-key envelopes. Render them for
reading, not as `str(dict)`.

- Unwrap single-key envelopes such as `recorded_content`, `content`, `payload`,
  and `wrapper` without consuming the recursion budget or repeating the label.
- If a text field contains embedded JSON, pretty-print the JSON segments and keep
  surrounding prose as text.
- Pretty-print dict/list arguments and nested evidence with `indent=2`.
- Preserve `diff`/`patch` as a diff lexer, shell as bash, and Python as Python.
- Detect a shell heredoc and render the script body with the right language
  instead of dumping the whole command line.
- Depth-limit recursive rendering (Agenturm: 64) and cap displayed payloads.
- `RichLog.clear()` must also clear the current text selection; otherwise Ctrl+C
  after an update copies the previous event.
- Provide `plain_text` and `get_selection()` for copy actions, and strip trailing
  whitespace per line.
- If JSON is malformed or too deep, show the raw text with a clear truncation
  marker rather than raising.

The user-visible bug that drove this: "at times, session inspector renders like
this and json are not indented properly." The fix was in the evidence renderer,
not the layout.

## Live feed: immutable scopes and atomic snapshots

Capture every input that affects a response **before** I/O:

```python
@dataclass(frozen=True)
class FeedScope:
    service: str
    session_id: str
    query: str
    activity_query: str
    mcp_query: str
    errors_only: bool
    include_reviews: bool
    activity_prompts: bool
    selected_trace: str | None
    selected_span_id: str | None
    pinned_trace: bool

    @classmethod
    def capture(cls, feed):
        return cls(**{name: getattr(feed, name) for name in cls.__dataclass_fields__})
```

At the start of `refresh()`: `requested = FeedScope.capture(self)`.
Before publishing: `if requested != FeedScope.capture(self): discard`.

This fixes the class of bugs where a Prompts toggle, session scope change, or
trace pin is overwritten by an older response.

Concurrency:

- Prefetch only known independent reads.
- Cap workers and prefetch slots (Agenturm: 4 and 16).
- Dependent reads stay explicit.
- Workers return data; only the polling thread publishes.
- Cancel outstanding requests on shutdown.
- Cap response bytes before JSON decode (16 MiB in Agenturm).
- Verify stale scopes and pagination history before assignment.

```python
requests = RequestBatch(api, stop)
requests.prefetch(("/api/health", "/api/metrics", "/api/connections", ...))
health = get("/api/health")
...
if requested_scope != FeedScope.capture(self):
    return                    # discard older view
self.snapshot = Snapshot(...) # atomic publication
```

## Navigation and selection

- Key every table row by a stable ID, not row index.
- Store selected IDs (`selected_source`, `selected_activity`, ...), not positions.
- When a selected event is pushed off the live page, append the cached record so
  the inspector does not blank: `hold_selected()`.
- Before navigating to related evidence, remember a location:
  `{page, expanded, focus, scroll{id: offset}}`.
- Restore after refresh; if the record expired, explain and preserve context.
- Compute linked traces by exact identity first (event trace ID, session ID),
  then a recorded task match. Never pick the first trace from another
  instrument/session.
- Resolve metric exemplars only inside the selected instrument and loaded
  history.
- Freeze list order while navigating; queue reorder; apply on explicit refresh or
  re-entry. Preserve selection by ID.
- On empty→non-empty transition, rebuild the order; do not keep an empty frozen
  list.

## Focus and keys

- `AUTO_FOCUS` the primary table; restore it on page activation.
- `Tab`/`Shift+Tab` should move through visible controls in spatial order; test
  it, because a hidden/disabled control can silently trap focus.
- `Enter` and the expand key should both open the inspector; row click should
  select and open.
- `Esc` must consume one layer per press.
- Printable keys must not fire when an `Input` has focus.
- A shortcut shown in the UI must work on the current view or notify why. The
  Agenturm `t` key silently did nothing on the default Agents page because the
  handler only covered four other views. Fix: resolve the session's linked trace,
  jump to Traces, or say "No linked trace for this selection."
- `p` pauses **display updates** only; collection continues. Label and tooltip
  must say so.
- Copy: prefer the current text selection; otherwise the selected record; route
  to the OS clipboard in a worker and report fallback behavior honestly.

## Search

- Search is per-view. Keep a query dict keyed by page; do not clear another
  view's inventory or selection because one view is searching.
- Debounce remote searches (~300 ms) and capture the scope before the request.
- Show "Filtering…" until the returned snapshot's query matches the current
  input; otherwise a stale result looks like a new one.
- `Clear` appears only when there is a query; clearing focuses the input.
- `Esc` exits search before it collapses a panel or navigates back.
- Typing must not trigger single-key navigation.
- Preserve the query across refresh and view switches, but do not persist it.

## Repaint budget

- Update a status only if its text changed; otherwise return.
- Use one 0.5 s UI timer; the feed can poll at 2 s.
- Render only the active tab. Hidden tabs update from the latest snapshot when
  activated.
- Cache inventory/findings reads for ~5 s unless scope changes.
- Avoid rebuilding a table if rows and heights are unchanged.
- Do not animate continuously for "Working"; static text is enough.

## Theme changes

Textual themes do not retroactively restyle Rich strips already written to a
`RichLog`, nor `Text` objects cached in table rows. On theme change:

1. clear table signatures and span signatures;
2. reflow/rebuild inspectors;
3. translate cached Rich styles to the new semantic palette;
4. update syntax backgrounds;
5. verify contrast in every theme.

Keep semantic roles in one palette module shared by TCSS variables and Rich
styles.

## Shutdown

Interrupt safety is a property of the whole cleanup, not each `join()`.

```python
@contextmanager
def _ignore_cleanup_interrupts():
    main = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN) if main else None
    try:
        yield
    finally:
        if main:
            signal.signal(signal.SIGINT, previous)

def complete_cleanup(*callbacks):
    with _ignore_cleanup_interrupts(), ExitStack() as cleanup:
        for callback in reversed(callbacks):
            cleanup.callback(callback)
```

- Bound every thread join.
- Run later cleanups even if one fails.
- Make close idempotent.
- Cancel in-flight HTTP requests and interrupt sockets.
- Restore the previous SIGINT handler.
- Test a real PTY: press `q`, send Ctrl-C during blocked HTTP shutdown, expect
  exit 0 and no traceback. Also test repeated interrupts.

Three separate tracebacks in Agenturm came from three unbounded joins. Fixing
them one at a time did not fix the class; shielding the whole sequence did.

## Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Tabs stop activating | `Tabs` wrapped/replaced inside `TabbedContent` | Keep `Tabs` a direct child; dock controls beside it |
| Rows wrap with old width | Width set after adding rows | Set `column_widths` before rebuild |
| One-character inspector lines | Hidden pane updated at width 0 | Skip invalid width; rebuild on visibility |
| Theme change misses cached cells | Rich Text equality ignores base style; strips cached | Clear signatures; compare style; rebuild |
| Selection jumps after refresh | Selection stored by row index | Store stable ID; map back to index |
| Evidence from previous row | New title rendered before new evidence arrives | Clear/label loading; never reuse old log |
| Filter overwritten by poll | Scope not captured before HTTP reads | Immutable `FeedScope` compare-before-publish |
| Hidden tab stale | Lazy view never refreshed | Refresh active tab; on activation use latest snapshot |
| Timers fire after unmount | Queued messages | Guard with `self.query("#health")` / mounted check |
| Full row repaint | Rebuilding table on every cell change | Signature + per-cell update |
| Ctrl-C traceback | Unbounded join / unprotected cleanup | `complete_cleanup`, bounded joins, real-PTY test |

## Minimum test seam

Expose the seams the tests need:

- a `FakeFeed` / `ManualFeed` with the same `Snapshot` contract as production
  (including new fields such as `activity_prompts`);
- `persist_preferences=False` for headless tests so they never touch the user's
  config;
- deterministic synthetic records with stable IDs;
- a way to stop the refresh timer in tests;
- `run_test(size=(w, h))` for geometry and keyboard tests.

If a demo harness constructs a fake feed, it must implement every field the UI
reads. In Agenturm, a missing `activity_prompts` left the demo stuck on
"Filtering…" while the real app worked.

## Checklist

- [ ] Feed/view-model/UI boundaries separated.
- [ ] Tabs kept as a direct child; navigation docked beside it.
- [ ] Column projection with drop order; widths set before rows.
- [ ] Stable row keys and selected IDs.
- [ ] Signature-based fill; per-cell updates; no unchanged repaint.
- [ ] Inspector signature + post-layout reflow; hidden-pane guard.
- [ ] Immutable scope captured before I/O; stale snapshots discarded.
- [ ] Bounded concurrent prefetch; atomic snapshot publication.
- [ ] Lazy hidden views; activation uses latest data.
- [ ] Freeze order while navigating; explicit Apply.
- [ ] Linked trace/exemplar resolution by exact identity.
- [ ] Focus, Tab, Enter/e, Esc, typing guards, copy, pause verified.
- [ ] Theme change rebuilds cached strips and contrast passes.
- [ ] Whole-cleanup SIGINT shield; bounded joins; real-PTY test.
- [ ] Core multi-agent flow test passes at wide and 80×24.
