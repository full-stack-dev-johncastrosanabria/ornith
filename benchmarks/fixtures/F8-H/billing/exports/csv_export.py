from ..utils import money


def csv_row(reference: str, amount: float) -> str:
    return f"{reference},{money.to_cents_legacy(amount)}"
