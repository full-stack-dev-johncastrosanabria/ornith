UPDATE orders SET status = 'refunded' WHERE id IN (SELECT order_id FROM payments WHERE kind = 'refund');
