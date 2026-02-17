"""
Drop and recreate the customers table with the new schema (including role_id).
"""
from sqlmodel import SQLModel, create_engine
from models import Customer
import os

# Path to your SQLite database file
db_path = os.path.join(os.path.dirname(__file__), "retail_agent.db")
engine = create_engine(f"sqlite:///{db_path}")


def drop_and_recreate_customers_table():
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS customers"))
        conn.commit()
    SQLModel.metadata.create_all(engine, tables=[Customer.__table__])
    print("[OK] Dropped and recreated customers table with role_id column.")


if __name__ == "__main__":
    print("\n=== Dropping and recreating customers table ===")
    drop_and_recreate_customers_table()
    print("[DONE] Customers table is ready. Now run your import script.")
