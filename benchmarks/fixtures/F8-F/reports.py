"""Sales reports. Amounts are integer cents."""


def monthly_revenue(conn, year):
    """Revenue of every month of `year`: twelve ("YYYY-MM", cents) pairs in calendar order, 0 for months without sales."""
    rows = conn.execute(
        "SELECT strftime('%Y-%m', ordered_on) AS month, SUM(total_cents) FROM orders "
        "WHERE strftime('%Y', ordered_on) = ? GROUP BY month ORDER BY month",
        (str(year),),
    ).fetchall()
    return [(month, total) for month, total in rows]


def top_customers(conn, limit=3):
    """Customers by total amount ordered (all time), highest first, ties by name: [(name, cents)]."""
    return conn.execute(
        "SELECT c.name, SUM(o.total_cents) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id "
        "JOIN payments p ON p.order_id = o.id "
        "GROUP BY c.id ORDER BY total DESC, c.name LIMIT ?",
        (limit,),
    ).fetchall()
