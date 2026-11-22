from .utils import money

PLANS = {"basic": 4.99, "team": 19.99, "pro": 2.675 * 10}


def monthly_cents(plan: str, seats: int = 1) -> int:
    return money.to_cents(PLANS[plan]) * seats
