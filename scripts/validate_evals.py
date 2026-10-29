#!/usr/bin/env python3
"""Validate the evaluation suite structure and activation-case counts."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
FLAGSHIPS = {
    "textual": "textual-tui-engineering",
    "ingestion": "local-agent-ingestion",
    "status": "agent-session-status",
}
FIXTURES = {
    "textual": "fixtures/textual_order_board",
    "ingestion": "fixtures/ingestion_forge",
    "status": "fixtures/status_kiln",
}


def main() -> int:
    errors: list[str] = []
    for name in ("README.md", "harness.py", "results/PENDING.md", "results/TEMPLATE.md"):
        if not (EVALS / name).is_file():
            errors.append(f"evals/{name}: missing")
    for flagship, skill in FLAGSHIPS.items():
        tasks = sorted((EVALS / "tasks" / flagship).glob("[0-9][0-9]-*.md"))
        if len(tasks) < 3:
            errors.append(f"evals/tasks/{flagship}: expected at least 3 tasks, found {len(tasks)}")
        activation = EVALS / "tasks" / flagship / "activation.md"
        if not activation.is_file():
            errors.append(f"evals/tasks/{flagship}/activation.md: missing")
        else:
            text = activation.read_text(encoding="utf-8")
            yes = text.split("## Should activate", 1)[-1].split("## Should not activate", 1)[0]
            no = text.split("## Should not activate", 1)[-1]
            if len(re.findall(r"^\d+\.\s+", yes, re.M)) < 2:
                errors.append(f"{activation}: expected at least 2 should-activate cases")
            if len(re.findall(r"^\d+\.\s+", no, re.M)) < 2:
                errors.append(f"{activation}: expected at least 2 should-not-activate cases")
        rubric = EVALS / "rubrics" / f"{flagship}.md"
        if not rubric.is_file():
            errors.append(f"evals/rubrics/{flagship}.md: missing")
        fixture = EVALS / FIXTURES[flagship]
        if not fixture.is_dir():
            errors.append(f"evals/{FIXTURES[flagship]}: missing fixture directory")
        elif not (fixture / "README.md").is_file():
            errors.append(f"evals/{FIXTURES[flagship]}: missing fixture README")
        source = ROOT / "skills"
        matches = list(source.rglob(f"{skill}/SKILL.md"))
        if not matches:
            errors.append(f"skill not found: {skill}")
    checks = EVALS / "checks"
    for name in ("textual_contract.py", "ingestion_contract.py", "status_contract.py", "README.md"):
        if not (checks / name).is_file():
            errors.append(f"evals/checks/{name}: missing")

    if errors:
        print("Evaluation validation failed:\n", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("Validated evaluation suite:")
    for flagship in FLAGSHIPS:
        tasks = len(list((EVALS / "tasks" / flagship).glob("[0-9][0-9]-*.md")))
        print(f"  ✓ {flagship}: {tasks} tasks + activation + {FIXTURES[flagship]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
