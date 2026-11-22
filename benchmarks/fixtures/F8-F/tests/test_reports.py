import hashlib
import sqlite3

import pytest

import migrate
import reports

LEGACY = ["001_customers.sql", "002_orders.sql", "003_payments.sql"]
RELEASED = {'001_customers.sql': '396184168ecc5bf8c96845dbf69e36fd544ac74ed1ee76d6a549f7013f446af6', '002_orders.sql': '70ea3abe567eb41a9ca3819c012aa4137900f1091a15c5cef90599f2dc6ddd97', '003_payments.sql': '1f5a71d1b9d0038e9865edb5732b5b7c34a150e5547a6fd7bd313111a206a025'}
SEED = """
INSERT INTO customers (id, name) VALUES (1, 'Ada');
INSERT INTO customers (id, name) VALUES (2, 'Bruno');
INSERT INTO customers (id, name) VALUES (3, 'Chen');
INSERT INTO customers (id, name) VALUES (4, 'Dalia');
INSERT INTO customers (id, name) VALUES (5, 'Eve');
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (1, 1, '2026-01-15', 12000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (2, 1, '2026-03-02', 5000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (3, 2, '2026-03-20', 9000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (4, 2, '2026-07-01', 7000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (5, 3, '2026-07-31', 15000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (6, 4, '2025-12-31', 99999);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (7, 4, '2026-11-11', 4000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (8, 3, '2026-03-05', 1000);
INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (9, 5, '2026-05-09', 7000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (1, 'charge', 12000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (2, 'charge', 2500);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (2, 'charge', 2500);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (3, 'charge', 9000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (3, 'refund', 9000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (4, 'charge', 3500);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (4, 'charge', 3500);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (5, 'charge', 15000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (6, 'charge', 99999);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (7, 'charge', 4000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (8, 'charge', 1000);
INSERT INTO payments (order_id, kind, amount_cents) VALUES (9, 'charge', 7000);
"""


@pytest.fixture
def db():
    """A production-like database created before migration 004, then upgraded."""
    conn = sqlite3.connect(":memory:")
    for name in LEGACY:
        migrate.apply_file(conn, migrate.MIGRATIONS / name)
    conn.executescript(SEED)
    assert migrate.apply_all(conn) == ["004"]
    return conn


def test_released_migrations_are_unchanged():
    for name, digest in RELEASED.items():
        assert hashlib.sha256((migrate.MIGRATIONS / name).read_bytes()).hexdigest() == digest, f"{name} was already released"


def test_fresh_database_gets_every_migration_once():
    conn = sqlite3.connect(":memory:")
    assert migrate.apply_all(conn) == ["001", "002", "003", "004"]
    assert migrate.applied(conn) == ["001", "002", "003", "004"]
    assert migrate.apply_all(conn) == []


def test_status_is_backfilled(db):
    status = dict(db.execute("SELECT id, status FROM orders"))
    assert status == {1: 'paid', 2: 'paid', 3: 'refunded', 4: 'paid', 5: 'paid', 6: 'paid', 7: 'paid', 8: 'paid', 9: 'paid'}


def test_new_orders_default_to_paid(db):
    db.execute("INSERT INTO orders (id, customer_id, ordered_on, total_cents) VALUES (50, 1, '2026-12-01', 100)")
    assert db.execute("SELECT status FROM orders WHERE id = 50").fetchone() == ("paid",)


def test_status_values_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO orders (id, customer_id, ordered_on, total_cents, status) VALUES (51, 1, '2026-12-01', 100, 'lost')")


def test_monthly_revenue_lists_every_month(db):
    assert reports.monthly_revenue(db, 2026) == [('2026-01', 12000), ('2026-02', 0), ('2026-03', 6000), ('2026-04', 0), ('2026-05', 7000), ('2026-06', 0), ('2026-07', 22000), ('2026-08', 0), ('2026-09', 0), ('2026-10', 0), ('2026-11', 4000), ('2026-12', 0)]


def test_top_customers(db):
    assert reports.top_customers(db, 3) == [('Dalia', 103999), ('Ada', 17000), ('Chen', 16000)]
    assert reports.top_customers(db, 5) == [('Dalia', 103999), ('Ada', 17000), ('Chen', 16000), ('Bruno', 7000), ('Eve', 7000)]
