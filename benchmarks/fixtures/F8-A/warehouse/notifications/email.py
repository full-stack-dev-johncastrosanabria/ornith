"""Email helpers for the notifications subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class EmailRecord:
    carrier: str = ""
    quantity: str = ""
    notes: str = ""
    attempts: str = ""
    weight_kg: str = ""
    batch: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class EmailStore:
    """In-memory index of EmailRecord keyed by carrier."""

    def __init__(self) -> None:
        self._items: dict[str, EmailRecord] = {}

    def add(self, record: EmailRecord) -> None:
        if not record.carrier:
            raise ValueError("carrier is required")
        if record.carrier in self._items:
            raise KeyError(f"duplicate carrier: {record.carrier}")
        self._items[record.carrier] = record
        record.touch("added")

    def get(self, carrier: str) -> EmailRecord | None:
        return self._items.get(carrier)

    def find(self, **criteria: str) -> list[EmailRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def bucket_attempts_0(records: list[EmailRecord], limit: int = 34) -> dict[str, int]:
    """Count records by attempts, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.attempts or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_notes_1(records: list[EmailRecord], limit: int = 30) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def normalize_attempts_2(records: list[EmailRecord], limit: int = 6) -> dict[str, int]:
    """Count records by attempts, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.attempts or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
