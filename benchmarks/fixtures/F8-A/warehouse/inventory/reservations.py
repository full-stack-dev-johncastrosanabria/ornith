"""Reservations helpers for the inventory subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ReservationsRecord:
    region: str = ""
    sku: str = ""
    channel: str = ""
    owner: str = ""
    batch: str = ""
    priority: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class ReservationsStore:
    """In-memory index of ReservationsRecord keyed by region."""

    def __init__(self) -> None:
        self._items: dict[str, ReservationsRecord] = {}

    def add(self, record: ReservationsRecord) -> None:
        if not record.region:
            raise ValueError("region is required")
        if record.region in self._items:
            raise KeyError(f"duplicate region: {record.region}")
        self._items[record.region] = record
        record.touch("added")

    def get(self, region: str) -> ReservationsRecord | None:
        return self._items.get(region)

    def find(self, **criteria: str) -> list[ReservationsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def validate_priority_0(records: list[ReservationsRecord], limit: int = 28) -> dict[str, int]:
    """Count records by priority, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.priority or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def route_owner_1(records: list[ReservationsRecord], limit: int = 7) -> dict[str, int]:
    """Count records by owner, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.owner or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def score_owner_2(records: list[ReservationsRecord], limit: int = 9) -> dict[str, int]:
    """Count records by owner, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.owner or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
