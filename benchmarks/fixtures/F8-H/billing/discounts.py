from .utils.money import to_cents_legacy


def coupon_cents(value: float) -> int:
    return to_cents_legacy(value)
