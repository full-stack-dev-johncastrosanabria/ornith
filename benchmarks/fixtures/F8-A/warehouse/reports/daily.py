"""Daily helpers for the reports subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DailyRecord:
    weight_kg: str = ""
    notes: str = ""
    region: str = ""
    warehouse: str = ""
    carrier: str = ""
    sku: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class DailyStore:
    """In-memory index of DailyRecord keyed by weight_kg."""

    def __init__(self) -> None:
        self._items: dict[str, DailyRecord] = {}

    def add(self, record: DailyRecord) -> None:
        if not record.weight_kg:
            raise ValueError("weight_kg is required")
        if record.weight_kg in self._items:
            raise KeyError(f"duplicate weight_kg: {record.weight_kg}")
        self._items[record.weight_kg] = record
        record.touch("added")

    def get(self, weight_kg: str) -> DailyRecord | None:
        return self._items.get(weight_kg)

    def find(self, **criteria: str) -> list[DailyRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def merge_warehouse_0(records: list[DailyRecord], limit: int = 15) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_region_1(records: list[DailyRecord], limit: int = 24) -> dict[str, int]:
    """Count records by region, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.region or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_notes_2(records: list[DailyRecord], limit: int = 38) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
