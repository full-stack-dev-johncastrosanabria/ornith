"""D061 fixtures F8-A (repo navigation), F8-B (long spec), F8-C (large log), F8-H (many call sites).

Each builder returns (files, reference_overlay, prompt). Deterministic: fixed seeds only.
"""
import math,random,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from decimal import Decimal,ROUND_HALF_UP

# ---------------------------------------------------------------- F8-A
FILLER_A=['inventory/stock','inventory/reservations','inventory/transfers','shipping/carriers','shipping/labels','shipping/tracking',
          'notifications/email','notifications/templates','notifications/sms','audit/log','audit/events','reports/daily','reports/export',
          'catalog/products','catalog/search','catalog/categories','services/returns','services/customers','services/invoices',
          'utils/dates','utils/text','utils/ids']
UNUSED_RULES=[('coupon','CouponRule',40,'coupon_rate'),('seasonal','SeasonalRule',50,'seasonal_rate'),('clearance','ClearanceRule',60,'clearance_rate'),
              ('membership','MembershipRule',35,'membership_rate'),('tax_holiday','TaxHolidayRule',90,'tax_holiday_rate')]

def filler(path,rnd):
    top,name=path.split('/')
    cls=''.join(w.title() for w in name.split('_'))
    pool=['sku','warehouse','quantity','status','created_at','owner','reference','priority','channel','region','notes','attempts','carrier','weight_kg','batch']
    fields=rnd.sample(pool,6);key=fields[0]
    out=[f'"""{cls} helpers for the {top} subsystem.','','Records are kept in memory; persistence is handled by the platform adapters.','"""',
         'from __future__ import annotations','','from dataclasses import dataclass, field','from datetime import datetime, timezone','','',
         '@dataclass',f'class {cls}Record:']
    out+=[f'    {f}: str = ""' for f in fields]
    out+=['    history: list[str] = field(default_factory=list)','','    def touch(self, note: str) -> None:',
          '        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")','        self.history.append(f"{stamp} {note}")','','',
          f'class {cls}Store:',f'    """In-memory index of {cls}Record keyed by {key}."""','','    def __init__(self) -> None:',
          f'        self._items: dict[str, {cls}Record] = {{}}','',f'    def add(self, record: {cls}Record) -> None:',
          f'        if not record.{key}:',f'            raise ValueError("{key} is required")',f'        if record.{key} in self._items:',
          f'            raise KeyError(f"duplicate {key}: {{record.{key}}}")',f'        self._items[record.{key}] = record','        record.touch("added")','',
          f'    def get(self, {key}: str) -> {cls}Record | None:',f'        return self._items.get({key})','',
          f'    def find(self, **criteria: str) -> list[{cls}Record]:',
          '        return [r for r in self._items.values() if all(getattr(r, k) == v for k, v in criteria.items())]','',
          '    def __len__(self) -> int:','        return len(self._items)']
    for j in range(3):
        f=rnd.choice(fields);verb=rnd.choice(['normalize','summarize','validate','describe','merge','score','route','bucket'])
        out+=['','',f'def {verb}_{f}_{j}(records: list[{cls}Record], limit: int = {rnd.randint(3,40)}) -> dict[str, int]:',
              f'    """Count records by {f}, keeping at most `limit` distinct values (most frequent first)."""',
              '    counts: dict[str, int] = {}','    for record in records:',f'        value = (record.{f} or "unknown").strip().lower()',
              '        counts[value] = counts.get(value, 0) + 1','    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))',
              '    return dict(ranked[:limit])']
    return '\n'.join(out)

LOADER_A='''"""Effective configuration: DEFAULTS plus per-customer overrides."""
import copy

from .defaults import DEFAULTS


def load(overrides=None):
    """Return DEFAULTS updated by `overrides`.

    Overrides may contain 'extra_rules' (appended to the default rule list) and
    'disabled_rules' (removed from it); any other key replaces the default value.
    """
    cfg = copy.deepcopy(DEFAULTS)
    overrides = dict(overrides or {})
    extra = overrides.pop("extra_rules", None)
    disabled = set(overrides.pop("disabled_rules", ()))
    cfg.update(overrides)
    if extra:
        cfg["rules"] = list(extra)
    cfg["rules"] = [rule for rule in cfg["rules"] if rule not in disabled]
    return cfg
'''
ENGINE_A='''"""Applies the configured pricing rules to an order."""
from decimal import Decimal

from .registry import build


def price(order, config):
    """Return the order total after every applicable rule, in ascending priority order."""
    total = order.subtotal
    for rule in sorted(build(config["rules"], config), key=lambda r: r.priority, reverse=True):
        if rule.applies(order):
            total = rule.apply(total, order)
    return total.quantize(Decimal("0.01"))
'''
BUNDLE_A='''"""Bundle discount: items sharing a bundle tag are discounted when the bundle is complete."""
from decimal import Decimal

from ..base import Rule


class BundleRule(Rule):
    name = "bundle"
    priority = 20

    def _complete(self, order):
        groups = {}
        for item in order.items:
            if item.bundle:
                groups.setdefault(item.bundle, []).append(item)
        # A bundle is complete when at least two different products carry its tag.
        return [group for group in groups.values() if sum(i.quantity for i in group) >= 2]

    def applies(self, order) -> bool:
        return bool(self._complete(order))

    def apply(self, total: Decimal, order) -> Decimal:
        eligible = sum((i.line_total for group in self._complete(order) for i in group), Decimal("0"))
        return total - eligible * Decimal(str(self.config["bundle_rate"]))
'''

def f8a():
    rnd=random.Random(8101);f={}
    f['warehouse/__init__.py']='"""Warehouse order management."""'
    f['warehouse/models.py']='''from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Item:
    sku: str
    quantity: int
    unit_price: Decimal
    bundle: str | None = None

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    customer_id: str
    region: str
    items: list[Item] = field(default_factory=list)

    @property
    def subtotal(self) -> Decimal:
        return sum((i.line_total for i in self.items), Decimal("0"))

    @property
    def quantity(self) -> int:
        return sum(i.quantity for i in self.items)'''
    f['warehouse/config/__init__.py']=''
    f['warehouse/config/defaults.py']='''from decimal import Decimal

DEFAULTS = {
    "rules": ["bulk", "bundle", "region_fee", "rounding"],
    "region_fees": {"north": Decimal("4.50"), "south": Decimal("6.00"), "islands": Decimal("12.00")},
    "loyalty_rates": {"gold": Decimal("0.07"), "silver": Decimal("0.03")},
    "bulk_threshold": 50,
    "bulk_rate": Decimal("0.05"),
    "bundle_rate": Decimal("0.15"),
    "rounding_step": Decimal("0.05"),
}'''
    f['warehouse/config/customers.py']='''"""Per-customer configuration overrides (see config.loader.load)."""

CUSTOMERS = {
    "c-100": {},
    "c-200": {"tier": "gold", "extra_rules": ["loyalty"]},
    "c-300": {"tier": "silver", "extra_rules": ["loyalty"], "disabled_rules": ["region_fee"]},
}'''
    f['warehouse/config/loader.py']=LOADER_A
    f['warehouse/pricing/__init__.py']=''
    f['warehouse/pricing/base.py']='''from decimal import Decimal


class Rule:
    """A pricing rule. Lower priority values run first."""

    name = "base"
    priority = 0

    def __init__(self, config):
        self.config = config

    def applies(self, order) -> bool:
        return True

    def apply(self, total: Decimal, order) -> Decimal:
        return total'''
    f['warehouse/pricing/engine.py']=ENGINE_A
    f['warehouse/pricing/rules/__init__.py']=''
    f['warehouse/pricing/rules/bundle.py']=BUNDLE_A
    f['warehouse/pricing/rules/bulk.py']='''from decimal import Decimal

from ..base import Rule


class BulkRule(Rule):
    name = "bulk"
    priority = 10

    def applies(self, order) -> bool:
        return order.quantity >= self.config["bulk_threshold"]

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["bulk_rate"]))'''
    f['warehouse/pricing/rules/loyalty.py']='''from decimal import Decimal

from ..base import Rule


class LoyaltyRule(Rule):
    name = "loyalty"
    priority = 30

    def applies(self, order) -> bool:
        return self.config.get("tier") in self.config["loyalty_rates"]

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * self.config["loyalty_rates"][self.config["tier"]]'''
    f['warehouse/pricing/rules/region_fee.py']='''from decimal import Decimal

from ..base import Rule


class RegionFeeRule(Rule):
    """Fixed delivery fee per region; fixed amounts run after percentage rules."""

    name = "region_fee"
    priority = 80

    def applies(self, order) -> bool:
        return order.region in self.config["region_fees"]

    def apply(self, total: Decimal, order) -> Decimal:
        return total + self.config["region_fees"][order.region]'''
    f['warehouse/pricing/rules/rounding.py']='''from decimal import ROUND_HALF_UP, Decimal

from ..base import Rule


class RoundingRule(Rule):
    """Cash rounding to the configured step; always the last rule."""

    name = "rounding"
    priority = 100

    def apply(self, total: Decimal, order) -> Decimal:
        step = self.config["rounding_step"]
        return (total / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step'''
    for name,cls,prio,key in UNUSED_RULES:
        f[f'warehouse/pricing/rules/{name}.py']=f'''"""{cls[:-4]} pricing rule (not enabled by default; enable it through extra_rules)."""
from decimal import Decimal

from ..base import Rule


class {cls}(Rule):
    name = "{name}"
    priority = {prio}

    def applies(self, order) -> bool:
        return bool(self.config.get("{key}"))

    def apply(self, total: Decimal, order) -> Decimal:
        return total - total * Decimal(str(self.config["{key}"]))'''
    mods=['bulk','bundle','loyalty','region_fee','rounding']+[n for n,*_ in UNUSED_RULES]
    classes=['bulk.BulkRule','bundle.BundleRule','loyalty.LoyaltyRule','region_fee.RegionFeeRule','rounding.RoundingRule']+[f'{n}.{c}' for n,c,*_ in UNUSED_RULES]
    f['warehouse/pricing/registry.py']='"""Maps configured rule names to rule classes."""\nfrom .rules import '+', '.join(mods)+'\n\nREGISTRY = {cls.name: cls for cls in (\n'+''.join(f'    {c},\n' for c in classes)+''')}


def build(names, config):
    unknown = [name for name in names if name not in REGISTRY]
    if unknown:
        raise KeyError(f"unknown pricing rules: {unknown}")
    return [REGISTRY[name](config) for name in names]'''
    f['warehouse/services/__init__.py']=''
    f['warehouse/services/checkout.py']='''from ..config.customers import CUSTOMERS
from ..config.loader import load
from ..pricing.engine import price


def checkout_total(order):
    """Final amount charged for `order`, using its customer's configuration."""
    return price(order, load(CUSTOMERS.get(order.customer_id, {})))'''
    for p in FILLER_A:
        pkg=p.split('/')[0]
        f.setdefault(f'warehouse/{pkg}/__init__.py','')
        f[f'warehouse/{p}.py']=filler(p,rnd)
    f['tests/__init__.py']=''
    f['tests/test_checkout.py']='''from decimal import Decimal as D

import pytest

from warehouse.config.loader import load
from warehouse.models import Item, Order
from warehouse.pricing.engine import price
from warehouse.services.checkout import checkout_total


def order(customer, region, *items):
    return Order(customer, region, list(items))


def test_regular_order_gets_region_fee():
    assert checkout_total(order("c-100", "north", Item("A-1", 2, D("25.00")), Item("B-2", 1, D("50.00")))) == D("104.50")


def test_percentages_apply_before_fixed_fees_and_rounding():
    assert checkout_total(order("c-100", "south", Item("C-3", 60, D("1.99")))) == D("119.45")


def test_complete_bundle_discount():
    assert checkout_total(order("c-100", "north", Item("K-1", 1, D("40.00"), "B1"), Item("K-2", 1, D("60.00"), "B1"), Item("Z-9", 1, D("10.00")))) == D("99.50")


def test_one_product_is_not_a_bundle():
    assert checkout_total(order("c-100", "north", Item("K-1", 3, D("40.00"), "B1"))) == D("124.50")


def test_gold_customer_keeps_default_rules():
    assert checkout_total(order("c-200", "north", Item("K-1", 1, D("40.00"), "B1"), Item("K-2", 1, D("60.00"), "B1"), Item("C-3", 50, D("1.00")))) == D("123.10")


def test_disabled_rule_is_removed():
    assert checkout_total(order("c-300", "islands", Item("A-1", 4, D("12.50")))) == D("48.50")


def test_extra_rules_extend_defaults():
    rules = load({"extra_rules": ["loyalty"]})["rules"]
    assert rules[:4] == ["bulk", "bundle", "region_fee", "rounding"] and "loyalty" in rules


def test_unknown_rule_is_rejected():
    with pytest.raises(KeyError):
        price(order("c-100", "north", Item("A-1", 1, D("1.00"))), load({"extra_rules": ["does-not-exist"]}))


def test_total_has_two_decimals():
    assert checkout_total(order("c-100", "north", Item("R-1", 1, D("10.02")))).as_tuple().exponent == -2'''
    ref={'warehouse/config/loader.py':LOADER_A.replace('        cfg["rules"] = list(extra)','        cfg["rules"] = cfg["rules"] + [rule for rule in extra if rule not in cfg["rules"]]'),
         'warehouse/pricing/engine.py':ENGINE_A.replace(', reverse=True',''),
         'warehouse/pricing/rules/bundle.py':BUNDLE_A.replace('sum(i.quantity for i in group) >= 2','len({i.sku for i in group}) >= 2')}
    assert all(ref[k]!=v for k,v in [('warehouse/config/loader.py',LOADER_A),('warehouse/pricing/engine.py',ENGINE_A),('warehouse/pricing/rules/bundle.py',BUNDLE_A)])
    prompt=('Checkout totals in the warehouse package are wrong for some orders: bulk orders, bundles, and customers with configured loyalty rules. '
            'Find and fix the defects so the acceptance tests pass. Pricing rules run in ascending priority order. '
            'The package is large: locate the relevant code before editing it.')
    return f,ref,prompt

# ---------------------------------------------------------------- F8-B
REGIONS='ABCDEFGH'
PREFIX_RANGES=[('00','11'),('12','23'),('24','35'),('36','47'),('48','59'),('60','71'),('72','85'),('86','99')]

def freight_data():
    rnd=random.Random(8102)
    zone={}
    for i,a in enumerate(REGIONS):
        for j,b in enumerate(REGIONS):
            if j<i:zone[a+b]=zone[b+a];continue
            zone[a+b]=1 if i==j else min(6,1+abs(i-j)+rnd.choice([0,0,0,1]))
    zone['AH']=zone['HA']=3  # coastal corridor exception
    tariff={z:{'ground':(Decimal('5.40')+Decimal('0.85')*z,Decimal('0.60')+Decimal('0.22')*z),
               'express':((Decimal('5.40')+Decimal('0.85')*z)*Decimal('1.8'),(Decimal('0.60')+Decimal('0.22')*z)*Decimal('1.6'))} for z in range(1,7)}
    tariff={z:{s:tuple(v.quantize(Decimal('0.01'),ROUND_HALF_UP) for v in t) for s,t in d.items()} for z,d in tariff.items()}
    fuel={m:Decimal(str(round(7.5+0.25*m+rnd.choice([0,0.5,1.0]),2))) for m in range(1,13)}
    remote=sorted(rnd.sample([f'{n:03d}' for n in range(1000)],12))
    contracts={'ACME':{'ground':Decimal('12'),'express':Decimal('12')},'GLOBEX':{'ground':Decimal('8'),'express':Decimal('8')},
               'INITECH':{'ground':Decimal('0'),'express':Decimal('15')},'UMBRELLA':{'ground':Decimal('5'),'express':Decimal('5')}}
    return zone,tariff,fuel,remote,contracts

FREIGHT_STUB='''"""Freight charges for parcel shipments. The rules are specified in SPEC.md."""
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
'''

def freight_ref(zone,tariff,fuel,remote,contracts):
    return FREIGHT_STUB.replace('''def rate(shipment: Shipment) -> Decimal:
    """Return the freight charge in EUR, following SPEC.md section 9 ("Calculation order")."""
    raise NotImplementedError
''',f'''from decimal import ROUND_CEILING, ROUND_HALF_UP

RANGES = {PREFIX_RANGES!r}
REGIONS = "{REGIONS}"
ZONE = {zone!r}
TARIFF = {tariff!r}
FUEL = {fuel!r}
REMOTE = {set(remote)!r}
CONTRACTS = {contracts!r}


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
''')

def f8b():
    zone,tariff,fuel,remote,contracts=freight_data()
    ref=freight_ref(zone,tariff,fuel,remote,contracts)
    ns={};exec(compile(ref,'freight_ref','exec'),ns)
    S,rate=ns['Shipment'],ns['rate']
    D=Decimal
    cases=[S('01020','05999',D('0.8'),20,15,10,1),S('12345','90210',D('4.2'),40,30,20,3),S('86001','00500',D('2.0'),30,20,10,6),
           S('48100','48155',D('12.5'),60,40,40,8,'ACME'),S('24000','72000',D('3.0'),50,50,50,11,'standard','express'),
           S('36000','99999',D('0.4'),10,10,5,12),S('60100','12000',D('31.0'),80,60,40,2,'GLOBEX'),
           S('72500','36500',D('9.9'),130,20,20,4),S('00001','86999',D('25.0'),100,50,30,7,'INITECH','express'),
           S('48000','24000',D('5.0'),60,60,60,9,'INITECH','ground'),S('12000','60000',D('1.25'),20,20,20,5,'UMBRELLA','express'),
           S('99000','11000',D('70'),90,50,50,10)]
    for r in remote[:2]:cases.append(S('24000',r+'42',D('3.3'),25,25,25,6))
    expected=[rate(c) for c in cases]
    def lit(c):return (f'Shipment({c.origin!r}, {c.destination!r}, D("{c.weight_kg}"), {c.length_cm}, {c.width_cm}, {c.height_cm}, {c.month}'
                       +(f', {c.customer!r}' if c.customer!='standard' or c.service!='ground' else '')+(f', {c.service!r}' if c.service!='ground' else '')+')')
    rows=''.join(f'    ({lit(c)}, D("{e}")),\n' for c,e in zip(cases,expected))
    bad=['Shipment("1234", "12345", D("1"), 10, 10, 10, 1)','Shipment("12345", "12345", D("0"), 10, 10, 10, 1)',
         'Shipment("12345", "12345", D("70.5"), 10, 10, 10, 1)','Shipment("12345", "12345", D("1"), 10, 10, 10, 13)',
         'Shipment("12345", "12345", D("1"), 10, 10, 10, 1, "WAYNE")','Shipment("12345", "12345", D("1"), 10, 10, 10, 1, "standard", "air")',
         'Shipment("12345", "12345", D("1"), 0, 10, 10, 1)']
    for b in bad:
        try:rate(eval(b,{'Shipment':S,'D':D}));raise AssertionError('invalid case accepted: '+b)
        except ns['RateError']:pass
    tests=f'''from decimal import Decimal as D

import pytest

from freight import RateError, Shipment, rate

CASES = [
{rows}]


@pytest.mark.parametrize("shipment,expected", CASES)
def test_rate(shipment, expected):
    assert rate(shipment) == expected


@pytest.mark.parametrize("shipment", [
{''.join(f'    {b},{chr(10)}' for b in bad)}])
def test_invalid(shipment):
    with pytest.raises(RateError):
        rate(shipment)
'''
    f={'freight.py':FREIGHT_STUB,'SPEC.md':freight_spec(zone,tariff,fuel,remote,contracts),'tests/__init__.py':'','tests/test_freight.py':tests}
    prompt='Implement rate() in freight.py exactly as specified in SPEC.md (a long document: read the sections you need). Keep the public names and signatures.'
    return f,{'freight.py':ref},prompt

def freight_spec(zone,tariff,fuel,remote,contracts):
    L=['# Parcel freight rating, version 3','',
       'This document specifies how the freight charge of a parcel shipment is computed. It replaces version 2 (see section 10, kept only for audit purposes). '
       'Amounts are in EUR. All arithmetic must be exact decimal arithmetic; binary floating point is not acceptable for money.','',
       '## 1. Background','',
       'Version 1 of the tariff was introduced when the network had four depots. The network now has eight regions and the tariff distinguishes six zones. '
       'Operations asked for a single, auditable calculation order (section 9) because earlier implementations applied surcharges and discounts in different orders. '
       'Customer service also reported disputes about volumetric weight on light, bulky parcels; section 4 settles them. '
       'Nothing in this background section changes the calculation.','',
       '## 2. Regions','','A postal code has exactly five digits. Its region is determined by its first two digits:','','| First two digits | Region |','|---|---|']
    L+=[f'| {lo}–{hi} | {r} |' for r,(lo,hi) in zip(REGIONS,PREFIX_RANGES)]
    L+=['','Codes that are not exactly five digits are invalid (section 8).','','## 3. Zones','',
        'The zone is looked up from the origin region (row) and the destination region (column). The table is symmetric.','',
        '| from \\ to | '+' | '.join(REGIONS)+' |','|---|'+'---|'*len(REGIONS)]
    L+=[f'| {a} | '+' | '.join(str(zone[a+b]) for b in REGIONS)+' |' for a in REGIONS]
    L+=['','Note: the A–H corridor is zone 3 by agreement with the coastal carrier, although the regions are far apart.','',
        '## 4. Billable weight','',
        '1. Volumetric weight (kg) = length × width × height (cm) divided by the service divisor: **5000 for ground, 4000 for express**.',
        '2. Billable weight is the largest of: the actual weight, the volumetric weight, and 1.0 kg.',
        '3. The billable weight is then rounded **up** to the next multiple of 0.5 kg (a value that is already a multiple stays unchanged).','',
        'Example: an express parcel of 30×20×10 cm weighing 0.8 kg has a volumetric weight of 1.5 kg, so the billable weight is 1.5 kg.','',
        '## 5. Base tariff','',
        'The base charge for a zone and service is the price of the first kilogram plus the price of each additional 0.5 kg of billable weight above 1.0 kg.','',
        '| Zone | Ground first kg | Ground each extra 0.5 kg | Express first kg | Express each extra 0.5 kg |','|---|---|---|---|---|']
    L+=[f'| {z} | {t["ground"][0]} | {t["ground"][1]} | {t["express"][0]} | {t["express"][1]} |' for z,t in tariff.items()]
    L+=['','## 6. Surcharges','','### 6.1 Fuel','',
        'A fuel surcharge is a percentage of the **base charge** only. The percentage depends on the shipping month:','','| Month | Fuel % |','|---|---|']
    L+=[f'| {m} | {p} |' for m,p in fuel.items()]
    L+=['','### 6.2 Remote destinations','',
        'If the first three digits of the destination postal code are in the list below, add a flat 7.50.','',
        ', '.join(remote)+'.','',
        '### 6.3 Oversize','',
        'Add a flat 25.00 if the longest side exceeds 120 cm, or if the longest side plus twice the sum of the other two sides exceeds 300 cm. '
        'Oversize is charged at most once per parcel.','',
        '### 6.4 Heavy parcels','','Add a flat 15.00 when the billable weight exceeds 30 kg.','',
        '## 7. Contract discounts','',
        'Shipments of contract customers receive a percentage discount on base + fuel. Flat surcharges (6.2–6.4) are never discounted. '
        'Customers that are not under contract use the code `standard` and get no discount.','','| Contract | Ground % | Express % |','|---|---|---|']
    L+=[f'| {c} | {d["ground"]} | {d["express"]} |' for c,d in contracts.items()]
    L+=['','Any other customer code is invalid (section 8).','','## 8. Validation','',
        'A shipment is invalid, and the rating must raise `RateError`, when: a postal code is not exactly five digits; the weight is not greater than 0 kg or is above 70 kg; '
        'any dimension is below 1 cm; the month is outside 1–12; the service is not `ground` or `express`; or the customer is neither `standard` nor a contract listed in section 7.','',
        '## 9. Calculation order','',
        '1. Validate the shipment (section 8).','2. Compute the billable weight (section 4).','3. Look up the zone from the origin and destination regions (sections 2 and 3).',
        '4. Compute the base charge (section 5).','5. Add the fuel surcharge on the base charge (6.1).','6. Apply the contract discount to base + fuel (section 7).',
        '7. Add the flat surcharges that apply (6.2, 6.3, 6.4).','8. Round the total half-up to 0.01.','9. If the result is below the minimum charge of **6.90**, charge 6.90.','',
        '## 10. Version 2 rules (DEPRECATED — do not implement)','',
        'Kept for audits of old invoices only. None of these rules apply to version 3:','',
        '- volumetric divisor 6000 for every service;','- totals rounded to 0.05;','- a minimum charge of 5.50;',
        '- the fuel surcharge applied to the total after the remote surcharge;','- this obsolete fuel table:','','| Month | Fuel % (v2) |','|---|---|']
    L+=[f'| {m} | {Decimal(p)+Decimal("2.25")} |' for m,p in fuel.items()]
    L+=['','## 11. Glossary','','- **Base charge**: first-kilogram price plus additional half-kilogram prices (section 5).',
        '- **Billable weight**: the weight used for pricing after volumetric comparison and rounding (section 4).',
        '- **Flat surcharge**: a fixed amount added after discounts (6.2–6.4).','']
    return '\n'.join(L)

# ---------------------------------------------------------------- F8-C
LOGSTATS='''"""Summaries of the service log format described in LOGFORMAT.md."""
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

LINE = re.compile(r"^(?P<ts>\\S+) (?P<level>[A-Z]+) (?P<service>[\\w-]+) (?P<msg>.*)$")
REQ = re.compile(r"^req .*path=(?P<path>\\S+) .*dur=(?P<dur>\\d+)")
USER = re.compile(r"user=(?P<user>u\\d+)")
CODE = re.compile(r"code=(?P<code>E\\d+)")


def parse(path):
    records = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\\n")
            if not line.strip():
                continue
            match = LINE.match(line)
            if match:
                records.append({"ts": match["ts"], "level": match["level"], "service": match["service"], "msg": match["msg"]})
            else:
                records.append({"ts": None, "level": "UNKNOWN", "service": "", "msg": line})
    return records


def _when(ts):
    return datetime.fromisoformat(ts[:19]).replace(tzinfo=timezone.utc)


def p95(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def summarize(path, since=None):
    records = parse(path)
    if since is not None:
        records = [r for r in records if r["ts"] and _when(r["ts"]) >= since]
    durations = defaultdict(list)
    users = set()
    for record in records:
        request = REQ.search(record["msg"])
        if request:
            durations[request["path"]].append(float(request["dur"]))
        user = USER.search(record["msg"])
        if user:
            users.add(user["user"])
    return {
        "records": len(records),
        "levels": dict(Counter(r["level"] for r in records)),
        "errors_by_code": dict(Counter(m["code"] for r in records if r["level"] == "ERROR" for m in [CODE.search(r["msg"])] if m)),
        "p95_ms": {path: p95(values) for path, values in durations.items()},
        "users": len(users),
    }
'''
def sub(text,old,new):
    assert text.count(old)==1,old[:60]
    return text.replace(old,new)

LOGSTATS_FIXED=sub(sub(sub(LOGSTATS,'(?P<dur>\\d+)")','(?P<dur>\\d+(?:\\.\\d+)?)ms")'),
    '''            else:
                records.append({"ts": None, "level": "UNKNOWN", "service": "", "msg": line})''','''            elif records:
                records[-1].setdefault("continuation", []).append(line)'''),
    'return datetime.fromisoformat(ts[:19]).replace(tzinfo=timezone.utc)','return datetime.fromisoformat(ts).astimezone(timezone.utc)')
LOGFORMAT='''# Service log format

Each record starts on a new line:

    <timestamp> <LEVEL> <service> <message>

- `timestamp` is ISO-8601 with seconds and an explicit UTC offset, for example `2026-03-01T10:15:02+02:00`.
  Services run in several time zones, so offsets differ between lines. Comparisons (the `since` argument of
  `summarize`) are made on the absolute instant, that is, in UTC.
- `LEVEL` is one of DEBUG, INFO, WARN, ERROR.
- A record may span several lines. Continuation lines start with whitespace or with `Traceback`; they belong to
  the record above them and are never records themselves. Text in continuation lines (including words such as
  ERROR or fields such as user=...) is ignored by every statistic.
- Request records have a message starting with `req `, e.g. `req method=GET path=/api/orders status=200 dur=12.5ms user=u042`.
  `dur` is in milliseconds and may have decimals.
- Error records may carry `code=E1234` in their message.

`summarize(path, since=None)` returns:

- `records`: the number of records;
- `levels`: records per level;
- `errors_by_code`: ERROR records per `code`;
- `p95_ms`: per request path, the 95th percentile of `dur` with the nearest-rank method
  (sort ascending; take the element at position ceil(0.95 × n), counting from 1);
- `users`: the number of distinct `user` values in request records.
'''

def gen_log():
    rnd=random.Random(8103)
    services=['api-gateway','orders','billing','auth','search'];paths=['/api/orders','/api/items','/api/login','/api/search','/api/invoices','/api/profile']
    offsets=[timedelta(0),timedelta(hours=2),timedelta(hours=-5),timedelta(hours=5,minutes=30)]
    t=datetime(2026,3,1,tzinfo=timezone.utc);lines=[]
    for n in range(620):
        t+=timedelta(seconds=rnd.randint(5,90));off=rnd.choice(offsets)
        ts=t.astimezone(timezone(off)).isoformat(timespec='seconds')
        lvl=rnd.choices(['INFO','WARN','ERROR','DEBUG'],[70,14,11,5])[0];svc=rnd.choice(services)
        if lvl=='INFO' or (lvl=='WARN' and rnd.random()<.5):
            dur=f'{rnd.randint(2,900)}.{rnd.randint(0,9)}' if rnd.random()<.7 else str(rnd.randint(2,900))
            msg=f'req method={rnd.choice(["GET","POST","PUT"])} path={rnd.choice(paths)} status={rnd.choice([200,200,200,201,204,404,500])} dur={dur}ms user=u{rnd.randint(1,140):03d}'
        elif lvl=='ERROR':
            msg=f'{rnd.choice(["payment declined","timeout calling upstream","invalid token","db deadlock","template missing"])} code=E{rnd.choice([1301,1302,2001,2104,4040,5000])}'
        elif lvl=='WARN':msg=f'slow query {rnd.randint(200,4000)}ms table={rnd.choice(["orders","items","users"])}'
        else:msg=f'cache {rnd.choice(["hit","miss"])} key=k{rnd.randint(1,9999)}'
        lines.append(f'{ts} {lvl} {svc} {msg}')
        if lvl=='ERROR' and rnd.random()<.6:
            lines.append('Traceback (most recent call last):')
            for _ in range(rnd.randint(2,5)):
                lines.append(f'  File "/srv/{svc}/{rnd.choice(["handlers","db","client"])}.py", line {rnd.randint(10,400)}, in {rnd.choice(["handle","run","fetch","commit"])}')
            lines.append(f'    raise RuntimeError("ERROR during req path={rnd.choice(paths)} dur={rnd.randint(1,99)}ms user=u{rnd.randint(500,999)}")')
    return '\n'.join(lines)+'\n'

def f8c():
    import tempfile,pathlib
    log=gen_log();ns={};exec(compile(LOGSTATS_FIXED,'logstats_ref','exec'),ns)
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/'app.log';p.write_text(log)
        full=ns['summarize'](str(p));since=datetime(2026,3,1,6,0,tzinfo=timezone.utc);part=ns['summarize'](str(p),since=since)
        buggy={};exec(compile(LOGSTATS,'logstats_bug','exec'),buggy)
        assert buggy['summarize'](str(p))!=full and buggy['summarize'](str(p),since=since)!=part
    tests=f'''from datetime import datetime, timezone

import pytest

from logstats import summarize

LOG = "logs/app.log"
FULL = {full!r}
SINCE = {part!r}


def test_records():
    assert summarize(LOG)["records"] == FULL["records"]


def test_levels():
    assert summarize(LOG)["levels"] == FULL["levels"]


def test_error_codes():
    assert summarize(LOG)["errors_by_code"] == FULL["errors_by_code"]


def test_p95():
    assert summarize(LOG)["p95_ms"] == pytest.approx(FULL["p95_ms"])


def test_users():
    assert summarize(LOG)["users"] == FULL["users"]


def test_since_compares_instants():
    result = summarize(LOG, since=datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc))
    assert result["records"] == SINCE["records"] and result["levels"] == SINCE["levels"]


def test_continuation_lines(tmp_path):
    sample = tmp_path / "s.log"
    sample.write_text(
        "2026-03-01T10:00:00+02:00 ERROR orders db deadlock code=E2001\\n"
        "Traceback (most recent call last):\\n"
        '  File "/srv/orders/db.py", line 9, in commit\\n'
        "    raise RuntimeError(\\"ERROR req path=/x dur=5ms user=u999\\")\\n"
        "2026-03-01T08:00:01+00:00 INFO orders req method=GET path=/api/orders status=200 dur=12.5ms user=u001\\n"
    )
    result = summarize(str(sample))
    assert result["records"] == 2
    assert result["levels"] == {{"ERROR": 1, "INFO": 1}}
    assert result["users"] == 1
    assert result["p95_ms"] == {{"/api/orders": 12.5}}
'''
    f={'logstats.py':LOGSTATS,'LOGFORMAT.md':LOGFORMAT,'logs/app.log':log,'tests/__init__.py':'','tests/test_logstats.py':tests}
    prompt=('summarize() in logstats.py returns wrong statistics for logs/app.log. Fix logstats.py so it follows LOGFORMAT.md and the acceptance tests pass. '
            'The log is large: do not read it whole, and do not edit or truncate it.')
    return f,{'logstats.py':LOGSTATS_FIXED},prompt

# ---------------------------------------------------------------- F8-H
MONEY='''"""Money helpers. Amounts are in currency units; cents are integers."""
from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount) -> int:
    """Exact conversion of a Decimal, str, int or float amount to integer cents (half-up)."""
    value = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def to_cents_legacy(amount: float) -> int:
    """DEPRECATED: truncates binary floats (2.675 -> 267). Use to_cents()."""
    return int(amount * 100)


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"
'''
H_MODULES={
 'billing/invoices.py':('''from .utils.money import format_cents, to_cents_legacy


def line_cents(quantity: int, unit_price: float) -> int:
    return to_cents_legacy(unit_price) * quantity


def invoice_total_cents(lines: list[tuple[int, float]]) -> int:
    return sum(line_cents(q, p) for q, p in lines)


def invoice_label(lines: list[tuple[int, float]]) -> str:
    return "TOTAL " + format_cents(invoice_total_cents(lines))
''','''from .utils.money import format_cents, to_cents


def line_cents(quantity: int, unit_price: float) -> int:
    return to_cents(unit_price) * quantity


def invoice_total_cents(lines: list[tuple[int, float]]) -> int:
    return sum(line_cents(q, p) for q, p in lines)


def invoice_label(lines: list[tuple[int, float]]) -> str:
    return "TOTAL " + format_cents(invoice_total_cents(lines))
'''),
 'billing/refunds.py':('''from .utils.money import to_cents_legacy as cents


def refund_cents(paid: float, fee: float) -> int:
    """Amount returned to the customer: what was paid minus the processing fee."""
    return cents(paid) - cents(fee)
''','''from .utils.money import to_cents as cents


def refund_cents(paid: float, fee: float) -> int:
    """Amount returned to the customer: what was paid minus the processing fee."""
    return cents(paid) - cents(fee)
'''),
 'billing/subscriptions.py':('''from .utils import money

PLANS = {"basic": 4.99, "team": 19.99, "pro": 2.675 * 10}


def monthly_cents(plan: str, seats: int = 1) -> int:
    return money.to_cents_legacy(PLANS[plan]) * seats
''','''from .utils import money

PLANS = {"basic": 4.99, "team": 19.99, "pro": 2.675 * 10}


def monthly_cents(plan: str, seats: int = 1) -> int:
    return money.to_cents(PLANS[plan]) * seats
'''),
 'billing/discounts.py':('''from .utils.money import to_cents_legacy


def coupon_cents(value: float) -> int:
    return to_cents_legacy(value)
''','''from .utils.money import to_cents


def coupon_cents(value: float) -> int:
    return to_cents(value)
'''),
 'billing/taxes.py':('''from .utils.money import to_cents_legacy


def tax_cents(amount: str, rate: str) -> int:
    """Tax on `amount` at `rate`, both given as decimal strings."""
    return to_cents_legacy(float(amount) * float(rate))
''','''from decimal import Decimal

from .utils.money import to_cents


def tax_cents(amount: str, rate: str) -> int:
    """Tax on `amount` at `rate`, both given as decimal strings."""
    return to_cents(Decimal(amount) * Decimal(rate))
'''),
 'billing/exports/csv_export.py':('''from ..utils import money


def csv_row(reference: str, amount: float) -> str:
    return f"{reference},{money.to_cents_legacy(amount)}"
''','''from ..utils import money


def csv_row(reference: str, amount: float) -> str:
    return f"{reference},{money.to_cents(amount)}"
'''),
 'billing/exports/ledger.py':('''from ..utils.money import to_cents_legacy


def ledger_entries(movements: list[tuple[str, float]]) -> list[tuple[str, int]]:
    return [(account, to_cents_legacy(amount)) for account, amount in movements]
''','''from ..utils.money import to_cents


def ledger_entries(movements: list[tuple[str, float]]) -> list[tuple[str, int]]:
    return [(account, to_cents(amount)) for account, amount in movements]
'''),
 'billing/gateways/card.py':('''from ..utils import money as m


def capture_payload(amount: float, currency: str = "EUR") -> dict:
    return {"amount": m.to_cents_legacy(amount), "currency": currency}
''','''from ..utils import money as m


def capture_payload(amount: float, currency: str = "EUR") -> dict:
    return {"amount": m.to_cents(amount), "currency": currency}
'''),
 'billing/gateways/bank.py':('''from ..utils.money import to_cents_legacy


def transfer_cents(amounts: list[float]) -> int:
    total = 0
    for amount in amounts:
        total += to_cents_legacy(amount)
    return total
''','''from ..utils.money import to_cents


def transfer_cents(amounts: list[float]) -> int:
    total = 0
    for amount in amounts:
        total += to_cents(amount)
    return total
'''),
 'billing/reports/summary.py':('''from ..utils.money import format_cents, to_cents_legacy


def summary_line(label: str, amounts: list[float]) -> str:
    return f"{label}: {format_cents(sum(to_cents_legacy(a) for a in amounts))}"
''','''from ..utils.money import format_cents, to_cents


def summary_line(label: str, amounts: list[float]) -> str:
    return f"{label}: {format_cents(sum(to_cents(a) for a in amounts))}"
'''),
}

def f8h():
    f={'billing/__init__.py':'','billing/utils/__init__.py':'','billing/utils/money.py':MONEY,'billing/exports/__init__.py':'',
       'billing/gateways/__init__.py':'','billing/reports/__init__.py':''}
    ref={'billing/utils/money.py':MONEY.split('\n\ndef to_cents_legacy')[0]+'\n\n\ndef format_cents'+MONEY.split('\n\ndef format_cents')[1]}
    for k,(old,new) in H_MODULES.items():f[k]=old;ref[k]=new
    f['tests/__init__.py']=''
    f['tests/test_money.py']='''import ast
import pathlib

from billing.discounts import coupon_cents
from billing.exports.csv_export import csv_row
from billing.exports.ledger import ledger_entries
from billing.gateways.bank import transfer_cents
from billing.gateways.card import capture_payload
from billing.invoices import invoice_label, invoice_total_cents, line_cents
from billing.refunds import refund_cents
from billing.reports.summary import summary_line
from billing.subscriptions import monthly_cents
from billing.taxes import tax_cents
from billing.utils.money import format_cents, to_cents


def test_to_cents_is_exact():
    assert [to_cents(x) for x in (0.29, 2.675, 1.005, 19.99, "0.125", 7)] == [29, 268, 101, 1999, 13, 700]


def test_invoices():
    assert line_cents(3, 0.29) == 87
    assert invoice_total_cents([(1, 2.675), (2, 19.99)]) == 4266
    assert invoice_label([(1, 1.005)]) == "TOTAL 1.01"


def test_refunds_and_discounts():
    assert refund_cents(19.99, 0.29) == 1970
    assert coupon_cents(2.675) == 268


def test_subscriptions():
    assert monthly_cents("team", 3) == 5997
    assert monthly_cents("pro") == 2675


def test_taxes():
    assert tax_cents("19.99", "0.21") == 420
    assert tax_cents("2.675", "1") == 268


def test_exports_and_gateways():
    assert csv_row("INV-1", 0.29) == "INV-1,29"
    assert ledger_entries([("sales", 19.99), ("fees", 1.005)]) == [("sales", 1999), ("fees", 101)]
    assert capture_payload(2.675) == {"amount": 268, "currency": "EUR"}
    assert transfer_cents([0.29, 0.29, 19.99]) == 2057
    assert summary_line("day", [2.675, 0.29]) == "day: 2.97"
    assert format_cents(-5) == "-0.05"


def test_legacy_helper_is_gone():
    root = pathlib.Path(__file__).resolve().parents[1] / "billing"
    hits = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            name = getattr(node, "id", None) or getattr(node, "attr", None) or getattr(node, "name", None)
            if name == "to_cents_legacy" or (isinstance(node, ast.alias) and node.name == "to_cents_legacy"):
                hits.append(f"{path.name}:{getattr(node, 'lineno', '?')}")
    assert hits == []
'''
    prompt=('billing.utils.money.to_cents_legacy() truncates floats and is deprecated. Replace every use of it in the billing package with to_cents() '
            '(watch for aliases and module-qualified calls), then delete to_cents_legacy. Keep all public function names and signatures.')
    return f,ref,prompt
