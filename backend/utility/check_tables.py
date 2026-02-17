import sqlite3

# Check retail_agent.db
conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
conn.close()

print("Tables in retail_agent.db:")
for table in tables:
    print(f"  - {table[0]}")
