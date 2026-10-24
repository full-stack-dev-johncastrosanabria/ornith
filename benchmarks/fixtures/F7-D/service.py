from calculator import total
def invoice(amount, kind):
    return {'kind': kind, 'total': total(amount, kind)}
