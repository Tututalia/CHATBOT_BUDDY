"""Create and populate the `feedback` table in retail_agent.db.

Requirements:
- Table name: feedback
- Columns: product_id, review
- Populate feedback.product_id from products.product_id
- Generate one random float review in [2.0, 5.0] for each product_id

This script is idempotent:
- Creates the table if it doesn't exist
- Upserts rows for every product_id
"""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path


def main() -> None:
    backend_dir = Path(__file__).resolve().parent
    db_path = backend_dir / "retail_agent.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys=ON")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                product_id TEXT PRIMARY KEY,
                review REAL NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
            """
        )

        product_ids = [
            row[0]
            for row in conn.execute("SELECT product_id FROM products").fetchall()
        ]

        if not product_ids:
            print("No products found in products table; nothing to populate.")
            return

        # Upsert one review per product_id
        upsert_sql = (
            "INSERT INTO feedback(product_id, review) VALUES(?, ?) "
            "ON CONFLICT(product_id) DO UPDATE SET review=excluded.review"
        )

        rows = []
        for product_id in product_ids:
            review = round(random.uniform(2.0, 5.0), 2)
            rows.append((product_id, review))

        conn.executemany(upsert_sql, rows)
        conn.commit()

        feedback_count = conn.execute(
            "SELECT COUNT(*) FROM feedback").fetchone()[0]
        print(f"✅ feedback table ready. Rows in feedback: {feedback_count}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
