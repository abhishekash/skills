"""Tests for the runnable incremental DataTable example. Textual 8.2.8."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import DataTable

from table_projection import Row, TableProjection


def rows(*specs, style: str = "") -> list[Row]:
    return [
        Row(key=key, cells=(Text(task, style=style), Text(state)))
        for key, task, state in specs
    ]


class TableHarness(App):
    def compose(self) -> ComposeResult:
        yield DataTable(id="rows", cursor_type="row", zebra_stripes=False)

    def on_mount(self) -> None:
        table = self.query_one("#rows", DataTable)
        table.add_column("Task", width=24)
        table.add_column("State", width=10)
        self.projection = TableProjection(
            table,
            height_for=lambda values: max(1, values[0].plain.count("\n") + 1),
        )


class IncrementalTableTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TableHarness()
        self._ctx = self.app.run_test()
        self.pilot = await self._ctx.__aenter__()
        await self.pilot.pause()
        self.table = self.app.query_one("#rows", DataTable)

    async def asyncTearDown(self):
        await self._ctx.__aexit__(None, None, None)

    def apply(self, items, preserve=None):
        return self.app.projection.apply(items, preserve=preserve)

    async def test_initial_empty_to_populated(self):
        self.assertEqual(self.table.row_count, 0)
        result = self.apply(rows(("ord-1", "Pack", "queued"), ("ord-2", "Ship", "working")))
        await self.pilot.pause()
        self.assertEqual(result, "rebuilt")
        self.assertEqual(self.table.row_count, 2)
        self.assertEqual([key.value for key in self.table.rows], ["ord-1", "ord-2"])

    async def test_append_remove_and_reorder_take_rebuild_path(self):
        self.apply(rows(("ord-1", "Pack", "queued"), ("ord-2", "Ship", "working")))
        self.assertEqual(self.apply(rows(
            ("ord-1", "Pack", "queued"),
            ("ord-2", "Ship", "working"),
            ("ord-3", "Invoice", "done"),
        )), "rebuilt")
        self.assertEqual(self.table.row_count, 3)
        self.assertEqual(self.apply(rows(("ord-3", "Invoice", "done"), ("ord-1", "Pack", "queued"))), "rebuilt")
        self.assertEqual([key.value for key in self.table.rows], ["ord-3", "ord-1"])
        self.assertEqual(self.apply(rows(("ord-1", "Pack", "queued"))), "rebuilt")
        self.assertEqual(self.table.row_count, 1)

    async def test_unchanged_data_does_not_update_cells(self):
        self.apply(rows(("ord-1", "Pack", "queued")))
        with patch.object(self.table, "update_cell", wraps=self.table.update_cell) as update:
            result = self.apply(rows(("ord-1", "Pack", "queued")))
            update.assert_not_called()
        self.assertEqual(result, "unchanged")

    async def test_changed_content_updates_only_changed_cell(self):
        self.apply(rows(("ord-1", "Pack", "queued"), ("ord-2", "Ship", "working")))
        changed = rows(("ord-1", "Pack", "queued"), ("ord-2", "Ship", "done"))
        with patch.object(self.table, "update_cell", wraps=self.table.update_cell) as update:
            result = self.apply(changed)
            self.assertEqual(update.call_count, 1)
        self.assertEqual(result, "updated")
        self.assertEqual(self.table.get_row("ord-2")[1].plain, "done")

    async def test_style_only_change_is_not_missed(self):
        self.apply(rows(("ord-1", "Pack", "queued")))
        result = self.apply(rows(("ord-1", "Pack", "queued"), style="bold red"))
        self.assertEqual(result, "updated")
        self.assertEqual(str(self.table.get_row("ord-1")[0].style), "bold red")

    async def test_row_height_change_takes_rebuild_path(self):
        self.apply(rows(("ord-1", "Pack", "queued")))
        before = self.table.rows[next(iter(self.table.rows))].height
        result = self.apply(rows(("ord-1", "Pack\ntwo lines", "queued")))
        after = self.table.rows[next(iter(self.table.rows))].height
        self.assertEqual(result, "rebuilt")
        self.assertGreater(after, before)

    async def test_invalidation_forces_theme_or_projection_reapply(self):
        self.apply(rows(("ord-1", "Pack", "queued")))
        old_signature = self.app.projection.applied_signature
        self.app.projection.invalidate()
        result = self.apply(rows(("ord-1", "Pack", "queued")))
        self.assertNotEqual(result, "unchanged")
        self.assertNotEqual(self.app.projection.applied_signature, old_signature)

    async def test_selection_survives_reorder_and_falls_back_on_removal(self):
        self.apply(rows(
            ("ord-1", "Pack", "queued"),
            ("ord-2", "Ship", "working"),
            ("ord-3", "Invoice", "done"),
        ))
        self.table.move_cursor(row=2)
        self.apply(rows(
            ("ord-3", "Invoice", "done"),
            ("ord-1", "Pack", "queued"),
            ("ord-2", "Ship", "working"),
        ))
        self.assertEqual(self.table.cursor_row, 0)

        self.table.move_cursor(row=1)
        self.apply(rows(("ord-3", "Invoice", "done"), ("ord-2", "Ship", "working")))
        self.assertEqual(self.table.cursor_row, 1)

    async def test_failed_update_is_retryable(self):
        self.apply(rows(("ord-1", "Pack", "queued")))
        old_signature = self.app.projection.applied_signature
        original = self.table.update_cell
        calls = {"n": 0}

        def flaky(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("injected failure")
            return original(*args, **kwargs)

        with patch.object(self.table, "update_cell", side_effect=flaky):
            with self.assertRaises(RuntimeError):
                self.apply(rows(("ord-1", "Pack changed", "queued")))
        self.assertEqual(self.app.projection.applied_signature, old_signature)

        result = self.apply(rows(("ord-1", "Pack changed", "queued")))
        self.assertEqual(result, "updated")
        self.assertEqual(self.table.get_row("ord-1")[0].plain, "Pack changed")

    async def test_scroll_offset_remains_valid(self):
        items = [("ord-1", "A", "queued"), ("ord-2", "B", "queued"), ("ord-3", "C", "queued")]
        self.apply(rows(*items))
        self.table.scroll_to(y=1, animate=False)
        await self.pilot.pause()
        self.apply(rows(*items, ("ord-4", "D", "queued")))
        await self.pilot.pause()
        self.assertGreaterEqual(self.table.scroll_offset.y, 0)
        self.assertLessEqual(self.table.scroll_offset.y, self.table.row_count)


if __name__ == "__main__":
    unittest.main()
