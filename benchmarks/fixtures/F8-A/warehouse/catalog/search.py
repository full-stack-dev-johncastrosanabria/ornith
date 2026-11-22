"""Search helpers for the catalog subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SearchRecord:
    sku: str = ""
    owner: str = ""
    weight_kg: str = ""
    warehouse: str = ""
    quantity: str = ""
    attempts: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class SearchStore:
    """In-memory index of SearchRecord keyed by sku."""

    def __init__(self) -> None:
        self._items: dict[str, SearchRecord] = {}

    def add(self, record: SearchRecord) -> None:
        if not record.sku:
            raise ValueError("sku is required")
        if record.sku in self._items:
            raise KeyError(f"duplicate sku: {record.sku}")
        self._items[record.sku] = record
        record.touch("added")

    def get(self, sku: str) -> SearchRecord | None:
        return self._items.get(sku)

    def find(self, **criteria: str) -> list[SearchRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def normalize_sku_0(records: list[SearchRecord], limit: int = 23) -> dict[str, int]:
    """Count records by sku, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.sku or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def merge_owner_1(records: list[SearchRecord], limit: int = 40) -> dict[str, int]:
    """Count records by owner, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.owner or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def route_weight_kg_2(records: list[SearchRecord], limit: int = 30) -> dict[str, int]:
    """Count records by weight_kg, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.weight_kg or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
