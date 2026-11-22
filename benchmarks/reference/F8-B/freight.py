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


from decimal import ROUND_CEILING, ROUND_HALF_UP

RANGES = [('00', '11'), ('12', '23'), ('24', '35'), ('36', '47'), ('48', '59'), ('60', '71'), ('72', '85'), ('86', '99')]
REGIONS = "ABCDEFGH"
ZONE = {'AA': 1, 'AB': 2, 'AC': 3, 'AD': 4, 'AE': 5, 'AF': 6, 'AG': 6, 'AH': 3, 'BA': 2, 'BB': 1, 'BC': 2, 'BD': 4, 'BE': 4, 'BF': 5, 'BG': 6, 'BH': 6, 'CA': 3, 'CB': 2, 'CC': 1, 'CD': 3, 'CE': 3, 'CF': 4, 'CG': 5, 'CH': 6, 'DA': 4, 'DB': 4, 'DC': 3, 'DD': 1, 'DE': 3, 'DF': 4, 'DG': 4, 'DH': 5, 'EA': 5, 'EB': 4, 'EC': 3, 'ED': 3, 'EE': 1, 'EF': 3, 'EG': 3, 'EH': 5, 'FA': 6, 'FB': 5, 'FC': 4, 'FD': 4, 'FE': 3, 'FF': 1, 'FG': 2, 'FH': 3, 'GA': 6, 'GB': 6, 'GC': 5, 'GD': 4, 'GE': 3, 'GF': 2, 'GG': 1, 'GH': 2, 'HA': 3, 'HB': 6, 'HC': 6, 'HD': 5, 'HE': 5, 'HF': 3, 'HG': 2, 'HH': 1}
TARIFF = {1: {'ground': (Decimal('6.25'), Decimal('0.82')), 'express': (Decimal('11.25'), Decimal('1.31'))}, 2: {'ground': (Decimal('7.10'), Decimal('1.04')), 'express': (Decimal('12.78'), Decimal('1.66'))}, 3: {'ground': (Decimal('7.95'), Decimal('1.26')), 'express': (Decimal('14.31'), Decimal('2.02'))}, 4: {'ground': (Decimal('8.80'), Decimal('1.48')), 'express': (Decimal('15.84'), Decimal('2.37'))}, 5: {'ground': (Decimal('9.65'), Decimal('1.70')), 'express': (Decimal('17.37'), Decimal('2.72'))}, 6: {'ground': (Decimal('10.50'), Decimal('1.92')), 'express': (Decimal('18.90'), Decimal('3.07'))}}
FUEL = {1: Decimal('8.75'), 2: Decimal('8.5'), 3: Decimal('9.25'), 4: Decimal('9.0'), 5: Decimal('9.25'), 6: Decimal('9.5'), 7: Decimal('10.25'), 8: Decimal('10.5'), 9: Decimal('10.25'), 10: Decimal('10.5'), 11: Decimal('10.25'), 12: Decimal('11.0')}
REMOTE = {'085', '399', '757', '314', '086', '923', '131', '698', '451', '855', '349', '941'}
CONTRACTS = {'ACME': {'ground': Decimal('12'), 'express': Decimal('12')}, 'GLOBEX': {'ground': Decimal('8'), 'express': Decimal('8')}, 'INITECH': {'ground': Decimal('0'), 'express': Decimal('15')}, 'UMBRELLA': {'ground': Decimal('5'), 'express': Decimal('5')}}


def region(code):
    prefix = code[:2]
    for letter, (lo, hi) in zip(REGIONS, RANGES):
        if lo <= prefix <= hi:
            return letter
    raise RateError(code)


def rate(shipment: Shipment) -> Decimal:
    s = shipment
    for code in (s.origin, s.destination):
        if len(code) != 5 or not code.isdigit():
            raise RateError("postal code")
    if s.service not in ("ground", "express") or not 1 <= s.month <= 12:
        raise RateError("service or month")
    if not Decimal("0") < s.weight_kg <= Decimal("70") or min(s.length_cm, s.width_cm, s.height_cm) < 1:
        raise RateError("weight or dimensions")
    if s.customer != "standard" and s.customer not in CONTRACTS:
        raise RateError("contract")
    divisor = 5000 if s.service == "ground" else 4000
    volumetric = Decimal(s.length_cm * s.width_cm * s.height_cm) / divisor
    billable = max(s.weight_kg, volumetric, Decimal("1"))
    billable = (billable * 2).to_integral_value(rounding=ROUND_CEILING) / 2
    first, extra = TARIFF[ZONE[region(s.origin) + region(s.destination)]][s.service]
    base = first + extra * ((billable - 1) * 2)
    fuel = base * FUEL[s.month] / 100
    pct = CONTRACTS[s.customer][s.service] if s.customer != "standard" else Decimal("0")
    total = (base + fuel) * (100 - pct) / 100
    if s.destination[:3] in REMOTE:
        total += Decimal("7.50")
    sides = sorted((s.length_cm, s.width_cm, s.height_cm), reverse=True)
    if sides[0] > 120 or sides[0] + 2 * (sides[1] + sides[2]) > 300:
        total += Decimal("25.00")
    if billable > 30:
        total += Decimal("15.00")
    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return max(total, Decimal("6.90"))
