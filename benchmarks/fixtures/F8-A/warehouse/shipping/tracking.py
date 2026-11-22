"""Tracking helpers for the shipping subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TrackingRecord:
    carrier: str = ""
    reference: str = ""
    status: str = ""
    batch: str = ""
    weight_kg: str = ""
    sku: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class TrackingStore:
    """In-memory index of TrackingRecord keyed by carrier."""

    def __init__(self) -> None:
        self._items: dict[str, TrackingRecord] = {}

    def add(self, record: TrackingRecord) -> None:
        if not record.carrier:
            raise ValueError("carrier is required")
        if record.carrier in self._items:
            raise KeyError(f"duplicate carrier: {record.carrier}")
        self._items[record.carrier] = record
        record.touch("added")

    def get(self, carrier: str) -> TrackingRecord | None:
        return self._items.get(carrier)

    def find(self, **criteria: str) -> list[TrackingRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_sku_0(records: list[TrackingRecord], limit: int = 35) -> dict[str, int]:
    """Count records by sku, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.sku or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def normalize_weight_kg_1(records: list[TrackingRecord], limit: int = 30) -> dict[str, int]:
    """Count records by weight_kg, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.weight_kg or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def score_status_2(records: list[TrackingRecord], limit: int = 35) -> dict[str, int]:
    """Count records by status, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.status or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
