from ..utils.money import format_cents, to_cents_legacy


def summary_line(label: str, amounts: list[float]) -> str:
    return f"{label}: {format_cents(sum(to_cents_legacy(a) for a in amounts))}"
