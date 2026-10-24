from rates import DISCOUNTS, TAX_RATE
def total(amount, kind):
    discounted = amount * (1-DISCOUNTS[kind])
    return round(discounted + amount * TAX_RATE, 2)
