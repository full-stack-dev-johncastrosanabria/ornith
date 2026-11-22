"""Products helpers for the catalog subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ProductsRecord:
    sku: str = ""
    attempts: str = ""
    created_at: str = ""
    notes: str = ""
    region: str = ""
    owner: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class ProductsStore:
    """In-memory index of ProductsRecord keyed by sku."""

    def __init__(self) -> None:
        self._items: dict[str, ProductsRecord] = {}

    def add(self, record: ProductsRecord) -> None:
        if not record.sku:
            raise ValueError("sku is required")
        if record.sku in self._items:
            raise KeyError(f"duplicate sku: {record.sku}")
        self._items[record.sku] = record
        record.touch("added")

    def get(self, sku: str) -> ProductsRecord | None:
        return self._items.get(sku)

    def find(self, **criteria: str) -> list[ProductsRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def validate_notes_0(records: list[ProductsRecord], limit: int = 26) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def bucket_attempts_1(records: list[ProductsRecord], limit: int = 16) -> dict[str, int]:
    """Count records by attempts, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.attempts or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def validate_notes_2(records: list[ProductsRecord], limit: int = 24) -> dict[str, int]:
    """Count records by notes, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.notes or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
