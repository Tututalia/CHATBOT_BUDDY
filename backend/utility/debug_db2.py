import sqlite3

# Check retail_agent.db
print("=== retail_agent.db ===")
conn = sqlite3.connect('retail_agent.db')
cur = conn.cursor()

# Check cart table schema
print("\n=== cart table schema ===")
cur.execute("PRAGMA table_info(cart)")
columns = cur.fetchall()
for col in columns:
    print(col)

# Check ALL cart entries
print("\n=== ALL cart entries ===")
cur.execute("SELECT * FROM cart")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print("Cart table is EMPTY")

# Check CUST003 specifically
print("\n=== CUST003 cart entries ===")
cur.execute("SELECT * FROM cart WHERE customer_id = ?", ('CUST003',))
rows = cur.fetchall()
print(rows if rows else 'No items found')

# Check order_history for recent CART entries
print("\n=== Recent CART entries in order_history ===")
cur.execute("SELECT * FROM order_history WHERE transaction_id LIKE 'CART%' ORDER BY order_dates DESC LIMIT 10")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()
