CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    ordered_on TEXT NOT NULL, -- YYYY-MM-DD
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    status TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid', 'refunded'))
);
CREATE INDEX orders_by_date ON orders(ordered_on);
