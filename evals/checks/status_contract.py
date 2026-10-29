"""Executable contract checks for the status evaluation.

Run from a run directory that contains `status_model.py` and the Kiln fixture:

    python /path/to/evals/checks/status_contract.py

Contract:

    status_model.classify(scenario, *, now_ns=None) -> {
        "state": str, "active": bool, "evidence": str
    }
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import status_model  # noqa: E402


class StatusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path.cwd()
        cls.fixture = json.loads((root / "scenarios.json").read_text())
        cls.expected = json.loads((root / "expected.json").read_text())

    def classify(self, scenario):
        return status_model.classify(scenario, now_ns=self.fixture["now_ns"])

    def test_fixture_states(self):
        for scenario in self.fixture["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                result = self.classify(scenario)
                expected = self.expected[scenario["id"]]
                self.assertEqual(result["state"], expected["state"])
                self.assertEqual(bool(result["active"]), expected["active"])
                self.assertTrue(str(result.get("evidence", "")).strip())

    def test_newer_started_turn_wins_over_old_completion(self):
        scenario = next(s for s in self.fixture["scenarios"] if s["id"] == "old-completed-new-started")
        result = self.classify(scenario)
        self.assertNotEqual(result["state"], "Completed")
        self.assertTrue(result["active"])

    def test_out_of_order_turn_is_deterministic_and_flagged(self):
        scenario = {
            "id": "out-of-order",
            "job_id": "job-20",
            "turn_id": "turn-2",
            "run_state": "running",
            "waiting_for": "",
            "last_record_ns": self.fixture["now_ns"] - 1_000_000_000,
            "collector": {"last_success_ns": self.fixture["now_ns"], "backlog_bytes": 0},
            "process": {},
            "previous_turn": {
                "turn_id": "turn-3",
                "run_state": "completed",
                "ended_ns": self.fixture["now_ns"] + 1_000_000_000,
            },
        }
        result = self.classify(scenario)
        self.assertIn(result["state"], {"Working", "Working (quiet)", "Unconfirmed"})
        self.assertFalse(result["state"] == "Completed")


if __name__ == "__main__":
    unittest.main()
