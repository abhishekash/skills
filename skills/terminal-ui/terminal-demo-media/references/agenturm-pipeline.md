# Agenturm demo-media pipeline (case study)

This is a **pinned historical reproduction**, not a runnable part of this skill.
The scripts and paths below belong to Agenturm and do not exist in an unrelated
repository. Use them as an adaptation reference.

## Pinned source

Agenturm repository at commit
[`1c01095`](https://github.com/abhishekash/agenturm/tree/1c01095) (2026-10-25)
contains the capture/compose scripts referenced by the skill. Verify the paths
still exist before using a newer commit.

Relevant files in that checkout:

- `scripts/build_brand_assets.py`
- `scripts/capture_investigation_video.py`
- `scripts/compose_investigation_video.py`
- `scripts/make_readme_preview.py`
- `scripts/render_terminal_demo.py`
- `media/brand/icon.svg`
- `docs/investigation-video.md`

## Required tools

- Python 3.11+
- `cairosvg`
- `pillow`
- `imageio-ffmpeg`
- DejaVu Sans and DejaVu Sans Mono fonts
- a real terminal/Textual environment capable of driving the app headlessly

## Commands (Agenturm paths)

```bash
uv run --with cairosvg python scripts/build_brand_assets.py
uv run --with cairosvg python scripts/capture_investigation_video.py \
  --output /tmp/agenturm-capture --screenshots media/screenshots \
  --readme-image media/agenturm-terminal.png
uv run --with cairosvg --with pillow --with imageio-ffmpeg \
  python scripts/compose_investigation_video.py \
  --captures /tmp/agenturm-capture --output media/agenturm-demo.mp4
uv run --with cairosvg python scripts/capture_investigation_video.py \
  --size 100x42 --output /tmp/agenturm-readme
uv run --with cairosvg --with pillow --with imageio-ffmpeg \
  python scripts/compose_investigation_video.py --layout readme \
  --captures /tmp/agenturm-readme --output /tmp/agenturm-readme.mp4
uv run --with imageio-ffmpeg python scripts/make_readme_preview.py \
  --video /tmp/agenturm-readme.mp4 --output media/agenturm-demo.gif
```

## Adaptation requirements

To reuse the approach in another repository:

1. Replace the capture driver with one that drives **your** real app and synthetic
   feed. Do not mock the UI in HTML.
2. Implement every field of your production snapshot in the synthetic feed. A
   missing field can leave a scene stuck on "Filtering…" or empty.
3. Use your canonical brand SVG (if any) for the closing mark; render from source,
   not from a cached raster.
4. Choose a capture grid for the destination. Agenturm used 148×46 for video and
   100×42 for the README because GitHub renders inline media at roughly 840 px.
5. Keep dimensions even before H.264; odd height caused a one-pixel stretch.
6. Use a bounded duration, frame rate, and palette; measure the final size.
7. Label the data synthetic. Never read personal logs/databases.
8. Verify frames, not just the encoded file: logo, prompts, JSON, trace, compact
   size.
9. Regenerate README/site/profile copies from the same captures.

## Measured output (Agenturm, 2026-10-24/25)

- README GIF: 1600×1580, 19 s, 228 frames, 3.64 MiB.
- Full walkthrough: 29 s, 148×46 source captures, 1920×1080 composed frames.
- README capture: 100×42; terminal text about 50% larger at GitHub's rendered
  width than the earlier 148-column capture.

These are example measurements, not quality targets for another app.
