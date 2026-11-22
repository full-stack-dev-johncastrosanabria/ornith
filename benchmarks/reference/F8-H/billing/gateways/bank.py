from ..utils.money import to_cents


def transfer_cents(amounts: list[float]) -> int:
    total = 0
    for amount in amounts:
        total += to_cents(amount)
    return total
