from .utils.money import to_cents_legacy as cents


def refund_cents(paid: float, fee: float) -> int:
    """Amount returned to the customer: what was paid minus the processing fee."""
    return cents(paid) - cents(fee)
