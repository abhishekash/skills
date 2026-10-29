"""Smoke test for the runnable demo app."""
from __future__ import annotations

import unittest

from textual.widgets import DataTable

from demo import ProjectionDemo


class DemoSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_demo_opens_and_appends(self):
        app = ProjectionDemo()
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#rows", DataTable)
            self.assertEqual(table.row_count, 2)
            await pilot.press("a")
            await pilot.pause()
            self.assertEqual(table.row_count, 3)
            await pilot.press("u")
            await pilot.pause()
            self.assertIn("updated", table.get_row("ord-100")[0].plain)


if __name__ == "__main__":
    unittest.main()
