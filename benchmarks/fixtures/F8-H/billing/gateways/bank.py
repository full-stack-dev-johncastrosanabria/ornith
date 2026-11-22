from ..utils.money import to_cents_legacy


def transfer_cents(amounts: list[float]) -> int:
    total = 0
    for amount in amounts:
        total += to_cents_legacy(amount)
    return total
