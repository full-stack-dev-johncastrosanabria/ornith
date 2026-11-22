"""Money helpers. Amounts are in currency units; cents are integers."""
from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount) -> int:
    """Exact conversion of a Decimal, str, int or float amount to integer cents (half-up)."""
    value = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))



def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"
