"""Tests for hidden-pane reflow and stale-response rejection."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from textual.app import App, ComposeResult
from textual.widgets import RichLog

from detail_pane import DetailController, DetailPane, Scope


class PaneApp(App):
    def compose(self) -> ComposeResult:
        yield RichLog(id="detail", wrap=True, markup=False)


class HiddenPaneTests(unittest.IsolatedAsyncioTestCase):
    async def test_hidden_and_zero_width_renders_are_deferred(self):
        app = PaneApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            log = app.query_one("#detail", RichLog)
            pane = DetailPane(log)
            log.display = False
            await pilot.pause()
            with patch.object(log, "write", wraps=log.write) as write:
                self.assertEqual(pane.render("full evidence"), "deferred")
                write.assert_not_called()
            log.display = True
            await pilot.pause()
            self.assertEqual(pane.show(), "rendered")
            text = "\n".join(line.text for line in log.lines)
            self.assertIn("full evidence", text)
            self.assertNotIn("f\nu\nl\nl", text)

    async def test_zero_width_is_deferred_even_when_visible(self):
        class FakeLog:
            display = True
            size = type("Size", (), {"width": 0})()

            def clear(self):
                raise AssertionError("must not clear")

            def write(self, value):
                raise AssertionError("must not write")

        pane = DetailPane(FakeLog())
        self.assertEqual(pane.render("later"), "deferred")
        self.assertEqual(pane.pending, "later")


class StaleResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_b_a_rejects_obsolete_a_response(self):
        app = PaneApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            controller = DetailController(DetailPane(app.query_one("#detail", RichLog)))
            scope_a = Scope("record-a")
            scope_b = Scope("record-b")
            first_a = controller.request(scope_a)
            controller.request(scope_b)
            second_a = controller.request(scope_a)

            self.assertEqual(controller.apply(first_a, scope_a, "old A"), "stale")
            self.assertEqual(controller.apply(second_a, scope_a, "new A"), "rendered")
            text = "\n".join(line.text for line in app.query_one("#detail", RichLog).lines)
            self.assertIn("new A", text)
            self.assertNotIn("old A", text)

    async def test_mismatched_scope_is_stale(self):
        app = PaneApp()
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            controller = DetailController(DetailPane(app.query_one("#detail", RichLog)))
            token = controller.request(Scope("record-a"))
            self.assertEqual(controller.apply(token, Scope("record-b"), "wrong"), "stale")


if __name__ == "__main__":
    unittest.main()
