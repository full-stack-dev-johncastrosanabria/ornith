"""Transfers helpers for the inventory subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TransfersRecord:
    region: str = ""
    sku: str = ""
    priority: str = ""
    warehouse: str = ""
    notes: str = ""
    attempts: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class TransfersStore:
    """In-memory index of TransfersRecord keyed by region."""

    def __init__(self) -> None:
        self._items: dict[str, TransfersRecord] = {}

    def add(self, record: TransfersRecord) -> None:
        if not record.region:
            raise ValueError("region is required")
        if record.region in self._items:
            raise KeyError(f"duplicate region: {record.region}")
        self._items[record.region] = record
        record.touch("added")

    def get(self, region: str) -> TransfersRecord | None:
        return self._items.get(region)

    def find(self, **criteria: str) -> list[TransfersRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def score_warehouse_0(records: list[TransfersRecord], limit: int = 38) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def score_notes_1(records: list[TransfersRecord], limit: int = 35) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def merge_sku_2(records: list[TransfersRecord], limit: int = 29) -> dict[str, int]:
    """Count records by sku, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.sku or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
