"""Membership pricing rule (not enabled by default; enable it through extra_rules)."""
from decimal import Decimal

from ..base import Rule


class MembershipRule(Rule):
    name = "membership"
    priority = 35

    def applies(self, order) -> bool:
        return bool(self.config.get("membership_rate"))

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["membership_rate"]))
