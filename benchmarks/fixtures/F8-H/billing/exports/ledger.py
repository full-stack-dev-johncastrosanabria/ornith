from ..utils.money import to_cents_legacy


def ledger_entries(movements: list[tuple[str, float]]) -> list[tuple[str, int]]:
    return [(account, to_cents_legacy(amount)) for account, amount in movements]
