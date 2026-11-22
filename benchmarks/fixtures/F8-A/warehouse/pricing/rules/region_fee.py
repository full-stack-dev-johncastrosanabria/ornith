from decimal import Decimal

from ..base import Rule


class RegionFeeRule(Rule):
    """Fixed delivery fee per region; fixed amounts run after percentage rules."""

    name = "region_fee"
    priority = 80

    def applies(self, order) -> bool:
        return order.region in self.config["region_fees"]

    def apply(self, total: Decimal, order) -> Decimal:
        return total + self.config["region_fees"][order.region]
