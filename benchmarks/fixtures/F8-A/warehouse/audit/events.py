"""Events helpers for the audit subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class EventsRecord:
    reference: str = ""
    owner: str = ""
    attempts: str = ""
    weight_kg: str = ""
    quantity: str = ""
    carrier: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class EventsStore:
    """In-memory index of EventsRecord keyed by reference."""

    def __init__(self) -> None:
        self._items: dict[str, EventsRecord] = {}

    def add(self, record: EventsRecord) -> None:
        if not record.reference:
            raise ValueError("reference is required")
        if record.reference in self._items:
            raise KeyError(f"duplicate reference: {record.reference}")
        self._items[record.reference] = record
        record.touch("added")

    def get(self, reference: str) -> EventsRecord | None:
        return self._items.get(reference)

    def find(self, **criteria: str) -> list[EventsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def route_carrier_0(records: list[EventsRecord], limit: int = 27) -> dict[str, int]:
    """Count records by carrier, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.carrier or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def bucket_reference_1(records: list[EventsRecord], limit: int = 40) -> dict[str, int]:
    """Count records by reference, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.reference or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_carrier_2(records: list[EventsRecord], limit: int = 8) -> dict[str, int]:
    """Count records by carrier, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.carrier or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
