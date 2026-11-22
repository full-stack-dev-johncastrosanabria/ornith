"""Sales reports. Amounts are integer cents."""


def monthly_revenue(conn, year):
    """Revenue of every month of `year`: twelve ("YYYY-MM", cents) pairs in calendar order, 0 for months without sales."""
    totals = dict(conn.execute(
        "SELECT strftime('%Y-%m', ordered_on), SUM(total_cents) FROM orders "
        "WHERE strftime('%Y', ordered_on) = ? AND status = 'paid' GROUP BY 1",
        (str(year),),
    ).fetchall())
    return [(f"{year}-{m:02d}", totals.get(f"{year}-{m:02d}", 0)) for m in range(1, 13)]


def top_customers(conn, limit=3):
    """Customers by total amount ordered (all time), highest first, ties by name: [(name, cents)]."""
    return conn.execute(
        "SELECT c.name, SUM(o.total_cents) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' "
        "GROUP BY c.id ORDER BY total DESC, c.name LIMIT ?",
        (limit,),
    ).fetchall()
