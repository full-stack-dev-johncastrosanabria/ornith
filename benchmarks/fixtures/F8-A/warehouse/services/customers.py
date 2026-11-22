"""Customers helpers for the services subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CustomersRecord:
    region: str = ""
    sku: str = ""
    owner: str = ""
    weight_kg: str = ""
    created_at: str = ""
    status: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class CustomersStore:
    """In-memory index of CustomersRecord keyed by region."""

    def __init__(self) -> None:
        self._items: dict[str, CustomersRecord] = {}

    def add(self, record: CustomersRecord) -> None:
        if not record.region:
            raise ValueError("region is required")
        if record.region in self._items:
            raise KeyError(f"duplicate region: {record.region}")
        self._items[record.region] = record
        record.touch("added")

    def get(self, region: str) -> CustomersRecord | None:
        return self._items.get(region)

    def find(self, **criteria: str) -> list[CustomersRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def route_owner_0(records: list[CustomersRecord], limit: int = 33) -> dict[str, int]:
    """Count records by owner, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.owner or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def merge_created_at_1(records: list[CustomersRecord], limit: int = 20) -> dict[str, int]:
    """Count records by created_at, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.created_at or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_region_2(records: list[CustomersRecord], limit: int = 33) -> dict[str, int]:
    """Count records by region, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.region or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
