from ..utils.money import to_cents


def ledger_entries(movements: list[tuple[str, float]]) -> list[tuple[str, int]]:
    return [(account, to_cents(amount)) for account, amount in movements]
