from dataclasses import dataclass, field
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
        return sum(i.quantity for i in self.items)
