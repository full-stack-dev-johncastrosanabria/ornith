"""Carriers helpers for the shipping subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CarriersRecord:
    batch: str = ""
    sku: str = ""
    attempts: str = ""
    notes: str = ""
    priority: str = ""
    created_at: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class CarriersStore:
    """In-memory index of CarriersRecord keyed by batch."""

    def __init__(self) -> None:
        self._items: dict[str, CarriersRecord] = {}

    def add(self, record: CarriersRecord) -> None:
        if not record.batch:
            raise ValueError("batch is required")
        if record.batch in self._items:
            raise KeyError(f"duplicate batch: {record.batch}")
        self._items[record.batch] = record
        record.touch("added")

    def get(self, batch: str) -> CarriersRecord | None:
        return self._items.get(batch)

    def find(self, **criteria: str) -> list[CarriersRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def bucket_notes_0(records: list[CarriersRecord], limit: int = 39) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def route_attempts_1(records: list[CarriersRecord], limit: int = 22) -> dict[str, int]:
    """Count records by attempts, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.attempts or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def normalize_priority_2(records: list[CarriersRecord], limit: int = 39) -> dict[str, int]:
    """Count records by priority, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.priority or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
