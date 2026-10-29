#!/usr/bin/env python3
"""Prepare paired with/without-skill evaluation runs and optionally execute a command."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
SKILLS = {
    "textual": ROOT / "skills/terminal-ui/textual-tui-engineering",
    "ingestion": ROOT / "skills/agent-observability/local-agent-ingestion",
    "status": ROOT / "skills/agent-observability/agent-session-status",
}


def copy_fixture(fixture: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for item in fixture.iterdir():
        if item.name in {"__pycache__", ".git"} or item.suffix == ".pyc":
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare paired evaluation runs.")
    parser.add_argument("--flagship", choices=sorted(SKILLS), required=True)
    parser.add_argument("--fixture", required=True, help="path relative to evals/")
    parser.add_argument("--task", required=True, help="path relative to evals/")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--out", required=True)
    parser.add_argument("--command", help="command template; {dir} is the run directory")
    args = parser.parse_args()

    fixture = (EVALS / args.fixture).resolve()
    task_path = (EVALS / args.task).resolve()
    skill = SKILLS[args.flagship]
    if not fixture.is_dir():
        print(f"error: fixture not found: {fixture}", file=sys.stderr)
        return 2
    if not task_path.is_file():
        print(f"error: task not found: {task_path}", file=sys.stderr)
        return 2
    if args.runs < 1:
        print("error: --runs must be >= 1", file=sys.stderr)
        return 2

    out = Path(args.out).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        print(f"error: output directory is not empty: {out}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    task_text = task_path.read_text(encoding="utf-8")
    records = []

    for run in range(1, args.runs + 1):
        for arm in ("with-skill", "without-skill"):
            run_dir = out / f"run-{run:02d}" / arm
            copy_fixture(fixture, run_dir)
            (run_dir / "TASK.md").write_text(task_text, encoding="utf-8")
            if arm == "with-skill":
                shutil.copytree(skill, run_dir / "skill")
            record = {
                "run": run,
                "arm": arm,
                "flagship": args.flagship,
                "fixture": str(fixture.relative_to(EVALS)),
                "task": str(task_path.relative_to(EVALS)),
                "directory": str(run_dir),
                "command": None,
                "exit_code": None,
                "duration_seconds": None,
                "stdout": None,
                "stderr": None,
            }
            if args.command:
                command = args.command.replace("{dir}", str(run_dir))
                started = time.monotonic()
                try:
                    completed = subprocess.run(
                        command,
                        shell=True,
                        cwd=run_dir,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=1800,
                    )
                    record["exit_code"] = completed.returncode
                    record["stdout"] = completed.stdout
                    record["stderr"] = completed.stderr
                except subprocess.TimeoutExpired as exc:
                    record["exit_code"] = "timeout"
                    record["stdout"] = exc.stdout
                    record["stderr"] = exc.stderr
                record["duration_seconds"] = round(time.monotonic() - started, 3)
                record["command"] = command
            records.append(record)

    (out / "results.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(records)} runs in {out}")
    print("Grade them with the task's checks and the independent rubric.")
    if not args.command:
        print("No --command supplied; run your agent manually in each directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
