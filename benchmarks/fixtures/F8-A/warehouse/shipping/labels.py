"""Labels helpers for the shipping subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LabelsRecord:
    status: str = ""
    warehouse: str = ""
    notes: str = ""
    batch: str = ""
    priority: str = ""
    channel: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class LabelsStore:
    """In-memory index of LabelsRecord keyed by status."""

    def __init__(self) -> None:
        self._items: dict[str, LabelsRecord] = {}

    def add(self, record: LabelsRecord) -> None:
        if not record.status:
            raise ValueError("status is required")
        if record.status in self._items:
            raise KeyError(f"duplicate status: {record.status}")
        self._items[record.status] = record
        record.touch("added")

    def get(self, status: str) -> LabelsRecord | None:
        return self._items.get(status)

    def find(self, **criteria: str) -> list[LabelsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def describe_priority_0(records: list[LabelsRecord], limit: int = 33) -> dict[str, int]:
    """Count records by priority, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.priority or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def normalize_batch_1(records: list[LabelsRecord], limit: int = 29) -> dict[str, int]:
    """Count records by batch, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.batch or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def summarize_priority_2(records: list[LabelsRecord], limit: int = 20) -> dict[str, int]:
    """Count records by priority, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.priority or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
