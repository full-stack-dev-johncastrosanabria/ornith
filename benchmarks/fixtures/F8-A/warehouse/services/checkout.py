from ..config.customers import CUSTOMERS
from ..config.loader import load
from ..pricing.engine import price


def checkout_total(order):
    """Final amount charged for `order`, using its customer's configuration."""
    return price(order, load(CUSTOMERS.get(order.customer_id, {})))
