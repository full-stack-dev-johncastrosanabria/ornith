"""Applies the configured pricing rules to an order."""
from decimal import Decimal

from .registry import build


def price(order, config):
    """Return the order total after every applicable rule, in ascending priority order."""
    total = order.subtotal
    for rule in sorted(build(config["rules"], config), key=lambda r: r.priority, reverse=True):
        if rule.applies(order):
            total = rule.apply(total, order)
    return total.quantize(Decimal("0.01"))
