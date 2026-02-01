"""Check cart table data"""
from database import get_db_session
from crud import cart_crud
import sqlite3

# Method 1: Using CRUD
print("="*60)
print("CART DATA (via CRUD)")
print("="*60)
with get_db_session() as session:
    items = cart_crud.get_all(session, limit=20)
    if not items:
        print("No cart items found")
    else:
        for i in items:
            qty = getattr(i, 'quantity', 'NO ATTR')
            print(f"Order: {i.order_id}")
            print(f"  Product: {i.product_id}")
            print(f"  Customer: {i.customer_id}")
            print(f"  Quantity: {qty}")
            print(f"  Status: {i.status}")
            print()

# Method 2: Direct SQL
print("="*60)
print("CART DATA (via Direct SQL)")
print("="*60)
conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()
cursor.execute(
    "SELECT order_id, customer_id, product_id, quantity, status FROM cart LIMIT 20")
rows = cursor.fetchall()
if not rows:
    print("No cart items found")
else:
    for row in rows:
        print(f"Order: {row[0]}")
        print(f"  Customer: {row[1]}")
        print(f"  Product: {row[2]}")
        print(f"  Quantity: {row[3]}")
        print(f"  Status: {row[4]}")
        print()
conn.close()

# Check table schema
print("="*60)
print("CART TABLE SCHEMA")
print("="*60)
conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(cart)")
schema = cursor.fetchall()
for col in schema:
    print(f"Column: {col[1]}, Type: {col[2]}, Default: {col[4]}")
conn.close()
