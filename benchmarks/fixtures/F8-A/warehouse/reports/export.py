"""Export helpers for the reports subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ExportRecord:
    channel: str = ""
    batch: str = ""
    region: str = ""
    warehouse: str = ""
    status: str = ""
    quantity: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class ExportStore:
    """In-memory index of ExportRecord keyed by channel."""

    def __init__(self) -> None:
        self._items: dict[str, ExportRecord] = {}

    def add(self, record: ExportRecord) -> None:
        if not record.channel:
            raise ValueError("channel is required")
        if record.channel in self._items:
            raise KeyError(f"duplicate channel: {record.channel}")
        self._items[record.channel] = record
        record.touch("added")

    def get(self, channel: str) -> ExportRecord | None:
        return self._items.get(channel)

    def find(self, **criteria: str) -> list[ExportRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_status_0(records: list[ExportRecord], limit: int = 36) -> dict[str, int]:
    """Count records by status, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.status or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def bucket_warehouse_1(records: list[ExportRecord], limit: int = 14) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def score_status_2(records: list[ExportRecord], limit: int = 25) -> dict[str, int]:
    """Count records by status, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.status or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
