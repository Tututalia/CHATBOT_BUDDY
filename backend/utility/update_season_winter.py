import sqlite3
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "retail_agent.db")

conn = sqlite3.connect(db_path)

# Show current season values for Jacket/Hoodie categories before update
cur = conn.execute(
    "SELECT product_id, product_name, category, season FROM products "
    "WHERE LOWER(category) IN ('jacket', 'jackets', 'hoodie', 'hoodies')"
)
rows = cur.fetchall()
print(
    f"Found {len(rows)} products with category Jacket/Jackets/Hoodie/Hoodies:\n")
for r in rows:
    print(f"  {r[0]} | {r[1]} | category={r[2]} | season={r[3]}")

# Update season to 'Winter' for matching categories
result = conn.execute(
    "UPDATE products SET season = 'Winter' "
    "WHERE LOWER(category) IN ('jacket', 'jackets', 'hoodie', 'hoodies')"
)
conn.commit()
print(f"\nUpdated {result.rowcount} row(s) → season = 'Winter'")

# Verify
cur2 = conn.execute(
    "SELECT product_id, product_name, category, season FROM products "
    "WHERE LOWER(category) IN ('jacket', 'jackets', 'hoodie', 'hoodies')"
)
print("\nAfter update:")
for r in cur2.fetchall():
    print(f"  {r[0]} | {r[1]} | category={r[2]} | season={r[3]}")

print("\nDone!")
conn.close()
