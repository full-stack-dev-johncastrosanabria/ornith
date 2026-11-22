ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('paid', 'refunded'));
UPDATE orders SET status = 'refunded' WHERE id IN (SELECT order_id FROM payments WHERE kind = 'refund');
