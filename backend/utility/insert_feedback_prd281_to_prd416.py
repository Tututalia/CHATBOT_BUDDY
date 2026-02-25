"""Insert product_ids PRD281–PRD416 into the feedback table with random reviews.

Each product_id gets a random float review in [3.01, 5.00].
Existing rows are updated (upsert) so the script is safe to re-run.
"""

from __future__ import annotations

import random
import sqlite3
import os


def main() -> None:
    db_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "..", "retail_agent.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")

        # Ensure the feedback table exists
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                product_id TEXT PRIMARY KEY,
                review REAL NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
            """
        )

        upsert_sql = (
            "INSERT INTO feedback(product_id, review) VALUES(?, ?) "
            "ON CONFLICT(product_id) DO UPDATE SET review=excluded.review"
        )

        rows = []
        for i in range(281, 417):  # PRD281 to PRD416 inclusive
            product_id = f"PRD{i}"
            review = round(random.uniform(3.01, 5.00), 2)
            rows.append((product_id, review))

        conn.executemany(upsert_sql, rows)
        conn.commit()

        inserted_count = len(rows)
        total_count = conn.execute(
            "SELECT COUNT(*) FROM feedback").fetchone()[0]

        print(f"✅ Inserted/updated {inserted_count} rows (PRD281 – PRD416).")
        print(f"   Total rows in feedback table: {total_count}")

        # Show a few sample rows
        sample = conn.execute(
            "SELECT product_id, review FROM feedback "
            "WHERE CAST(SUBSTR(product_id, 4) AS INTEGER) BETWEEN 281 AND 416 "
            "ORDER BY CAST(SUBSTR(product_id, 4) AS INTEGER) "
            "LIMIT 10"
        ).fetchall()
        print("\n   Sample rows:")
        for pid, rev in sample:
            print(f"     {pid}  →  {rev}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
