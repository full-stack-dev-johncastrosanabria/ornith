from decimal import Decimal

DEFAULTS = {
    "rules": ["bulk", "bundle", "region_fee", "rounding"],
    "region_fees": {"north": Decimal("4.50"), "south": Decimal("6.00"), "islands": Decimal("12.00")},
    "loyalty_rates": {"gold": Decimal("0.07"), "silver": Decimal("0.03")},
    "bulk_threshold": 50,
    "bulk_rate": Decimal("0.05"),
    "bundle_rate": Decimal("0.15"),
    "rounding_step": Decimal("0.05"),
}
