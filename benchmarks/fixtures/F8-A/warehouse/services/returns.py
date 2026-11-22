"""Returns helpers for the services subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ReturnsRecord:
    priority: str = ""
    carrier: str = ""
    notes: str = ""
    sku: str = ""
    status: str = ""
    region: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class ReturnsStore:
    """In-memory index of ReturnsRecord keyed by priority."""

    def __init__(self) -> None:
        self._items: dict[str, ReturnsRecord] = {}

    def add(self, record: ReturnsRecord) -> None:
        if not record.priority:
            raise ValueError("priority is required")
        if record.priority in self._items:
            raise KeyError(f"duplicate priority: {record.priority}")
        self._items[record.priority] = record
        record.touch("added")

    def get(self, priority: str) -> ReturnsRecord | None:
        return self._items.get(priority)

    def find(self, **criteria: str) -> list[ReturnsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_sku_0(records: list[ReturnsRecord], limit: int = 29) -> dict[str, int]:
    """Count records by sku, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.sku or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def bucket_priority_1(records: list[ReturnsRecord], limit: int = 22) -> dict[str, int]:
    """Count records by priority, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.priority or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_carrier_2(records: list[ReturnsRecord], limit: int = 31) -> dict[str, int]:
    """Count records by carrier, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.carrier or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
