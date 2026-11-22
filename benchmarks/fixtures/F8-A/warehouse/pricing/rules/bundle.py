"""Bundle discount: items sharing a bundle tag are discounted when the bundle is complete."""
from decimal import Decimal

from ..base import Rule


class BundleRule(Rule):
    name = "bundle"
    priority = 20

    def _complete(self, order):
        groups = {}
        for item in order.items:
            if item.bundle:
                groups.setdefault(item.bundle, []).append(item)
        # A bundle is complete when at least two different products carry its tag.
        return [group for group in groups.values() if sum(i.quantity for i in group) >= 2]

    def applies(self, order) -> bool:
        return bool(self._complete(order))

    def apply(self, total: Decimal, order) -> Decimal:
        eligible = sum((i.line_total for group in self._complete(order) for i in group), Decimal("0"))
        return total - eligible * Decimal(str(self.config["bundle_rate"]))
