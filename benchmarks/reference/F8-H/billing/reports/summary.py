from ..utils.money import format_cents, to_cents


def summary_line(label: str, amounts: list[float]) -> str:
    return f"{label}: {format_cents(sum(to_cents(a) for a in amounts))}"
