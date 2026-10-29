"""Executable contract checks for the ingestion evaluation.

Run from a run directory that contains `reader.py` and the Forge fixture:

    python /path/to/evals/checks/ingestion_contract.py

Contract expected by the evaluator:

    reader.read_once(path, *, offset=0, record_budget=..., poll_budget=...) -> {
        "records": [ {job_id, ...}, ... ],
        "offset": int,
        "diagnostics": {"skipped_oversized": int, "skipped_records": int, ...},
        "partial": bool,
    }
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import reader  # noqa: E402


class IngestionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.dir = Path(cls.tmp.name)
        subprocess.run(
            [sys.executable, "generate.py", "--output", str(cls.dir / "build_log.jsonl")],
            cwd=Path.cwd(),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        cls.mixed = cls.dir / "build_log_mixed.jsonl"
        cls.partial = cls.dir / "build_log.jsonl"
        cls.backlog = cls.dir / "build_backlog.jsonl"

    def read(self, path, offset=0):
        return reader.read_once(
            path,
            offset=offset,
            record_budget=64 * 1024,
            poll_budget=128 * 1024,
        )

    def test_partial_then_complete(self):
        first = self.read(self.partial)
        ids = [row["job_id"] for row in first["records"]]
        self.assertIn("job-1", ids)
        self.assertNotIn("job-2", ids)
        self.assertTrue(first.get("partial"))
        with self.partial.open("a", encoding="utf-8") as stream:
            stream.write(',"status":"ok"}\n')
        second = self.read(self.partial, offset=int(first["offset"]))
        self.assertIn("job-2", [row["job_id"] for row in second["records"]])

    def test_oversized_and_malformed_do_not_lose_valid_tail(self):
        ids: list[str] = []
        diagnostics = {"skipped_oversized": 0, "skipped_records": 0}
        offset = 0
        for _ in range(6):
            result = self.read(self.mixed, offset=offset)
            ids.extend(row["job_id"] for row in result["records"])
            diagnostics["skipped_oversized"] += int(result["diagnostics"].get("skipped_oversized", 0))
            diagnostics["skipped_records"] += int(result["diagnostics"].get("skipped_records", 0))
            new_offset = int(result["offset"])
            if new_offset == offset:
                break
            offset = new_offset
            if offset >= self.mixed.stat().st_size:
                break
        self.assertIn("job-4", ids)
        self.assertIn("job-5", ids)
        self.assertNotIn("job-oversized", ids)
        self.assertGreaterEqual(diagnostics["skipped_oversized"], 1)
        self.assertGreaterEqual(diagnostics["skipped_records"], 1)

    def test_backlog_makes_fair_progress(self):
        seen: list[str] = []
        offset = 0
        for _ in range(40):
            result = self.read(self.backlog, offset=offset)
            seen.extend(row["job_id"] for row in result["records"])
            new_offset = int(result["offset"])
            if new_offset == offset and not result["records"]:
                break
            offset = new_offset
            if len(set(seen)) >= 40:
                break
        unique = set(seen)
        expected = {f"job-{index}" for index in range(10, 50)}
        self.assertEqual(unique, expected)
        self.assertNotIn("job-huge", unique)

    def test_schema_v2_optional_fields(self):
        path = self.dir / "v2.jsonl"
        path.write_text('{"job_id":"job-6","step":"test","status":"ok","elapsed_ms":12}\n')
        result = self.read(path)
        self.assertEqual([row["job_id"] for row in result["records"]], ["job-6"])


if __name__ == "__main__":
    unittest.main()
