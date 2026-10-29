# Hidden-pane and stale-response example

A small runnable/tested companion to the inspector and live-feed sections of
`SKILL.md`.

## Tested versions

- Python 3.13.5
- Textual **8.2.8**
- Rich **15.0.0**

## Run

```bash
python -m pip install -r ../incremental_table/requirements.txt
python -m unittest -v
```

There is no interactive demo; this example is about two invariants:

1. A `RichLog` updated while hidden or at width 0 must not cache one-character
   lines. Cache the text and render it when the pane is visible and measured.
2. An async detail response must be tied to a request generation. `A -> B -> A`
   must reject the first A response even though its field values match the
   current A scope again.

`RequestGate` is deliberately independent of Textual so it can be unit-tested
without async timing. `DetailPane` is exercised against a real headless
`RichLog`.
