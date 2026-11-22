from decimal import Decimal

from ..base import Rule


class BulkRule(Rule):
    name = "bulk"
    priority = 10

    def applies(self, order) -> bool:
        return order.quantity >= self.config["bulk_threshold"]

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["bulk_rate"]))
