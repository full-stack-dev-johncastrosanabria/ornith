Add migration db/migrations/004_order_status.sql: orders get a status column, either paid or refunded (enforced by the database, default paid); existing orders that have a refund payment become refunded. Refunded orders must not count in reports.py. The reports are also wrong today: monthly_revenue omits months and top_customers overstates some customers. Existing databases are upgraded with migrate.apply_all; never edit migrations that were already released.

Run: /Users/johnbenjamincastrosanabria/Developer/ornith/benchmarks/.venv/bin/python -m pytest -q -p no:cacheprovider
Do not modify tests or project dependency files.
