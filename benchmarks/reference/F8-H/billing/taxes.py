from decimal import Decimal

from .utils.money import to_cents


def tax_cents(amount: str, rate: str) -> int:
    """Tax on `amount` at `rate`, both given as decimal strings."""
    return to_cents(Decimal(amount) * Decimal(rate))
