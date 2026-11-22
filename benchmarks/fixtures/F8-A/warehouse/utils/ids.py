"""Ids helpers for the utils subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class IdsRecord:
    warehouse: str = ""
    notes: str = ""
    region: str = ""
    reference: str = ""
    channel: str = ""
    batch: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class IdsStore:
    """In-memory index of IdsRecord keyed by warehouse."""

    def __init__(self) -> None:
        self._items: dict[str, IdsRecord] = {}

    def add(self, record: IdsRecord) -> None:
        if not record.warehouse:
            raise ValueError("warehouse is required")
        if record.warehouse in self._items:
            raise KeyError(f"duplicate warehouse: {record.warehouse}")
        self._items[record.warehouse] = record
        record.touch("added")

    def get(self, warehouse: str) -> IdsRecord | None:
        return self._items.get(warehouse)

    def find(self, **criteria: str) -> list[IdsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_batch_0(records: list[IdsRecord], limit: int = 37) -> dict[str, int]:
    """Count records by batch, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.batch or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_notes_1(records: list[IdsRecord], limit: int = 37) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def merge_channel_2(records: list[IdsRecord], limit: int = 16) -> dict[str, int]:
    """Count records by channel, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.channel or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
