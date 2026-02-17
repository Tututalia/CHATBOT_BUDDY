import sqlite3
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "retail_agent.db")

conn = sqlite3.connect(db_path)

# Count rows with "Rs. " prefix
cur = conn.execute("SELECT COUNT(*) FROM products WHERE price LIKE 'Rs.%'")
count = cur.fetchone()[0]
print(f"Rows with 'Rs. ' prefix: {count}")

# Remove "Rs. " prefix
conn.execute(
    "UPDATE products SET price = REPLACE(price, 'Rs. ', '') WHERE price LIKE 'Rs.%'")
conn.commit()

# Verify
cur2 = conn.execute("SELECT product_id, price FROM products LIMIT 5")
print("\nSample prices after update:")
for r in cur2.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\nPrice update complete!")
conn.close()
