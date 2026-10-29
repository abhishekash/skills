"""Minimal hidden-pane + stale-response example.

The important invariants:
- Do not write a RichLog while it is hidden or has zero width; cache the text.
- Bind every async response to a request generation, not just field equality.
  A -> B -> A must reject the first A response even though its fields match again.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual.widgets import RichLog


@dataclass(frozen=True)
class Scope:
    record: str
    query: str = ""


class RequestGate:
    def __init__(self) -> None:
        self.generation = 0
        self.scope: Scope | None = None

    def begin(self, scope: Scope) -> int:
        self.generation += 1
        self.scope = scope
        return self.generation

    def accept(self, token: int, scope: Scope) -> bool:
        return token == self.generation and scope == self.scope


class DetailPane:
    def __init__(self, log: RichLog) -> None:
        self.log = log
        self.pending: str | None = None

    def render(self, text: str) -> str:
        if not self.log.display or self.log.size.width <= 0:
            self.pending = text
            return "deferred"
        self.log.clear()
        self.log.write(Text(text))
        self.pending = None
        return "rendered"

    def show(self) -> str:
        if self.pending is None:
            return "empty"
        return self.render(self.pending)


class DetailController:
    def __init__(self, pane: DetailPane) -> None:
        self.pane = pane
        self.gate = RequestGate()

    def request(self, scope: Scope) -> int:
        return self.gate.begin(scope)

    def apply(self, token: int, scope: Scope, text: str) -> str:
        if not self.gate.accept(token, scope):
            return "stale"
        return self.pane.render(text)
