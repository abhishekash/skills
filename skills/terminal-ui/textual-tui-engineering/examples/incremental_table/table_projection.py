"""A small, tested incremental-update helper for Textual DataTable.

This is deliberately independent of Agenturm. It is the runnable example
referenced by the textual-tui-engineering skill.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

from rich.text import Text
from textual.widgets import DataTable

Cell = Any
Projector = Callable[[Sequence[Cell]], Sequence[Cell]]
HeightFor = Callable[[Sequence[Cell]], int]


@dataclass(frozen=True)
class Row:
    key: str
    cells: tuple[Cell, ...]


def cell_signature(value: Cell) -> tuple:
    """Content plus styles/spans, not just str(value)."""
    if isinstance(value, Text):
        return (
            "text",
            value.plain,
            str(value.style),
            tuple((span.start, span.end, str(span.style)) for span in value.spans),
        )
    return (type(value).__name__, str(value))


class TableProjection:
    """Apply logical rows to a DataTable with stable identity and cheap updates.

    Call ``invalidate()`` on theme changes, column projection changes, or a
    resize that can change wrapped row heights. The generation is part of the
    signature, so the next ``apply`` cannot be skipped.
    """

    def __init__(
        self,
        table: DataTable,
        *,
        project: Projector | None = None,
        height_for: HeightFor | None = None,
    ) -> None:
        self.table = table
        self.project = project or (lambda values: values)
        self.height_for = height_for or (lambda values: 1)
        self.generation = 0
        self.applied_signature: tuple | None = None

    def invalidate(self) -> None:
        self.generation += 1
        self.applied_signature = None

    def _signature(self, projected: list[tuple[str, tuple[Cell, ...]]]) -> tuple:
        return (
            self.generation,
            tuple(
                (
                    key,
                    tuple(cell_signature(value) for value in values),
                    self.height_for(values),
                )
                for key, values in projected
            ),
        )

    def apply(self, rows: Iterable[Row], preserve: str | None = None) -> str:
        """Apply rows and return ``unchanged``, ``updated`` or ``rebuilt``.

        The signature is recorded only after the table update succeeds, so a
        failed update can be retried.
        """
        projected = [(row.key, tuple(self.project(row.cells))) for row in rows]
        signature = self._signature(projected)
        if signature == self.applied_signature:
            return "unchanged"

        table = self.table
        selected = preserve
        if selected is None:
            try:
                selected = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            except Exception:
                selected = None
        old_index = table.cursor_row
        scroll = table.scroll_offset

        with table.prevent(DataTable.RowHighlighted):
            existing_keys = [row_key.value for row_key in table.rows]
            incoming_keys = [key for key, _ in projected]
            keys_match = existing_keys == incoming_keys
            heights_match = False
            if keys_match:
                by_key = {row_key.value: row_key for row_key in table.rows}
                heights_match = all(
                    table.rows[by_key[key]].height == self.height_for(values)
                    for key, values in projected
                )

            if keys_match and heights_match:
                by_key = {row_key.value: row_key for row_key in table.rows}
                for key, values in projected:
                    for column, value in zip(table.columns, values):
                        previous = table.get_cell(by_key[key], column)
                        if cell_signature(previous) != cell_signature(value):
                            table.update_cell(by_key[key], column, value)
                result = "updated"
            else:
                table.clear()
                for key, values in projected:
                    table.add_row(*values, key=key, height=self.height_for(values))
                result = "rebuilt"

            if projected:
                index = next(
                    (i for i, (key, _) in enumerate(projected) if key == selected),
                    None,
                )
                if index is None:
                    # The selected record disappeared. Keep the nearest valid row.
                    index = min(max(old_index, 0), len(projected) - 1)
                table.move_cursor(row=index, scroll=False)
                # Scroll offsets are cell-based; keeping the same offset is valid
                # for wrapped rows and is clamped by Textual.
                table.scroll_to(x=scroll.x, y=scroll.y, animate=False)

        self.applied_signature = signature
        return result
