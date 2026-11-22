"""Clearance pricing rule (not enabled by default; enable it through extra_rules)."""
from decimal import Decimal

from ..base import Rule


class ClearanceRule(Rule):
    name = "clearance"
    priority = 60

    def applies(self, order) -> bool:
        return bool(self.config.get("clearance_rate"))

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["clearance_rate"]))
