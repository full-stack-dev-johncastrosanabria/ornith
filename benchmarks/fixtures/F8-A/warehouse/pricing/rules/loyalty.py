from decimal import Decimal

from ..base import Rule


class LoyaltyRule(Rule):
    name = "loyalty"
    priority = 30

    def applies(self, order) -> bool:
        return self.config.get("tier") in self.config["loyalty_rates"]

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * self.config["loyalty_rates"][self.config["tier"]]
