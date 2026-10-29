#!/usr/bin/env python3
"""Zero-dependency validator for the Agenturm TUI skills repo."""
from __future__ import annotations

import json
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

    def load_json(relative: str) -> dict:
        path = ROOT / relative
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            errors.append(f"{relative}: cannot read: {exc}")
        except json.JSONDecodeError as exc:
            errors.append(f"{relative}: invalid JSON: {exc}")
        return {}

    manifest = load_json("skills.json")
    package = load_json("package.json")
    claude_plugin = load_json(".claude-plugin/plugin.json")
    marketplace = load_json(".claude-plugin/marketplace.json")
    codex_plugin = load_json(".codex-plugin/plugin.json")

    versions = {
        "skills.json": manifest.get("version"),
        "package.json": package.get("version"),
        ".claude-plugin/plugin.json": claude_plugin.get("version"),
        ".claude-plugin/marketplace.json": (marketplace.get("metadata") or {}).get("version"),
        ".codex-plugin/plugin.json": codex_plugin.get("version"),
    }
    unique_versions = {version for version in versions.values() if version}
    if len(unique_versions) != 1 or None in versions.values():
        errors.append(f"version mismatch across manifests: {versions}")
    elif not any(f"## {version}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
                 for version in unique_versions):
        errors.append("CHANGELOG.md: missing a section for the current version")

    declared = manifest.get("skills", [])
    declared_names = [item.get("name") for item in declared if isinstance(item, dict)]
    if sorted(declared_names) != sorted(names):
        errors.append(f"skills.json: skills {declared_names} do not match directories {sorted(names)}")
    for item in declared:
        if not isinstance(item, dict):
            errors.append("skills.json: every skill entry must be an object")
            continue
        path = item.get("path", "")
        if not (ROOT / path).is_dir():
            errors.append(f"skills.json: missing path {path!r}")
        if not item.get("description"):
            errors.append(f"skills.json: {item.get('name')} missing description")

    targets = manifest.get("targets", {})
    if not targets:
        errors.append("skills.json: no install targets")
    if len(set(targets.values())) != len(targets):
        errors.append("skills.json: duplicate target paths")
    for name, path in targets.items():
        if not (path.startswith("~/") or path.startswith("/")):
            errors.append(f"skills.json: target {name} must be an absolute or ~ path")
    if package.get("pi", {}).get("skills") != ["./skills"]:
        errors.append("package.json: pi.skills must be ['./skills']")

    plugins = marketplace.get("plugins") or []
    if len(plugins) != 1:
        errors.append(".claude-plugin/marketplace.json: expected exactly one plugin")
    else:
        plugin_skills = plugins[0].get("skills") or []
        expected = ["./" + item["path"] for item in declared if isinstance(item, dict)]
        if plugin_skills != expected:
            errors.append(".claude-plugin/marketplace.json: plugin skills do not match skills.json")
        if plugins[0].get("name") != claude_plugin.get("name"):
            errors.append(".claude-plugin: marketplace plugin name does not match plugin.json")
        if codex_plugin.get("name") != claude_plugin.get("name"):
            errors.append(".codex-plugin/plugin.json: name does not match the Claude plugin")
    if codex_plugin.get("skills") != "./skills/":
        errors.append(".codex-plugin/plugin.json: skills must be './skills/'")

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
