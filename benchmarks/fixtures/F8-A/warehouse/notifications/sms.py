"""Sms helpers for the notifications subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SmsRecord:
    sku: str = ""
    status: str = ""
    reference: str = ""
    batch: str = ""
    attempts: str = ""
    carrier: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class SmsStore:
    """In-memory index of SmsRecord keyed by sku."""

    def __init__(self) -> None:
        self._items: dict[str, SmsRecord] = {}

    def add(self, record: SmsRecord) -> None:
        if not record.sku:
            raise ValueError("sku is required")
        if record.sku in self._items:
            raise KeyError(f"duplicate sku: {record.sku}")
        self._items[record.sku] = record
        record.touch("added")

    def get(self, sku: str) -> SmsRecord | None:
        return self._items.get(sku)

    def find(self, **criteria: str) -> list[SmsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def summarize_attempts_0(records: list[SmsRecord], limit: int = 37) -> dict[str, int]:
    """Count records by attempts, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.attempts or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_batch_1(records: list[SmsRecord], limit: int = 12) -> dict[str, int]:
    """Count records by batch, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.batch or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def describe_reference_2(records: list[SmsRecord], limit: int = 11) -> dict[str, int]:
    """Count records by reference, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.reference or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
