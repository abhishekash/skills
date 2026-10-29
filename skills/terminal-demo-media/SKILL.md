---
name: terminal-demo-media
description: Produce an honest, legible demo GIF or MP4 for a terminal UI from real captures — GitHub README sizing, synthetic data, canonical logo rendering, reproducible storyboard, and visual QA. Use when recording a TUI demo for a README, website, or profile, or when a demo shows the wrong logo, empty scene, or unreadable text.
---

# Terminal demo media

A TUI demo is a product claim. It should show the real interface, with synthetic
data, at a size a human can actually read. Most demo failures are not encoding
problems; they are claims the app cannot support or assets that were drawn by
hand instead of rendered from source.

## When to use

- Recording a README/site/profile walkthrough.
- The demo is unreadable after GitHub scales it.
- The logo/tower/mark in the capture looks wrong.
- A scene is empty ("Filtering…", "No data") despite the app working.
- The video is stretched, huge, or too long.
- A release changes the header/layout and the old demo is stale.

## Rules

1. **Capture the real TUI.** Drive the actual app through its keyboard actions
   and synthetic data. Do not build a separate HTML mock.
2. **Use synthetic data and label it.** Never read personal prompts, local agent
   logs, a real receiver, or a real database. No paid model calls.
3. **Show a real investigation, not a feature montage.** A useful sequence:
   overview → prompts → failed tool call → evidence → linked trace → identity.
4. **Don't claim a fix that did not happen.** Agenturm's demo showed an HTTP 403
   rate-limit error and explicitly did not claim checkout was fixed.
5. **Render brand assets from the canonical source.** Do not hand-draw a logo in
   terminal block art if the brand has an SVG.
6. **Design for the destination width.** GitHub renders README images at roughly
   840 px; a wider capture does not make text bigger.

## README legibility

GitHub caps inline README media at its content width. A 148-column terminal
scaled into ~840 px is tiny. The fix is to reduce the terminal grid so the text
fills the frame:

- Wide/video capture: ~148×46.
- README capture: **100×42**.
- Compose a README-specific frame that fills the width; remove 16:9 margins.
- Output ~1600 px wide, 12 fps, 256-colour palette.
- Keep duration short (Agenturm: 29 s full video, 19 s GIF), file size ~3–4 MiB.
- Link the full-resolution video under the animation.

Agenturm's 100×42 README capture made terminal text ~50% larger at GitHub's
rendered width. The GIF was 1600×1580, 19 s, 228 frames, 3.64 MiB.

## Synthetic feed contract

The demo harness is a client of the app. It must implement every field the UI
reads.

Agenturm added `Snapshot.activity_prompts` for the Prompts filter. The synthetic
`FakeFeed` did not set it, so the demo's Prompts scene was stuck on "Filtering…"
while the real app worked. The fix was both a feed change and a media test.

Rules:

- Keep `FakeFeed`/`ManualFeed` in sync with the production `Snapshot`.
- Assert the expected scene has actual rows, not a loading/empty placeholder.
- Use stable synthetic IDs and timestamps for reproducible captures.
- Do not let a demo-specific shortcut bypass the real view model.

## Storyboard

| Time | On screen | Action |
|---|---|---|
| 0–5 s | Every session, one place | Agents overview with 3 runtimes |
| 5–10 s | Read the prompts | Focus a session, enable Prompts |
| 10–14 s | Which call failed | MCP Calls list |
| 14–20 s | Open the evidence | Expand failed call + indented JSON |
| 20–26 s | Follow the call | Linked execution tree |
| 26–29 s | Identity | Canonical tower/wordmark + command |

Every scene should answer a question. If a scene only shows chrome, cut it.

## Pipeline

```text
1. Build brand assets from SVG source.
2. Capture the real TUI at the chosen grid (wide and README sizes).
3. Save per-step screenshots (and a compact 80×24 shot for docs).
4. Compose frames (no in-memory full video).
5. Encode H.264 with even dimensions.
6. Generate the GIF from the README-layout video.
7. Visually verify key frames.
8. Record duration, frame count, resolution, file size.
9. Regenerate README/site/profile assets from the same captures.
```

Agenturm's reproduction commands (adapt paths):

```bash
uv run --with cairosvg python scripts/build_brand_assets.py
uv run --with cairosvg python scripts/capture_investigation_video.py \
  --output /tmp/opencode/agenturm-capture \
  --screenshots media/screenshots --readme-image media/agenturm-terminal.png
uv run --with cairosvg --with pillow --with imageio-ffmpeg \
  python scripts/compose_investigation_video.py \
  --captures /tmp/opencode/agenturm-capture --output media/agenturm-demo.mp4
uv run --with cairosvg python scripts/capture_investigation_video.py \
  --size 100x42 --output /tmp/opencode/agenturm-readme
uv run --with cairosvg --with pillow --with imageio-ffmpeg \
  python scripts/compose_investigation_video.py --layout readme \
  --captures /tmp/opencode/agenturm-readme --output /tmp/opencode/agenturm-readme.mp4
uv run --with imageio-ffmpeg python scripts/make_readme_preview.py \
  --video /tmp/opencode/agenturm-readme.mp4 --output media/agenturm-demo.gif
```

## Visual QA

Verify stills, not only the encoded file:

- closing logo matches `media/brand/icon.svg` (circular deck, lens, mast);
- no malformed terminal block art in the header;
- Prompts scene contains both expected prompts, not "Filtering…";
- JSON is indented and readable;
- MCP evidence and linked trace are populated;
- compact 80×24 capture is legible;
- no clipping, overlap, or one-character wrapping;
- theme/contrast matches the shipping default;
- video is not stretched (even width/height);
- duration/frame count/size are within budget.

Keep a regression test for the feed/scene contract, not just a visual check.

## Brand assets

- Use the canonical SVG for the app icon, wordmark, hero, and social preview.
- In the terminal, prefer a text wordmark; terminal block art rarely reproduces
  a detailed mark at cell resolution.
- The demo compositor should render the closing logo directly from the SVG, not
  from a cached PNG that can drift.
- If the terminal no longer draws the logo, remove it from captures rather than
  preserving a stale malformed mark.
- Regenerate README/site/profile media from the same source when the header
  changes.

## Failure modes

| Anti-pattern | Result |
|---|---|
| 148-column capture in an 840 px README | Unreadable text |
| Hand-drawn terminal logo | Malformed/NSFW-looking mark |
| Cached PNG logo | Drifts from SVG |
| Synthetic feed misses a new Snapshot field | Empty/"Filtering" scene |
| Odd-height canvas | One-pixel H.264 stretch |
| Reading a real agent DB | Privacy leak; non-reproducible |
| Showing a fix that did not happen | False product claim |
| Recording before the UI is stable | Stale header/layout |
| Only checking the video, not frames | Logo/scene bug ships |
| Forgetting site/profile copies | Inconsistent brand |

## Case study

Agenturm's first demo GIF showed a narrow, malformed tower because the terminal
header used block art. The fix was not a GIF filter: the terminal capture was
changed to a text-only wordmark, and the closing tower is rendered directly from
the canonical SVG. The README capture was reduced from 148 to 100 columns so the
text grew ~50% at GitHub's width. A later layout change added a snapshot field;
the synthetic feed lagged, leaving the Prompts scene empty. That became a media
regression test. The final GIF was 1600×1580, 19 s, 228 frames, 3.64 MiB.

## Checklist

- [ ] Real TUI capture; synthetic data labeled.
- [ ] Storyboard shows a real investigation, not chrome.
- [ ] README capture sized for GitHub (~100 columns); full-res video linked.
- [ ] Canonical SVG used for brand renders; no hand-drawn terminal logo.
- [ ] Fake feed matches the current Snapshot contract.
- [ ] Key frames visually verified (logo, prompts, JSON, trace, compact).
- [ ] Even dimensions; duration/size/frame count recorded.
- [ ] Screenshots and site/profile media regenerated from the same source.
- [ ] No false claims; limitations stated.
- [ ] Media regression test covers the scene contract.
