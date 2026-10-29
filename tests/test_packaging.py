"""Packaged-resource checks: copy and symlink installs must keep links working."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|#|mailto:)([^)]+)\)")


def run_installer(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "install.py"), "--target", "opencode", "--dest", str(dest), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )


class PackagedResourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="agenturm-skills-pack-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def assert_links_resolve(self, dest: Path):
        skill_files = list(dest.glob("*/SKILL.md"))
        self.assertEqual(len(skill_files), 9)
        for skill_file in skill_files:
            body = skill_file.read_text(encoding="utf-8").split("\n---\n", 1)[-1]
            for relative in LINK_RE.findall(body):
                target = (skill_file.parent / relative).resolve()
                self.assertTrue(target.exists(), f"{skill_file}: broken installed link {relative}")

    def test_copy_install_keeps_relative_resources(self):
        dest = self.tmp / "copy"
        result = run_installer(dest, "--copy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_links_resolve(dest)
        self.assertTrue((dest / "textual-tui-engineering" / "examples" / "incremental_table" / "table_projection.py").is_file())
        self.assertTrue((dest / "terminal-cockpit-design" / "references" / "agenturm-case-study.md").is_file())

    def test_symlink_install_keeps_relative_resources(self):
        dest = self.tmp / "link"
        result = run_installer(dest, "--link")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_links_resolve(dest)
        for link in dest.iterdir():
            self.assertTrue(link.is_symlink())

    def test_installed_examples_are_runnable(self):
        dest = self.tmp / "copy"
        result = run_installer(dest, "--copy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        base = dest / "textual-tui-engineering" / "examples"
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for name in ("incremental_table", "async_detail"):
            with self.subTest(example=name):
                example = base / name
                check = subprocess.run(
                    [sys.executable, "-m", "unittest", "-q"],
                    cwd=example,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120,
                )
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
