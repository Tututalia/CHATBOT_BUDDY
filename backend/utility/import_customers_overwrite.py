"""
Import customer_data.csv into the customers table, overwriting all existing data.
"""
import csv
from sqlmodel import Session, create_engine
from models import Customer
import os

# Path to your SQLite database file
db_path = os.path.join(os.path.dirname(__file__), "retail_agent.db")
engine = create_engine(f"sqlite:///{db_path}")

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customer_data.csv")


def import_customers_overwrite():
    print("\n>> Importing customers (overwrite mode)...")
    from sqlalchemy import text
    with Session(engine) as session:
        # Delete all existing data
        session.exec(text("DELETE FROM customers"))
        session.commit()
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Handle empty or invalid loyalty_points
                try:
                    loyalty_points = int(
                        row['loyalty_points']) if row['loyalty_points'].strip() != '' else 0
                except Exception:
                    loyalty_points = 0
                customer = Customer(
                    customer_id=row['customer_id'],
                    customer_name=row['customer_name'],
                    gender=row['gender'],
                    phone=row['phone'],
                    address=row['address'],
                    loyalty_points=loyalty_points,
                    order_history=row.get('order_history'),
                    order_dates=row.get('order_dates'),
                    pending_orders=row.get('pending_orders'),
                    role_id=int(row['role_id']) if row.get(
                        'role_id') and row['role_id'].strip() != '' else None
                )
                session.add(customer)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} customers (overwritten)")


if __name__ == "__main__":
    import_customers_overwrite()
