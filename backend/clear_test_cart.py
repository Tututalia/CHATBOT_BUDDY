"""
Clear test cart for CUST001
"""
import sqlite3

conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()

cursor.execute("DELETE FROM cart WHERE customer_id = 'CUST001'")
conn.commit()

print("✅ Test cart cleared for CUST001")
print(f"   Deleted {cursor.rowcount} items")

conn.close()
