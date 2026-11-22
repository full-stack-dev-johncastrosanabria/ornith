"""Seasonal pricing rule (not enabled by default; enable it through extra_rules)."""
from decimal import Decimal

from ..base import Rule


class SeasonalRule(Rule):
    name = "seasonal"
    priority = 50

    def applies(self, order) -> bool:
        return bool(self.config.get("seasonal_rate"))

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["seasonal_rate"]))
