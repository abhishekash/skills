"""Baseline smoke test for the evaluation fixture."""
from __future__ import annotations

import unittest

from textual.widgets import DataTable

from order_board import Order, OrderBoard


class OrderBoardSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_initial_rows(self):
        app = OrderBoard()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#orders", DataTable)
            self.assertEqual(table.row_count, 2)
            self.assertEqual(app.orders[0].id, "ord-100")

    async def test_apply_orders_replaces_rows(self):
        app = OrderBoard()
        async with app.run_test() as pilot:
            await pilot.pause()
            app.apply_orders([Order("ord-200", "Label parcel", "queued")])
            await pilot.pause()
            table = app.query_one("#orders", DataTable)
            self.assertEqual(table.row_count, 1)
            self.assertEqual([key.value for key in table.rows], ["ord-200"])


if __name__ == "__main__":
    unittest.main()
