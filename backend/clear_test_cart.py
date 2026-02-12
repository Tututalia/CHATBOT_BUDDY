import sqlite3



DB_PATH = "retail_agent.db"  # change if needed

tables = ["cart", "order_history", "store_keeper_transactions"]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

for table in tables:
    cur.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cur.fetchone():
        continue

    cols = [r[1]
            for r in cur.execute(f"PRAGMA table_info('{table}')").fetchall()]
    if "size" not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN size TEXT;")

conn.commit()
conn.close()
print("Done.")