import sqlite3
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "retail_agent.db")

conn = sqlite3.connect(db_path)

# Show current value
cur = conn.execute(
    "SELECT product_id, product_name, category FROM products WHERE product_id = 'PRD037'")
row = cur.fetchone()
if row:
    print(f"Before: {row[0]} | {row[1]} | category = {row[2]}")
else:
    print("Product PRD037 not found!")
    conn.close()
    exit()

# Update category to Jackets
conn.execute(
    "UPDATE products SET category = 'Jackets' WHERE product_id = 'PRD037'")
conn.commit()

# Verify
cur2 = conn.execute(
    "SELECT product_id, product_name, category FROM products WHERE product_id = 'PRD037'")
row2 = cur2.fetchone()
print(f"After:  {row2[0]} | {row2[1]} | category = {row2[2]}")

print("\nCategory update complete!")
conn.close()
