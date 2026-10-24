def quote(kind, amount):
    if kind == 'regular':
        return round(amount * 1.2, 2)
    if kind == 'member':
        return round(amount * 0.9 * 1.2, 2)
    if kind == 'staff':
        return round(amount * 0.8 * 1.2, 2)
    raise ValueError('unknown kind')
