#!/usr/bin/env python3
"""Install the Agenturm TUI skills into agent skill directories.

No third-party dependencies. Supports copy (default) and symlink installs.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "skills.json"
MARKER = ".agenturm-skill"


def fail(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read {MANIFEST_PATH}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"invalid {MANIFEST_PATH}: {exc}")


def parse_targets(args, manifest: dict) -> list[str]:
    known = manifest.get("targets", {})
    if args.all:
        return list(known)
    values: list[str] = []
    for raw in args.target:
        for item in raw.split(","):
            item = item.strip()
            if item:
                values.append(item)
    if not values:
        home = Path.home()
        if (home / ".config/opencode").exists():
            values = ["opencode"]
        elif (home / ".claude").exists():
            values = ["claude-code"]
        elif (home / ".agents").exists():
            values = ["codex"]
        else:
            values = ["opencode"]
        print(f"No target supplied; detected: {', '.join(values)}")
    unknown = [item for item in values if item not in known]
    if unknown:
        fail(f"unknown target(s): {', '.join(unknown)}. Known: {', '.join(known)}")
    # Preserve order, remove duplicates.
    return list(dict.fromkeys(values))


def target_path(target: str, manifest: dict, override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    return Path(manifest["targets"][target]).expanduser()


def is_ours(destination: Path) -> bool:
    """True when a destination is a symlink into this checkout or a marked copy."""
    if destination.is_symlink():
        try:
            destination.resolve().relative_to(ROOT)
            return True
        except (OSError, ValueError):
            return False
    return (destination / MARKER).is_file()


def remove_destination(destination: Path, force: bool) -> bool:
    if not destination.exists() and not destination.is_symlink():
        return True
    if not force and not is_ours(destination):
        return False
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    else:
        shutil.rmtree(destination)
    return True


def install_skill(source: Path, destination: Path, *, link: bool, force: bool, dry_run: bool) -> str:
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        return f"skip (missing {source / 'SKILL.md'})"

    if destination.is_symlink():
        kind = "symlink"
    elif destination.is_file():
        kind = "file"
    elif destination.is_dir():
        kind = "directory"
    else:
        kind = "missing"

    if kind != "missing":
        if link and kind == "symlink" and is_ours(destination):
            try:
                if destination.resolve() == source.resolve():
                    return "already installed"
            except OSError:
                pass
        if not force:
            return "skipped (exists; use --force to update)"
        action = "replace"
    else:
        action = "install"

    if dry_run:
        return f"would {action} ({'link' if link else 'copy'}) -> {destination}"

    if kind != "missing" and not remove_destination(destination, force=True):
        return "failed: could not replace existing destination"

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if link:
            os.symlink(source.resolve(), destination, target_is_directory=True)
        else:
            shutil.copytree(source, destination)
            (destination / MARKER).write_text(
                json.dumps({"pack": "agenturm-tui-skills", "source": str(source.resolve())}, indent=2) + "\n",
                encoding="utf-8",
            )
    except OSError as exc:
        # Never leave a partial copy that could be mistaken for a complete skill.
        try:
            if destination.is_symlink() or destination.is_file():
                destination.unlink(missing_ok=True)
            elif destination.is_dir():
                shutil.rmtree(destination, ignore_errors=True)
        except OSError:
            pass
        return f"failed: {exc}"
    return "linked" if link else "copied"


def remove_skill(destination: Path, *, force: bool, dry_run: bool) -> str:
    if not destination.exists() and not destination.is_symlink():
        return "not installed"
    if not force and not is_ours(destination):
        return "skipped (not managed; use --force)"
    if dry_run:
        return f"would remove {destination}"
    try:
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        else:
            shutil.rmtree(destination)
    except OSError as exc:
        return f"failed: {exc}"
    return "removed"


def list_contents(manifest: dict) -> None:
    print(f"{manifest['name']} {manifest['version']}")
    print(f"{manifest['description']}\n")
    print("Skills:")
    for skill in manifest["skills"]:
        print(f"  {skill['name']:<34} {skill['path']}")
    print("\nTargets:")
    for name, path in manifest["targets"].items():
        print(f"  {name:<14} {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install Agenturm TUI skills into a local agent skills directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  ./install.sh --target opencode
  ./install.sh --target claude-code --link
  ./install.sh --all --copy
  ./install.sh --dest ./.agents/skills --copy
  ./install.sh --list
""",
    )
    parser.add_argument("--target", action="append", default=[], metavar="NAME",
                        help="target agent (opencode, claude-code, codex, cursor, gemini-cli, agents); repeatable or comma-separated")
    parser.add_argument("--all", action="store_true", help="install to every known target")
    parser.add_argument("--dest", metavar="DIR", help="install to an explicit skills directory (overrides target paths)")
    parser.add_argument("--link", action="store_true", help="symlink skill directories instead of copying")
    parser.add_argument("--copy", action="store_true", help="copy skill directories (default)")
    parser.add_argument("--force", action="store_true", help="replace existing destinations")
    parser.add_argument("--dry-run", action="store_true", help="show the plan without changing files")
    parser.add_argument("--list", action="store_true", help="list skills and target paths")
    parser.add_argument("--remove", action="store_true", help="remove installed copies/symlinks")
    args = parser.parse_args()

    manifest = load_manifest()
    if args.list:
        list_contents(manifest)
        return 0
    if args.link and args.copy:
        fail("choose --link or --copy, not both")
    if args.dest and args.all:
        fail("--dest cannot be combined with --all")
    targets = parse_targets(args, manifest)
    if args.dest and len(targets) != 1:
        fail("--dest requires exactly one --target")

    link = bool(args.link)
    failures = 0
    for target in targets:
        destination_root = target_path(target, manifest, args.dest)
        print(f"\n{target}: {destination_root}")
        if not args.dry_run:
            try:
                destination_root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                print(f"  error: cannot create {destination_root}: {exc}", file=sys.stderr)
                failures += 1
                continue
        for skill in manifest["skills"]:
            source = ROOT / skill["path"]
            destination = destination_root / skill["name"]
            if args.remove:
                result = remove_skill(destination, force=args.force, dry_run=args.dry_run)
            else:
                result = install_skill(source, destination, link=link, force=args.force, dry_run=args.dry_run)
            print(f"  {skill['name']:<34} {result}")
            if (result.startswith("failed") or result.startswith("skip (missing")
                    or result.startswith("not a managed")):
                failures += 1
    if failures:
        print(f"\n{failures} skill(s) were not installed/removed.", file=sys.stderr)
        return 1
    print("\nDone. Restart your agent so it discovers the skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
