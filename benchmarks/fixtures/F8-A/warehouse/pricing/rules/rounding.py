from decimal import ROUND_HALF_UP, Decimal

from ..base import Rule


class RoundingRule(Rule):
    """Cash rounding to the configured step; always the last rule."""

    name = "rounding"
    priority = 100

    def apply(self, total: Decimal, order) -> Decimal:
        step = self.config["rounding_step"]
        return (total / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step
