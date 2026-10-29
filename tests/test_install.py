"""Installer safety regressions. Never touches the real agent config."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_COUNT = 9


def snapshot(root: Path) -> dict:
    """Content, link targets, modes and mtimes; access times intentionally ignored."""
    if not os.path.lexists(root):
        return {"exists": False}

    def record(path: Path) -> dict:
        info = os.lstat(path)
        item = {
            "mode": stat.S_IMODE(info.st_mode),
            "mtime_ns": info.st_mtime_ns,
        }
        if stat.S_ISLNK(info.st_mode):
            item["type"] = "symlink"
            item["target"] = os.readlink(path)
        elif stat.S_ISDIR(info.st_mode):
            item["type"] = "dir"
            item["children"] = {
                child.name: record(child)
                for child in sorted(path.iterdir(), key=lambda p: p.name)
            }
        elif stat.S_ISREG(info.st_mode):
            item["type"] = "file"
            item["content"] = path.read_bytes()
        else:
            item["type"] = "other"
        return item

    return {"exists": True, "root": record(root)}


class InstallerSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="agenturm-skills-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.dest = self.tmp / "skills"
        self.home = self.tmp / "home"
        self.home.mkdir()

    def run_installer(self, *args: str, dest: Path | None = None) -> subprocess.CompletedProcess:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "install.py"),
            "--target",
            "opencode",
            "--dest",
            str(dest or self.dest),
            *args,
        ]
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )

    def assert_ok(self, result: subprocess.CompletedProcess):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def install_copy(self):
        result = self.run_installer("--copy")
        self.assert_ok(result)
        self.assertEqual(len(list(self.dest.glob("*/SKILL.md"))), SKILL_COUNT)

    def assert_unchanged(self, before: dict):
        self.assertEqual(snapshot(self.dest), before)

    def test_missing_destination_dry_run_does_not_create_root(self):
        result = self.run_installer("--dry-run")
        self.assert_ok(result)
        self.assertFalse(self.dest.exists())

    def test_managed_directory_force_dry_run_is_non_mutating(self):
        self.install_copy()
        before = snapshot(self.dest)
        result = self.run_installer("--copy", "--force", "--dry-run")
        self.assert_ok(result)
        self.assert_unchanged(before)

    def test_unmanaged_directory_force_dry_run_is_non_mutating(self):
        target = self.dest / "terminal-cockpit-design"
        target.mkdir(parents=True)
        (target / "keep.txt").write_text("keep me")
        before = snapshot(self.dest)
        result = self.run_installer("--copy", "--force", "--dry-run")
        self.assert_ok(result)
        self.assert_unchanged(before)

    def test_regular_file_force_dry_run_is_non_mutating(self):
        self.dest.mkdir(parents=True)
        target = self.dest / "terminal-cockpit-design"
        target.write_text("not a skill")
        before = snapshot(self.dest)
        result = self.run_installer("--copy", "--force", "--dry-run")
        self.assert_ok(result)
        self.assert_unchanged(before)

    def test_valid_symlink_force_dry_run_preserves_link_and_target(self):
        target_dir = self.tmp / "outside-target"
        target_dir.mkdir()
        (target_dir / "keep.txt").write_text("target content")
        self.dest.mkdir()
        link = self.dest / "terminal-cockpit-design"
        link.symlink_to(target_dir, target_is_directory=True)
        before_dest = snapshot(self.dest)
        before_target = snapshot(target_dir)
        result = self.run_installer("--copy", "--force", "--dry-run")
        self.assert_ok(result)
        self.assert_unchanged(before_dest)
        self.assertEqual(snapshot(target_dir), before_target)
        self.assertTrue(link.is_symlink())

    def test_link_force_dry_run_preserves_existing_symlink(self):
        target_dir = self.tmp / "outside-target-link"
        target_dir.mkdir()
        (target_dir / "keep.txt").write_text("target content")
        self.dest.mkdir()
        link = self.dest / "terminal-cockpit-design"
        link.symlink_to(target_dir, target_is_directory=True)
        before_dest = snapshot(self.dest)
        before_target = snapshot(target_dir)
        result = self.run_installer("--link", "--force", "--dry-run")
        self.assert_ok(result)
        self.assert_unchanged(before_dest)
        self.assertEqual(snapshot(target_dir), before_target)
        self.assertTrue(link.is_symlink())

    def test_dangling_symlink_force_dry_run_preserves_link(self):
        self.dest.mkdir()
        link = self.dest / "terminal-cockpit-design"
        link.symlink_to(self.tmp / "missing-target", target_is_directory=True)
        before = snapshot(self.dest)
        result = self.run_installer("--copy", "--force", "--dry-run")
        self.assert_ok(result)
        self.assert_unchanged(before)
        self.assertTrue(link.is_symlink())

    def test_remove_dry_run_preserves_all_destination_types(self):
        cases = []
        for name, kind in (
            ("managed", "managed"),
            ("unmanaged-dir", "dir"),
            ("file", "file"),
            ("symlink", "symlink"),
            ("dangling", "dangling"),
        ):
            dest = self.tmp / name
            if kind == "managed":
                result = self.run_installer("--copy", dest=dest)
                self.assert_ok(result)
            elif kind == "dir":
                (dest / "terminal-cockpit-design").mkdir(parents=True)
                (dest / "terminal-cockpit-design" / "keep.txt").write_text("keep")
            elif kind == "file":
                dest.mkdir()
                (dest / "terminal-cockpit-design").write_text("keep")
            elif kind == "symlink":
                target = self.tmp / f"{name}-target"
                target.mkdir()
                (target / "keep.txt").write_text("keep")
                dest.mkdir()
                (dest / "terminal-cockpit-design").symlink_to(target, target_is_directory=True)
            elif kind == "dangling":
                dest.mkdir()
                (dest / "terminal-cockpit-design").symlink_to(self.tmp / "missing", target_is_directory=True)
            cases.append((dest, snapshot(dest)))

        for dest, before in cases:
            for force in (False, True):
                with self.subTest(dest=dest.name, force=force):
                    args = ["--remove", "--dry-run"]
                    if force:
                        args.append("--force")
                    result = self.run_installer(*args, dest=dest)
                    self.assert_ok(result)
                    self.assertEqual(snapshot(dest), before)

    def test_real_copy_link_force_update_and_remove(self):
        self.install_copy()
        marker = self.dest / "terminal-cockpit-design" / ".agenturm-skill"
        self.assertTrue(marker.is_file())
        changed = self.dest / "terminal-cockpit-design" / "SKILL.md"
        changed.write_text("changed")
        result = self.run_installer("--copy", "--force")
        self.assert_ok(result)
        self.assertNotEqual(changed.read_text(), "changed")

        link_dest = self.tmp / "linked"
        result = self.run_installer("--link", dest=link_dest)
        self.assert_ok(result)
        for link in link_dest.iterdir():
            self.assertTrue(link.is_symlink())
            self.assertTrue((link / "SKILL.md").is_file())

        result = self.run_installer("--remove", dest=link_dest)
        self.assert_ok(result)
        self.assertFalse(any(link_dest.iterdir()))

    def test_non_force_install_preserves_unrelated_content(self):
        self.install_copy()
        existing = self.dest / "terminal-cockpit-design" / "SKILL.md"
        existing.write_text("user content")
        result = self.run_installer("--copy")
        self.assert_ok(result)
        self.assertEqual(existing.read_text(), "user content")

    def test_real_remove_symlink_does_not_delete_target(self):
        target_dir = self.tmp / "remove-target"
        target_dir.mkdir()
        (target_dir / "keep.txt").write_text("target content")
        self.dest.mkdir()
        link = self.dest / "terminal-cockpit-design"
        link.symlink_to(target_dir, target_is_directory=True)
        result = self.run_installer("--remove", "--force")
        self.assert_ok(result)
        self.assertFalse(link.exists())
        self.assertTrue((target_dir / "keep.txt").is_file())

    def test_failed_operation_is_nonzero(self):
        blocker = self.tmp / "not-a-directory"
        blocker.write_text("x")
        result = self.run_installer("--copy", dest=blocker)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot create", (result.stdout + result.stderr).lower())

    def test_repeated_install_is_predictable(self):
        self.install_copy()
        before = snapshot(self.dest)
        result = self.run_installer("--copy")
        self.assert_ok(result)
        self.assert_unchanged(before)


if __name__ == "__main__":
    unittest.main()
