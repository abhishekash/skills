# Behavioral evaluations

This directory contains the behavioral evaluation suite for the three flagship
skills:

- `textual-tui-engineering`
- `local-agent-ingestion`
- `agent-session-status`

**Status: pilot executed; replication pending.** A two-pair-per-task pilot on
2026-10-29 had zero functional delta (both arms passed every task), 12/12
correct activation decisions, and mostly larger with-skill patches in round 2. Packaging checks and executable example tests are
still not effectiveness evidence. No claim that the skills improve agent results
is made until repeated paired runs are executed and reported.

## What is here

```text
evals/
├── tasks/                 # prompts + acceptance checks per flagship
├── fixtures/              # independent synthetic projects/data
├── rubrics/               # independent scoring criteria
├── harness.py             # prepares paired with/without-skill runs
└── results/               # raw scores and PENDING.md
```

Each flagship has three representative tasks and four activation cases (two
should activate, two should not). The fixtures use other domains — orders, build
logs, and batch jobs — not Agenturm sessions, IDs, or schema.

## Run a paired evaluation

1. Pick a task and fixture. Example:

   ```bash
   python3 evals/harness.py \
     --flagship textual \
     --fixture fixtures/textual_order_board \
     --task tasks/textual/01-incremental-rows.md \
     --runs 3 \
     --out /tmp/agenturm-eval-textual
   ```

2. The harness creates paired directories:

   ```text
   run-01/with-skill/
   run-01/without-skill/
   ```

   The only difference is the `skill/` directory in the `with-skill` run. Both
   receive the same fixture, `TASK.md`, model, tools, permissions, and budget.

3. Run the same agent command in each directory, for example (replace with your
   harness's command):

   ```bash
   cd run-01/with-skill && agent run "Read TASK.md and implement it."
   ```

   Or pass a command template to the harness:

   ```bash
   python3 evals/harness.py ... \
     --command 'agent run "Read TASK.md and implement it."'
   ```

   The harness records stdout/stderr, exit code, and duration in
   `results.json`. It does not grade.

4. Apply the task's executable checks and the independent rubric. Run the checks
   from the run directory, not from this repository.

5. Record every run, including failures, timeouts, and exclusions. Do not drop a
   failed run because it is inconvenient.

## Controls

- Same model and version in both arms.
- Same tools, permissions, starting fixture, and budget.
- Fresh working directory per run.
- The `without-skill` arm must not contain the skill text or references.
- The `with-skill` arm contains the complete skill directory (SKILL.md + its
  references/examples), not just a copied summary.
- Multiple paired runs (at least 3 preliminary; more for a stronger claim).
- Report medians/paired deltas and raw runs; do not report only the best run.

## Scoring

Primary:

1. Functional correctness on the task's executable checks.
2. Regressions in the baseline fixture.

Secondary:

3. Unnecessary changes (files, dependencies, unrelated rewrites).
4. Completion effort/time and token usage when available.
5. Blind rubric for judgment-based quality.

Do not reward copying the skill's terminology, adding prose, or touching more
files. A skill that produces a correct, smaller patch wins.

## Executable checks

The suite includes independent contract checks in `evals/checks/`:

- `textual_contract.py` — order board, Textual 8.2.8.
- `ingestion_contract.py` — Forge reader contract.
- `status_contract.py` — Kiln classifier contract.

They are expected to fail on the untouched fixtures (the baseline is
intentionally naive) and pass only after the task's behavior is implemented.
They are run against a prepared run directory, not against the repository's
packaging CI.

## Activation cases

Run the activation prompts separately, without giving the agent the skill name as
a hint. Judge semantic selection from the prompt, not keyword presence.

- `tasks/<flagship>/activation.md` lists two should-activate and two
  should-not-activate prompts with the expected decision and rationale.

## Reporting

Publish:

- the exact model/version, tools, fixture, task, and run count;
- raw per-run scores and failures;
- the paired delta and its direction;
- cases where the skill performs worse;
- a statement of what the suite does not establish.

Use [`results/TEMPLATE.md`](results/TEMPLATE.md). Read the pilot in
[`results/PILOT-2026-10-29.md`](results/PILOT-2026-10-29.md); keep
[`results/PENDING.md`](results/PENDING.md) as the status until replicated.

## Limits

- Three tasks per skill is preliminary evidence, not proof of universal
  improvement.
- Executable checks measure behavior on these fixtures; they do not cover every
  runtime or terminal.
- A blind rubric is still judgment; two independent reviewers are better than one.
- The pilot is **preliminary** and has only two pairs per task.
