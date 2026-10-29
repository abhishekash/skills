# Ingestion task 2 — fair progress through a backlog

## Context

`build_backlog.jsonl` begins with one oversized record followed by 40 valid
records. A bounded reader that retries the oversized prefix forever will never
reach the tail.

## Goal

Implement fair, resumable progress across repeated polls.

## Required behavior

- The oversized head does not permanently starve later records.
- Repeated polls eventually ingest all 40 valid records.
- A changed record behind the cursor is still observed.
- Progress state is bounded (no unbounded per-record history).
- Diagnostics show backlog/progress and skipped counts.
- The reader remains read-only and content-free in diagnostics.

## Checks

Use `evals/checks/ingestion_contract.py` with the `read_once` contract from task
1. It loops repeated polls against `build_backlog.jsonl` and fails if the tail is
not reached.

## Deliverable

A reader implementation with an explicit cursor/digest and tests for repeated
polls, starvation, and a changed record behind the cursor.

## Completion

All valid tail records arrive; the huge head does not loop forever; a changed
record behind the cursor is seen; diagnostics are content-free.

## Constraints

- Do not "solve" this by reading the whole file into memory.
- Do not make the oversized record omission silently permanent unless documented;
  either resume fairly or state the cap.
- Synthetic data only.
