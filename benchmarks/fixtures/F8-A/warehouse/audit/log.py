"""Log helpers for the audit subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LogRecord:
    channel: str = ""
    carrier: str = ""
    reference: str = ""
    region: str = ""
    notes: str = ""
    batch: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class LogStore:
    """In-memory index of LogRecord keyed by channel."""

    def __init__(self) -> None:
        self._items: dict[str, LogRecord] = {}

    def add(self, record: LogRecord) -> None:
        if not record.channel:
            raise ValueError("channel is required")
        if record.channel in self._items:
            raise KeyError(f"duplicate channel: {record.channel}")
        self._items[record.channel] = record
        record.touch("added")

    def get(self, channel: str) -> LogRecord | None:
        return self._items.get(channel)

    def find(self, **criteria: str) -> list[LogRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def route_channel_0(records: list[LogRecord], limit: int = 14) -> dict[str, int]:
    """Count records by channel, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.channel or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def summarize_carrier_1(records: list[LogRecord], limit: int = 20) -> dict[str, int]:
    """Count records by carrier, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.carrier or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def merge_region_2(records: list[LogRecord], limit: int = 28) -> dict[str, int]:
    """Count records by region, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.region or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
