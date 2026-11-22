from .utils.money import to_cents


def coupon_cents(value: float) -> int:
    return to_cents(value)
