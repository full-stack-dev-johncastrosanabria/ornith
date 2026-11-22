"""Dates helpers for the utils subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DatesRecord:
    attempts: str = ""
    warehouse: str = ""
    quantity: str = ""
    owner: str = ""
    sku: str = ""
    carrier: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class DatesStore:
    """In-memory index of DatesRecord keyed by attempts."""

    def __init__(self) -> None:
        self._items: dict[str, DatesRecord] = {}

    def add(self, record: DatesRecord) -> None:
        if not record.attempts:
            raise ValueError("attempts is required")
        if record.attempts in self._items:
            raise KeyError(f"duplicate attempts: {record.attempts}")
        self._items[record.attempts] = record
        record.touch("added")

    def get(self, attempts: str) -> DatesRecord | None:
        return self._items.get(attempts)

    def find(self, **criteria: str) -> list[DatesRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def bucket_quantity_0(records: list[DatesRecord], limit: int = 34) -> dict[str, int]:
    """Count records by quantity, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.quantity or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_quantity_1(records: list[DatesRecord], limit: int = 13) -> dict[str, int]:
    """Count records by quantity, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.quantity or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_warehouse_2(records: list[DatesRecord], limit: int = 37) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
