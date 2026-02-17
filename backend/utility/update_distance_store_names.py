"""
Script to update store_name in the distance table
by looking up the store_id in the stores table.
"""

import sqlite3
import os

# Resolve the path to the database (same level as the backend folder)
DB_PATH = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "retail_agent.db")


def update_store_names():
    """
    For each row in the distance table, look up the store_id in the stores table
    and update the store_name column with the matching value.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Preview current state
    cur.execute(
        "SELECT COUNT(*) FROM distance"
    )
    total_rows = cur.fetchone()[0]
    print(f"Total rows in distance table: {total_rows}")

    # Perform the update using a correlated subquery
    update_sql = """
        UPDATE distance
        SET store_name = (
            SELECT s.store_name
            FROM stores s
            WHERE s.store_id = distance.store_id
        )
        WHERE EXISTS (
            SELECT 1
            FROM stores s
            WHERE s.store_id = distance.store_id
        )
    """
    cur.execute(update_sql)
    updated = cur.rowcount
    conn.commit()

    print(f"✓ Updated store_name for {updated} rows in the distance table.")

    # Report any rows with store_id not found in the stores table
    cur.execute(
        """
        SELECT DISTINCT store_id FROM distance
        WHERE store_id NOT IN (SELECT store_id FROM stores)
        """
    )
    missing = cur.fetchall()
    if missing:
        print(f"⚠ {len(missing)} store_id(s) in distance not found in stores table:")
        for row in missing:
            print(f"   - {row[0]}")
    else:
        print("✓ All store_ids in distance matched a store in the stores table.")

    # Show a sample of updated rows
    print("\nSample updated rows:")
    cur.execute("SELECT store_id, store_name FROM distance LIMIT 10")
    for row in cur.fetchall():
        print(f"  store_id={row[0]}  →  store_name={row[1]}")

    conn.close()


if __name__ == "__main__":
    update_store_names()
