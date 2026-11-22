from decimal import Decimal


class Rule:
    """A pricing rule. Lower priority values run first."""

    name = "base"
    priority = 0

    def __init__(self, config):
        self.config = config

    def applies(self, order) -> bool:
        return True

    def apply(self, total: Decimal, order) -> Decimal:
        return total
