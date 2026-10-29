# Changelog

## 1.1.0 — 2026-10-29

- Reorganized the pack into three layers: `terminal-ui` (featured),
  `agent-observability` (truth and data), and `operations` (performance and
  privacy).
- Added category/featured metadata to `skills.json`.
- Updated Claude marketplace and plugin skill paths for the categorized layout.
- Kept installed skills flat (`<target>/<skill-name>/SKILL.md`) for compatibility.

## 1.0.0 — 2026-10-29

- Initial release extracted from the Agenturm terminal-cockpit effort.
- Nine skills: cockpit design, Textual engineering, TUI regression testing,
  session status, local ingestion, SQLite telemetry, performance budgets,
  local-first privacy, and terminal demo media.
- Added the full reconstruction in
  [`docs/agenturm-tui-retrospective.md`](docs/agenturm-tui-retrospective.md).
- Added a dependency-free installer (`install.sh` / `scripts/install.py`),
  `skills.json` manifest, Claude Code plugin/marketplace manifests, and a
  Codex plugin manifest.
- Added CI validation for frontmatter, naming, routing language, required
  sections, links, manifest consistency, and installer dry runs.
