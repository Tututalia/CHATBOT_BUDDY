import sqlite3

# Get customer IDs from retail_agent.db
retail_conn = sqlite3.connect('retail_agent.db')
retail_cursor = retail_conn.cursor()

retail_cursor.execute("""
    SELECT customer_id 
    FROM customers 
    WHERE customer_id BETWEEN 'CUST001' AND 'CUST102' 
    ORDER BY customer_id
""")

customer_ids = retail_cursor.fetchall()
retail_conn.close()

# Insert into payload table in chat_history.db
chat_conn = sqlite3.connect('chat_history.db')
chat_cursor = chat_conn.cursor()

for (customer_id,) in customer_ids:
    chat_cursor.execute(
        "INSERT INTO payload (customer_id, payload) VALUES (?, NULL)", (customer_id,))

chat_conn.commit()
print(f'✅ Inserted {len(customer_ids)} customer IDs into payload table')
chat_conn.close()
