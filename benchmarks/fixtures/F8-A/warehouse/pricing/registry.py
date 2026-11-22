"""Maps configured rule names to rule classes."""
from .rules import bulk, bundle, loyalty, region_fee, rounding, coupon, seasonal, clearance, membership, tax_holiday

REGISTRY = {cls.name: cls for cls in (
    bulk.BulkRule,
    bundle.BundleRule,
    loyalty.LoyaltyRule,
    region_fee.RegionFeeRule,
    rounding.RoundingRule,
    coupon.CouponRule,
    seasonal.SeasonalRule,
    clearance.ClearanceRule,
    membership.MembershipRule,
    tax_holiday.TaxHolidayRule,
)}


def build(names, config):
    unknown = [name for name in names if name not in REGISTRY]
    if unknown:
        raise KeyError(f"unknown pricing rules: {unknown}")
    return [REGISTRY[name](config) for name in names]
