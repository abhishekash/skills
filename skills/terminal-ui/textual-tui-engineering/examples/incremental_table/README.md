# Incremental DataTable example

A runnable, tested implementation of the incremental `DataTable` update pattern
described in `SKILL.md`.

## Tested versions

- Python 3.13.5
- Textual **8.2.8**
- Rich **15.0.0**

This is a tested combination, not a claim of broad compatibility across Textual
releases. Check the `DataTable` API before using it with another major version.

## Run

```bash
python -m pip install -r requirements.txt
python demo.py
```

Keys: `a` append, `d` remove last, `u` change content, `t` toggle style,
`i` invalidate, `q` quit.

## Test

```bash
python -m unittest -v
```

The suite covers:

- empty → populated (rebuild)
- append, removal, reorder (rebuild)
- unchanged data (no cell updates)
- changed content (one cell update)
- style-only change
- row-height change (rebuild)
- explicit theme/projection invalidation
- selection by stable key, and fallback when the selected key disappears
- an injected update failure that remains retryable
- a valid scroll offset after a rebuild
- the demo app itself

## What the example does not do

- It does not implement column resizing or responsive column dropping. Call
  `invalidate()` after changing the projection.
- It does not implement RichLog inspector reflow. The skill's `SKILL.md`
  describes that pattern; a separate example may add it.
- It uses an integer `height_for` callback rather than measuring rendered
  wrapped cells. In a real app, derive height from the actual column widths and
  invalidate on resize.

## Contract

`TableProjection.apply()` returns `unchanged`, `updated`, or `rebuilt`.

- The signature covers displayed content, Rich base styles and spans, row height,
  and an explicit generation bumped by `invalidate()`.
- The signature is recorded only after a successful update.
- Selection is by stable key. If the key disappears, the nearest valid row is
  selected.
- New or removed keys always take the rebuild path; existing row heights are not
  accessed before key compatibility is established.
