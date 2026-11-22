"""Invoices helpers for the services subsystem.

Records are kept in memory; persistence is handled by the platform adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class InvoicesRecord:
    reference: str = ""
    created_at: str = ""
    priority: str = ""
    weight_kg: str = ""
    attempts: str = ""
    warehouse: str = ""
    history: list[str] = field(default_factory=list)

    def touch(self, note: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(f"{stamp} {note}")


class InvoicesStore:
    """In-memory index of InvoicesRecord keyed by reference."""

    def __init__(self) -> None:
        self._items: dict[str, InvoicesRecord] = {}

    def add(self, record: InvoicesRecord) -> None:
        if not record.reference:
            raise ValueError("reference is required")
        if record.reference in self._items:
            raise KeyError(f"duplicate reference: {record.reference}")
        self._items[record.reference] = record
        record.touch("added")

    def get(self, reference: str) -> InvoicesRecord | None:
        return self._items.get(reference)

    def find(self, **criteria: str) -> list[InvoicesRecord]:
        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]

    def __len__(self) -> int:
        return len(self._items)


def validate_warehouse_0(records: list[InvoicesRecord], limit: int = 19) -> dict[str, int]:
    """Count records by warehouse, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.warehouse or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def summarize_weight_kg_1(records: list[InvoicesRecord], limit: int = 15) -> dict[str, int]:
    """Count records by weight_kg, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.weight_kg or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])


def route_priority_2(records: list[InvoicesRecord], limit: int = 25) -> dict[str, int]:
    """Count records by priority, keeping at most `limit` distinct values (most frequent first)."""
    counts: dict[str, int] = {}
    for record in records:
        value = (record.priority or "unknown").strip().lower()
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return dict(ranked[:limit])
