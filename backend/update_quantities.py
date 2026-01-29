import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), "retail_agent.db")
DB = os.path.abspath(DB)
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Product IDs to set to zero as requested
targets = ['PRD001', 'PRD004', 'PRD005']
placeholders = ','.join(['?']*len(targets))
sql = f"UPDATE products SET quantity = 0 WHERE product_id IN ({placeholders})"
cur.execute(sql, targets)
conn.commit()
print(f"Updated rows for product_ids: {targets}")
print('\nSample rows after update:')
for r in cur.execute("SELECT product_id, product_name, quantity FROM products WHERE product_id IN ('PRD001','PRD004','PRD005') ORDER BY product_id").fetchall():
    print(r)
conn.close()
