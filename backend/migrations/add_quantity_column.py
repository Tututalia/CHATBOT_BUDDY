import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "retail_agent.db")
DB_PATH = os.path.abspath(DB_PATH)

if not os.path.exists(DB_PATH):
    print(f"Database not found: {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cols = [r[1] for r in cur.execute("PRAGMA table_info(products)").fetchall()]
if 'quantity' in cols:
    print('quantity column already exists — nothing to do')
    conn.close()
    sys.exit(0)

print('Adding column `quantity` to products table...')
cur.execute("ALTER TABLE products ADD COLUMN quantity INTEGER DEFAULT 0")
conn.commit()
cols2 = [r[1] for r in cur.execute("PRAGMA table_info(products)").fetchall()]
print('Done. Columns now:', cols2)
conn.close()
