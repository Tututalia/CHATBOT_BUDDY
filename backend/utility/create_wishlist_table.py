"""Utility script: Create the `wishlist` table in retail_agent.db.

Columns:
  - id              (INTEGER, auto-increment primary key)
  - customer_id     (TEXT, FK → customers.customer_id)
  - product_id      (TEXT, FK → products.product_id)
"""

from sqlalchemy import create_engine, text, inspect
from database import DATABASE_URL
import sys
from pathlib import Path

# Ensure the backend package is on sys.path so we can import `database`.
# MUST come before importing from the backend package.
sys.path.append(str(Path(__file__).resolve().parent.parent))


TABLE = "wishlist"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS wishlist (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  TEXT NOT NULL,
    product_id   TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);
"""


def create_wishlist_table() -> None:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        conn.exec_driver_sql(CREATE_SQL)

    # Verify
    insp = inspect(engine)
    if TABLE in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns(TABLE)]
        print(f"✅ Table '{TABLE}' exists with columns: {cols}")
    else:
        print(f"❌ Table '{TABLE}' was NOT created.")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("CREATE WISHLIST TABLE")
    print("=" * 50 + "\n")
    try:
        create_wishlist_table()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
