"""Text helpers for the utils subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TextRecord:
    attempts: str = ""
    weight_kg: str = ""
    channel: str = ""
    warehouse: str = ""
    reference: str = ""
    region: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class TextStore:
    """In-memory index of TextRecord keyed by attempts."""

    def __init__(self) -> None:
        self._items: dict[str, TextRecord] = {}

    def add(self, record: TextRecord) -> None:
        if not record.attempts:
            raise ValueError("attempts is required")
        if record.attempts in self._items:
            raise KeyError(f"duplicate attempts: {record.attempts}")
        self._items[record.attempts] = record
        record.touch("added")

    def get(self, attempts: str) -> TextRecord | None:
        return self._items.get(attempts)

    def find(self, **criteria: str) -> list[TextRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_warehouse_0(records: list[TextRecord], limit: int = 38) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def normalize_warehouse_1(records: list[TextRecord], limit: int = 29) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def score_region_2(records: list[TextRecord], limit: int = 36) -> dict[str, int]:
    """Count records by region, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.region or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
