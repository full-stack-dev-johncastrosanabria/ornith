"""Stock helpers for the inventory subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class StockRecord:
    carrier: str = ""
    owner: str = ""
    batch: str = ""
    attempts: str = ""
    quantity: str = ""
    notes: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class StockStore:
    """In-memory index of StockRecord keyed by carrier."""

    def __init__(self) -> None:
        self._items: dict[str, StockRecord] = {}

    def add(self, record: StockRecord) -> None:
        if not record.carrier:
            raise ValueError("carrier is required")
        if record.carrier in self._items:
            raise KeyError(f"duplicate carrier: {record.carrier}")
        self._items[record.carrier] = record
        record.touch("added")

    def get(self, carrier: str) -> StockRecord | None:
        return self._items.get(carrier)

    def find(self, **criteria: str) -> list[StockRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def bucket_attempts_0(records: list[StockRecord], limit: int = 5) -> dict[str, int]:
    """Count records by attempts, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.attempts or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_notes_1(records: list[StockRecord], limit: int = 22) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def normalize_owner_2(records: list[StockRecord], limit: int = 13) -> dict[str, int]:
    """Count records by owner, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.owner or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
