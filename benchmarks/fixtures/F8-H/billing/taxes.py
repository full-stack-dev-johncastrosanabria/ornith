from .utils.money import to_cents_legacy


def tax_cents(amount: str, rate: str) -> int:
    """Tax on `amount` at `rate`, both given as decimal strings."""
    return to_cents_legacy(float(amount) * float(rate))
