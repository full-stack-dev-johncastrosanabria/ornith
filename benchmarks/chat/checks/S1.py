import sqlite3
db=sqlite3.connect(':memory:')
db.executescript('''
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), created_at TEXT NOT NULL, total REAL NOT NULL, status TEXT NOT NULL);
INSERT INTO customers VALUES (1,'Ana','ES'),(2,'Luis','ES'),(3,'Marta','MX'),(4,'Pedro','MX'),(5,'Sofía','CO'),(6,'Juan','CO'),(7,'Eva','AR'),(8,'Leo','PE');
INSERT INTO orders VALUES
 (1,1,'2025-01-10',60.0,'paid'),(2,1,'2025-03-05',40.5,'pending'),(3,2,'2025-06-01',30.0,'cancelled'),(4,2,'2024-12-31',500.0,'paid'),
 (5,3,'2025-02-02',80.0,'paid'),(6,4,'2025-11-11',70.25,'paid'),(7,5,'2025-07-07',100.0,'paid'),(8,6,'2026-01-01',300.0,'paid'),
 (9,7,'2025-05-05',150.25,'paid'),(10,8,'2025-08-08',999.0,'cancelled'),(11,7,'2025-12-31',0.0,'cancelled'),(12,1,'2025-12-31',10.0,'paid'),
 (13,2,'2025-09-09',5.0,'paid');
''')
cur=db.execute(open('query.sql').read().strip().rstrip(';'))
names=[d[0].lower() for d in cur.description];rows=cur.fetchall()
assert names==['country','customers','revenue'],names
want=[('AR',1,150.25),('MX',2,150.25),('ES',2,115.5)]
assert len(rows)==len(want) and all(r[0]==w[0] and r[1]==w[1] and abs(r[2]-w[2])<.005 for r,w in zip(rows,want)),rows
print('OK')
