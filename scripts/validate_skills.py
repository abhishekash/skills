#!/usr/bin/env python3
"""Zero-dependency validator for the Agenturm TUI skills repo."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROUTING_RE = re.compile(r"\bUse (?:when|for|before|after|during)\b", re.IGNORECASE)
REQUIRED_SECTIONS = ("## When to use", "## Checklist")
FAILURE_HEADINGS = ("## Failure modes", "## Failure notes", "## Pitfalls")


def parse_frontmatter(text: str, path: Path) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing opening frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: missing closing frontmatter")
    block = text[4:end]
    values: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}: malformed frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    errors: list[str] = []
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    if not skill_dirs:
        errors.append("no skill directories found")

    names: dict[str, Path] = {}
    for directory in skill_dirs:
        path = directory / "SKILL.md"
        if not path.is_file():
            errors.append(f"{directory}: missing SKILL.md")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 500:
            errors.append(f"{path}: body is too short")
        try:
            meta = parse_frontmatter(text, path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        name = meta.get("name", "")
        description = meta.get("description", "")
        if not name:
            errors.append(f"{path}: missing name")
        elif name != directory.name:
            errors.append(f"{path}: name {name!r} does not match directory {directory.name!r}")
        elif not NAME_RE.fullmatch(name):
            errors.append(f"{path}: invalid skill name {name!r}")
        elif len(name) > 64:
            errors.append(f"{path}: name longer than 64 characters")
        if name in names:
            errors.append(f"{path}: duplicate name also used by {names[name]}")
        names[name] = path

        if not 80 <= len(description) <= 1024:
            errors.append(f"{path}: description length {len(description)} not in 80..1024")
        if not ROUTING_RE.search(description):
            errors.append(f"{path}: description lacks routing language (Use when/for/...)")

        for section in REQUIRED_SECTIONS:
            if section not in text:
                errors.append(f"{path}: missing {section!r}")
        if not any(heading in text for heading in FAILURE_HEADINGS):
            errors.append(f"{path}: missing a failure/pitfalls section")

        body = text.split("\n---\n", 1)[1] if "\n---\n" in text else text
        if re.search(r"\bsk-[A-Za-z0-9_-]{16,}\b", body) or "BEGIN PRIVATE KEY" in body:
            errors.append(f"{path}: possible secret material")
        for relative in re.findall(r"\[[^\]]+\]\((?!https?://|#)([^)]+)\)", body):
            target = (path.parent / relative).resolve()
            if not target.exists():
                errors.append(f"{path}: broken relative link {relative!r}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in names:
        if f"skills/{name}/SKILL.md" not in readme:
            errors.append(f"README.md: missing table entry for {name}")

    if errors:
        print("Skill validation failed:\n", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(names)} skills:")
    for name in sorted(names):
        print(f"  ✓ {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
