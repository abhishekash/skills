"""Executable contract checks for the Textual order-board evaluation.

Run from a run directory that contains `order_board.py`:

    python /path/to/evals/checks/textual_contract.py

The checks are intentionally behavioral and headless. They assume the fixture's
public contract, not a particular implementation.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from textual.widgets import DataTable

from order_board import Order, OrderBoard


class TextualContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = OrderBoard()
        self._ctx = self.app.run_test(size=(120, 40))
        self.pilot = await self._ctx.__aenter__()
        await self.pilot.pause()
        self.table = self.app.query_one("#orders", DataTable)

    async def asyncTearDown(self):
        await self._ctx.__aexit__(None, None, None)

    async def test_append_remove_reorder_and_selection(self):
        self.app.apply_orders([
            Order("ord-1", "Pack", "queued"),
            Order("ord-2", "Ship", "working"),
            Order("ord-3", "Invoice", "done"),
        ])
        await self.pilot.pause()
        self.assertEqual([key.value for key in self.table.rows], ["ord-1", "ord-2", "ord-3"])
        self.table.move_cursor(row=2)
        self.app.apply_orders([
            Order("ord-3", "Invoice", "done"),
            Order("ord-1", "Pack", "queued"),
        ])
        await self.pilot.pause()
        self.assertEqual([key.value for key in self.table.rows], ["ord-3", "ord-1"])
        self.assertEqual(self.table.cursor_row, 0)

    async def test_hidden_detail_defers_and_show_renders(self):
        log = self.app.query_one("#detail")
        log.display = False
        await self.pilot.pause()
        token = self.app.begin_detail("ord-100")
        self.assertEqual(self.app.apply_detail(token, "ord-100", "full detail"), "deferred")
        self.assertEqual(len(log.lines), 0)
        log.display = True
        await self.pilot.pause()
        self.assertEqual(self.app.show_detail(), "rendered")
        self.assertIn("full detail", "\n".join(line.text for line in log.lines))

    async def test_a_b_a_rejects_obsolete_response(self):
        first_a = self.app.begin_detail("ord-100")
        self.app.begin_detail("ord-101")
        second_a = self.app.begin_detail("ord-100")
        self.assertEqual(self.app.apply_detail(first_a, "ord-100", "old A"), "stale")
        self.assertEqual(self.app.apply_detail(second_a, "ord-100", "new A"), "rendered")
        log = self.app.query_one("#detail")
        text = "\n".join(line.text for line in log.lines)
        self.assertIn("new A", text)
        self.assertNotIn("old A", text)


if __name__ == "__main__":
    unittest.main()
