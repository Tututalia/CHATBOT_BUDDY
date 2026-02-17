"""
Import CSV data into the SQLite database
"""
import csv
from sqlmodel import Session
from database import engine, init_db
from models import Customer, Product, Store, OrderHistory, StoreKeeperTransaction, AdminDashboardData


def import_customers():
    """Import customer data from CSV"""
    print("\n>> Importing customers...")
    with Session(engine) as session:
        with open('data/customer_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                customer = Customer(
                    customer_id=row['customer_id'],
                    customer_name=row['customer_name'],
                    gender=row['gender'],
                    phone=row['phone'],
                    address=row['address'],
                    loyalty_points=int(row['loyalty_points']),
                    order_history=row.get('order_history'),
                    order_dates=row.get('order_dates'),
                    pending_orders=row.get('pending_orders')
                )
                session.add(customer)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} customers")


def import_products():
    """Import product data from CSV"""
    print("\n>> Importing products...")
    with Session(engine) as session:
        with open('data/product_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            seen_products = set()
            for row in reader:
                product_id = row['product_id']
                # Skip duplicates (like PRD040 that appears twice)
                if product_id in seen_products:
                    continue
                seen_products.add(product_id)

                product = Product(
                    product_id=product_id,
                    product_name=row['product_name'],
                    category=row['category'],
                    gender=row['gender'],
                    price=float(row['price']),
                    online_available=row['online_available'],
                    offline_available=row['offline_available'],
                    offline_stores=row.get('offline_stores'),
                    store_ids=row.get('store_ids'),
                    festival=row.get('festival'),
                    season=row['season'],
                    image_reference=row['image_reference'],
                    loyalty_points=int(row['loyalty_points'])
                )
                session.add(product)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} products")


def import_stores():
    """Import store data from CSV"""
    print("\n>> Importing stores...")
    with Session(engine) as session:
        with open('data/outlate_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                store = Store(
                    store_id=row['store_id'],
                    store_name=row['store_name'],
                    address=row['address'],
                    manager_name=row['manager_name'],
                    store_phone=row['store_phone']
                )
                session.add(store)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} stores")


def import_order_history():
    """Import order history from CSV"""
    print("\n>> Importing order history...")
    with Session(engine) as session:
        with open('data/order_history.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Generate unique transaction ID by appending row count
                unique_txn_id = f"{row['transaction_id']}-{count:04d}"

                order = OrderHistory(
                    transaction_id=unique_txn_id,
                    customer_id=row['customer_id'],
                    customer_name=row['customer_name'],
                    product_id=row['product_id'],
                    product_name=row['product_name'],
                    quantity=int(row['quantity']),
                    order_dates=row['order_dates'],
                    loyalty_points=int(row['loyalty_points'])
                )
                session.add(order)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} order history records")


def import_store_keeper_transactions():
    """Import store keeper transactions from CSV"""
    print("\n>> Importing store keeper transactions...")
    with Session(engine) as session:
        with open('data/store keeper transaction data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                transaction = StoreKeeperTransaction(
                    id=int(row['ID']),
                    customer_id=row['customer_id'],
                    product_id=row['product_id'],
                    date=row['Date'],
                    user_name=row['User Name'],
                    product=row['Product'],
                    qty=int(row['Qty']),
                    mode=row['Mode'],
                    # This now references stores.store_id
                    store_name=row['Store Name'],
                    store_id=None,
                    status=row['Status'],
                    amount=float(row['Amount']),
                    address=row['Address'],
                    phone=row['Phone']
                )
                session.add(transaction)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} store keeper transactions")


def import_admin_dashboard():
    """Import admin dashboard data from CSV"""
    print("\n>> Importing admin dashboard data...")
    with Session(engine) as session:
        with open('data/admin_dashboard_data.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                data = AdminDashboardData(
                    id=int(row['ID']),
                    date=row['Date'],
                    user_name=row['User Name'],
                    product=row['Product'],
                    qty=int(row['Qty']),
                    mode=row['Mode'],
                    store_name=row['Store Name'],
                    status=row['Status'],
                    amount=float(row['Amount']),
                    address=row['Address'],
                    phone=row['Phone']
                )
                session.add(data)
                count += 1
            session.commit()
    print(f"[OK] Imported {count} admin dashboard records")


if __name__ == "__main__":
    print("="*60)
    print("IMPORTING CSV DATA INTO DATABASE")
    print("="*60)

    # Initialize database and create tables first
    print("\n>> Creating database tables...")
    init_db()
    print("[OK] Database tables created\n")

    try:
        # Import in order (respecting foreign key relationships)
        import_customers()
        import_products()
        import_stores()
        import_order_history()
        import_store_keeper_transactions()
        import_admin_dashboard()

        print("\n" + "="*60)
        print("[SUCCESS] ALL DATA IMPORTED SUCCESSFULLY!")
        print("="*60)
        print("\nRefresh your SQLite viewer to see the data.")

    except Exception as e:
        print(f"\n[ERROR] Error during import: {e}")
        import traceback
        traceback.print_exc()
