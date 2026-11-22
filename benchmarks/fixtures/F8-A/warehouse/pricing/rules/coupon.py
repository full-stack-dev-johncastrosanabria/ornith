"""Coupon pricing rule (not enabled by default; enable it through extra_rules)."""
from decimal import Decimal

from ..base import Rule


class CouponRule(Rule):
    name = "coupon"
    priority = 40

    def applies(self, order) -> bool:
        return bool(self.config.get("coupon_rate"))

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["coupon_rate"]))
