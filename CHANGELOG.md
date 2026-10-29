# Changelog

## 1.2.1 — 2026-10-29

- Scoped the evaluation checks per task (`EVAL_TASK=1|2|3`) so a task-2 solution is
  not penalized for not implementing task 1.
- Added style-only/unchanged checks to the Textual task-1 fixture and baseline
  detail behavior that fails tasks 2/3 until fixed.
- Added `recorded-failure` and `completed-only` status controls.
- Executed two paired repetitions across all nine evaluation tasks:
  **36/36 arms passed**, **12/12 activation decisions correct**, **zero functional
  delta**; patch size was mixed in round 1 and mostly larger with the skill in
  round 2. Results are preliminary and are not an effectiveness claim.
- Published the pilot report and raw scores in `evals/results/`.

## 1.2.0 — 2026-10-29

- **Installer safety:** dry runs are non-mutating for install, replace, remove,
  destination-root creation, files, directories, valid symlinks, and dangling
  symlinks. Added snapshot-based regressions.
- **Executable Textual examples:** incremental `DataTable` projection and
  hidden/async detail examples, tested with Python 3.13.5, Textual 8.2.8, Rich
  15.0.0. The `fill()` schematic now checks key compatibility before row heights,
  uses a content/style/height/generation signature, records only successful
  updates, and defines selection fallback.
- **Portable instructions:** all nine skills now state purpose, inputs, workflow,
  deliverable, and completion; classify guidance as invariant/default/case study;
  label numeric limits; and explain that naming a related skill does not load it.
- **References:** Agenturm-specific measurements, runtime observations, schema
  choices, and media pipeline details moved to directly linked reference files.
- **Evaluation suite:** three flagship tasks each, activation cases, independent
  order/build/job fixtures, executable contract checks, rubrics, and a paired-run
  harness. Comparative runs are pending; no effectiveness claim is made.
- **Validation:** removed arbitrary length/heading-template checks; added
  operating-contract, portability, category, packaged-resource, installed-example,
  and evaluation-suite checks.

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
