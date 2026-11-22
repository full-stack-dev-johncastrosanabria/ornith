"""Categories helpers for the catalog subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CategoriesRecord:
    notes: str = ""
    weight_kg: str = ""
    warehouse: str = ""
    sku: str = ""
    channel: str = ""
    status: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class CategoriesStore:
    """In-memory index of CategoriesRecord keyed by notes."""

    def __init__(self) -> None:
        self._items: dict[str, CategoriesRecord] = {}

    def add(self, record: CategoriesRecord) -> None:
        if not record.notes:
            raise ValueError("notes is required")
        if record.notes in self._items:
            raise KeyError(f"duplicate notes: {record.notes}")
        self._items[record.notes] = record
        record.touch("added")

    def get(self, notes: str) -> CategoriesRecord | None:
        return self._items.get(notes)

    def find(self, **criteria: str) -> list[CategoriesRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_warehouse_0(records: list[CategoriesRecord], limit: int = 11) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def route_status_1(records: list[CategoriesRecord], limit: int = 20) -> dict[str, int]:
    """Count records by status, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.status or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def summarize_sku_2(records: list[CategoriesRecord], limit: int = 3) -> dict[str, int]:
    """Count records by sku, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.sku or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
