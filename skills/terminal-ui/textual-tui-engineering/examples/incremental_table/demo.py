"""Minimal runnable demo for TableProjection.

Requires Textual 8.2.x (tested with 8.2.8) and Rich 15.x.

    python demo.py

Keys: a append, d remove last, u change content, t toggle style,
      i invalidate, q quit.
"""
from __future__ import annotations

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Static

from table_projection import Row, TableProjection


class ProjectionDemo(App):
    BINDINGS = [
        ("a", "append", "Append"),
        ("d", "remove_last", "Remove last"),
        ("u", "change_content", "Change content"),
        ("t", "toggle_style", "Toggle style"),
        ("i", "invalidate", "Invalidate"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.items = [
            {"id": "ord-100", "task": "Pack order", "state": "queued"},
            {"id": "ord-101", "task": "Ship order", "state": "working"},
        ]
        self.bold = False
        self.next_id = 102

    def compose(self) -> ComposeResult:
        yield DataTable(id="rows", cursor_type="row", zebra_stripes=False)
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#rows", DataTable)
        table.add_column("Task", width=32)
        table.add_column("State", width=12)
        self.projection = TableProjection(
            table,
            height_for=lambda values: max(1, values[0].plain.count("\n") + 1),
        )
        self.refresh_rows("initial")

    def rows(self) -> list[Row]:
        return [
            Row(
                key=item["id"],
                cells=(
                    Text(item["task"], style="bold" if self.bold else ""),
                    Text(item["state"]),
                ),
            )
            for item in self.items
        ]

    def refresh_rows(self, label: str) -> None:
        result = self.projection.apply(self.rows())
        self.query_one("#status", Static).update(f"{label}: {result}")

    def action_append(self) -> None:
        self.items.append(
            {"id": f"ord-{self.next_id}", "task": f"New order {self.next_id}", "state": "queued"}
        )
        self.next_id += 1
        self.refresh_rows("append")

    def action_remove_last(self) -> None:
        if self.items:
            self.items.pop()
        self.refresh_rows("remove")

    def action_change_content(self) -> None:
        if self.items:
            self.items[0]["task"] += " · updated"
        self.refresh_rows("change content")

    def action_toggle_style(self) -> None:
        self.bold = not self.bold
        self.refresh_rows("toggle style")

    def action_invalidate(self) -> None:
        self.projection.invalidate()
        self.refresh_rows("invalidate")


if __name__ == "__main__":
    ProjectionDemo().run()
