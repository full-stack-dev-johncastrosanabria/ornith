from .utils.money import format_cents, to_cents


def line_cents(quantity: int, unit_price: float) -> int:
    return to_cents(unit_price) * quantity


def invoice_total_cents(lines: list[tuple[int, float]]) -> int:
    return sum(line_cents(q, p) for q, p in lines)


def invoice_label(lines: list[tuple[int, float]]) -> str:
    return "TOTAL " + format_cents(invoice_total_cents(lines))
