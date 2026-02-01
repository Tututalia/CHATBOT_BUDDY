"""
Recreate the customers table to include the new role_id column, preserving existing data if possible.
"""
from sqlmodel import SQLModel, create_engine, Session
from models import Customer
import os
import csv

# Path to your SQLite database file
db_path = os.path.join(os.path.dirname(__file__), "retail_agent.db")
engine = create_engine(f"sqlite:///{db_path}")

BACKUP_CSV = os.path.join(os.path.dirname(
    __file__), "data", "customers_backup_temp.csv")

# 1. Backup current customers data to a temp CSV


def backup_customers():
    from sqlalchemy import text
    with Session(engine) as session:
        try:
            # Use raw SQL to handle missing columns gracefully
            result = session.exec(text("SELECT * FROM customers")).all()
            if not result:
                print("[INFO] No customers to backup.")
                return
            
            # Get column names from the first row
            columns = result[0]._mapping.keys() if result else []
            
            with open(BACKUP_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in result:
                    writer.writerow([row._mapping.get(col) for col in columns])
            print(f"[OK] Backed up {len(result)} customers to {BACKUP_CSV}")
        except Exception as e:
            print(f"[INFO] Could not backup existing data: {e}")

# 2. Drop and recreate the customers table


def recreate_customers_table():
    from sqlalchemy import text
    with Session(engine) as session:
        session.exec(text("DROP TABLE IF EXISTS customers"))
        session.commit()
    SQLModel.metadata.create_all(engine, tables=[Customer.__table__])
    print("[OK] Recreated customers table with role_id column.")

# 3. Restore data from backup CSV (if any)


def restore_customers():
    if not os.path.exists(BACKUP_CSV):
        print("[INFO] No backup found, skipping restore.")
        return
    with Session(engine) as session:
        with open(BACKUP_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    loyalty_points = int(
                        row['loyalty_points']) if row['loyalty_points'].strip() != '' else 0
                except Exception:
                    loyalty_points = 0
                role_id = int(row['role_id']) if row.get(
                    'role_id') and row['role_id'].strip() != '' else None
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
                    role_id=role_id
                )
                session.add(customer)
                count += 1
            session.commit()
    print(f"[OK] Restored {count} customers from backup.")
    os.remove(BACKUP_CSV)


if __name__ == "__main__":
    print("\n=== Recreating customers table with role_id column ===")
    backup_customers()
    recreate_customers_table()
    restore_customers()
    print("[DONE] Customers table recreated and data restored.")
