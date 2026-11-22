from ..utils import money as m


def capture_payload(amount: float, currency: str = "EUR") -> dict:
    return {"amount": m.to_cents_legacy(amount), "currency": currency}
