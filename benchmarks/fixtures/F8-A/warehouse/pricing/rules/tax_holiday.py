"""TaxHoliday pricing rule (not enabled by default; enable it through extra_rules)."""
from decimal import Decimal

from ..base import Rule


class TaxHolidayRule(Rule):
    name = "tax_holiday"
    priority = 90

    def applies(self, order) -> bool:
        return bool(self.config.get("tax_holiday_rate"))

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["tax_holiday_rate"]))
