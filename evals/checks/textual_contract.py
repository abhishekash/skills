"""Task-scoped executable checks for the Textual order-board evaluation.

Set ``EVAL_TASK=1``, ``2``, or ``3`` to run only that task's checks. With no
value, all checks run.

Run from a run directory that contains `order_board.py`:

    EVAL_TASK=1 python /path/to/evals/checks/textual_contract.py -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from textual.widgets import DataTable

from order_board import Order, OrderBoard

TASK = os.environ.get("EVAL_TASK", "").strip()
ONLY = (lambda task: TASK in ("", str(task)))


class TextualContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = OrderBoard()
        self._ctx = self.app.run_test(size=(120, 40))
        self.pilot = await self._ctx.__aenter__()
        await self.pilot.pause()
        self.table = self.app.query_one("#orders", DataTable)

    async def asyncTearDown(self):
        await self._ctx.__aexit__(None, None, None)

    @unittest.skipUnless(ONLY(1), "task 1 only")
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

    @unittest.skipUnless(ONLY(1), "task 1 only")
    async def test_unchanged_data_is_a_noop(self):
        items = [Order("ord-1", "Pack", "queued"), Order("ord-2", "Ship", "working")]
        self.app.apply_orders(items)
        result = self.app.apply_orders(items)
        self.assertEqual(result, "unchanged")

    @unittest.skipUnless(ONLY(1), "task 1 only")
    async def test_style_only_change_is_visible(self):
        self.app.apply_orders([Order("ord-1", "Pack", "queued")])
        result = self.app.apply_orders([Order("ord-1", "Pack", "queued", "bold red")])
        self.assertEqual(result, "updated")
        cell = self.table.get_row("ord-1")[0]
        self.assertIn("bold red", str(cell.style))

    @unittest.skipUnless(ONLY(2), "task 2 only")
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

    @unittest.skipUnless(ONLY(3), "task 3 only")
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
