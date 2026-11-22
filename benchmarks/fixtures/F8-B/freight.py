"""Freight charges for parcel shipments. The rules are specified in SPEC.md."""
from dataclasses import dataclass
from decimal import Decimal


class RateError(ValueError):
    """Raised for shipments that SPEC.md declares invalid."""


@dataclass(frozen=True)
class Shipment:
    origin: str  # 5-digit postal code
    destination: str  # 5-digit postal code
    weight_kg: Decimal
    length_cm: int
    width_cm: int
    height_cm: int
    month: int  # shipping month, 1..12
    customer: str = "standard"  # "standard" or a contract code
    service: str = "ground"  # "ground" or "express"


def rate(shipment: Shipment) -> Decimal:
    """Return the freight charge in EUR, following SPEC.md section 9 ("Calculation order")."""
    raise NotImplementedError
