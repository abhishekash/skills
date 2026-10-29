"""Independent Textual fixture for the evaluation suite: a warehouse order board.

This is intentionally NOT an agent monitor. The baseline has naive refresh and
detail behavior; the evaluation tasks ask for the fixes described in the skill.

Contract used by the checks:
- ``OrderBoard.apply_orders(orders)`` exists and keeps the table in sync.
- ``OrderBoard.begin_detail(order_id) -> token`` starts a detail request.
- ``OrderBoard.apply_detail(token, order_id, text)`` renders only the current
  request and returns ``"rendered" | "deferred" | "stale"``.
- ``OrderBoard.show_detail()`` renders a deferred detail after the pane is shown.
"""
from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import DataTable, RichLog


@dataclass(frozen=True)
class Order:
    id: str
    task: str
    state: str


class OrderBoard(App):
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, orders: list[Order] | None = None) -> None:
        super().__init__()
        self.orders = list(orders or [
            Order("ord-100", "Pack order", "queued"),
            Order("ord-101", "Ship order", "working"),
        ])
        self.detail_token = 0
        self.pending_detail: tuple[int, str, str] | None = None

    def compose(self) -> ComposeResult:
        yield DataTable(id="orders", cursor_type="row", zebra_stripes=False)
        yield RichLog(id="detail", wrap=True, markup=False)

    def on_mount(self) -> None:
        table = self.query_one("#orders", DataTable)
        table.add_column("Task", width=28)
        table.add_column("State", width=12)
        self.apply_orders(self.orders)

    # Baseline: clear and rebuild every time. No stable signature, no style
    # comparison, no row-height preservation.
    def apply_orders(self, orders: list[Order]) -> str:
        table = self.query_one("#orders", DataTable)
        table.clear()
        for order in orders:
            table.add_row(Text(order.task), Text(order.state), key=order.id)
        self.orders = list(orders)
        return "rebuilt"

    def begin_detail(self, order_id: str) -> int:
        self.detail_token += 1
        return self.detail_token

    # Baseline: ignores the token, so A -> B -> A can accept an old response.
    def apply_detail(self, token: int, order_id: str, text: str) -> str:
        log = self.query_one("#detail", RichLog)
        if not log.display or log.size.width <= 0:
            self.pending_detail = (token, order_id, text)
            return "deferred"
        log.clear()
        log.write(Text(text))
        return "rendered"

    def show_detail(self) -> str:
        if self.pending_detail is None:
            return "empty"
        token, order_id, text = self.pending_detail
        self.pending_detail = None
        return self.apply_detail(token, order_id, text)
