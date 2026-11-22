"""Templates helpers for the notifications subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TemplatesRecord:
    notes: str = ""
    priority: str = ""
    channel: str = ""
    region: str = ""
    warehouse: str = ""
    quantity: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class TemplatesStore:
    """In-memory index of TemplatesRecord keyed by notes."""

    def __init__(self) -> None:
        self._items: dict[str, TemplatesRecord] = {}

    def add(self, record: TemplatesRecord) -> None:
        if not record.notes:
            raise ValueError("notes is required")
        if record.notes in self._items:
            raise KeyError(f"duplicate notes: {record.notes}")
        self._items[record.notes] = record
        record.touch("added")

    def get(self, notes: str) -> TemplatesRecord | None:
        return self._items.get(notes)

    def find(self, **criteria: str) -> list[TemplatesRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def route_warehouse_0(records: list[TemplatesRecord], limit: int = 11) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_notes_1(records: list[TemplatesRecord], limit: int = 28) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_notes_2(records: list[TemplatesRecord], limit: int = 39) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
