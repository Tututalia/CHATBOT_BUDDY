import sqlite3
import os
import sys
import uuid
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE, "retail_agent.db")

if not os.path.exists(DB_PATH):
    print(f"Database not found: {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Turn foreign keys off during migration to allow copying any legacy rows,
# we'll enable enforcement at the end so the DB enforces FKs going forward.
cur.execute('PRAGMA foreign_keys = OFF')

# Check if cart table exists
tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if 'cart' not in tables:
    print('No cart table found, nothing to migrate.')
    conn.close()
    sys.exit(0)

print('Existing cart columns:')
for r in cur.execute("PRAGMA table_info(cart)").fetchall():
    print(r)

# Create new table cart_new with desired schema
print('\nCreating new table `cart_new` (with FK constraints)...')
cur.execute('''
CREATE TABLE IF NOT EXISTS cart_new (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    product_id TEXT,
    store_id TEXT,
    channel TEXT,
    status TEXT,
    created_at TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY(store_id) REFERENCES stores(store_id) ON DELETE SET NULL ON UPDATE CASCADE
)
''')

# Copy existing rows into new table, generating order_id if missing and filling defaults
rows = cur.execute('SELECT * FROM cart').fetchall()
cols = [r[1] for r in cur.execute('PRAGMA table_info(cart)').fetchall()]
print(f'Found {len(rows)} existing cart rows; columns: {cols}')

for row in rows:
    rowdict = dict(zip(cols, row))
    # Try to preserve customer_id and product_id if present
    customer_id = rowdict.get('customer_id')
    product_id = rowdict.get('product_id')
    # Generate order_id using uuid4
    order_id = rowdict.get('order_id') or (
        'ORD-' + str(uuid.uuid4())) if 'order_id' in rowdict else ('ORD-' + str(uuid.uuid4()))
    store_id = rowdict.get('store_id') if 'store_id' in rowdict else None
    channel = rowdict.get('channel') if 'channel' in rowdict else 'online'
    status = rowdict.get('status') if 'status' in rowdict else 'pending'
    created_at = rowdict.get(
        'created_at') if 'created_at' in rowdict else datetime.utcnow().isoformat()

    cur.execute('INSERT OR REPLACE INTO cart_new (order_id, customer_id, product_id, store_id, channel, status, created_at) VALUES (?,?,?,?,?,?,?)',
                (order_id, customer_id, product_id, store_id, channel, status, created_at))

conn.commit()

# Drop old table and rename
print('Dropping old `cart` table and renaming `cart_new` -> `cart`...')
cur.execute('DROP TABLE cart')
cur.execute('ALTER TABLE cart_new RENAME TO cart')
conn.commit()

print('Migration complete. New cart schema:')
for r in cur.execute("PRAGMA table_info(cart)").fetchall():
    print(r)

# Show some rows
print('\nSample rows:')
for r in cur.execute('SELECT order_id, customer_id, product_id, store_id, channel, status, created_at FROM cart LIMIT 10').fetchall():
    print(r)

# Ensure future connections enforce foreign keys by setting the pragma
cur.execute('PRAGMA foreign_keys = ON')
conn.close()
