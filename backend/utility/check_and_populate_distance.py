"""
Check existing data and populate distance table
"""

import random
from sqlalchemy import text
from database import engine


def check_data():
    """Check if customers and stores have data"""
    with engine.connect() as conn:
        # Check customers
        customers = conn.execute(
            text("SELECT COUNT(*) FROM customers")).scalar()
        print(f"Customers in database: {customers}")

        # Check stores
        stores = conn.execute(text("SELECT COUNT(*) FROM stores")).scalar()
        print(f"Stores in database: {stores}")

        # Check distance table
        try:
            distance = conn.execute(
                text("SELECT COUNT(*) FROM distance")).scalar()
            print(f"Distance records in database: {distance}")
        except:
            print("Distance table doesn't exist yet")

        return customers, stores


def drop_and_recreate_distance():
    """Drop and recreate the distance table"""
    with engine.connect() as conn:
        # Drop existing table
        conn.execute(text("DROP TABLE IF EXISTS distance"))
        conn.commit()
        print("✓ Dropped existing distance table")

        # Create new table
        create_table_sql = """
        CREATE TABLE distance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            store_id TEXT NOT NULL,
            store_name TEXT NOT NULL,
            store_address TEXT NOT NULL,
            distance REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        )
        """
        conn.execute(text(create_table_sql))
        conn.commit()
        print("✓ Created new distance table")


def populate_distance():
    """Populate distance table with all customer-store combinations"""
    with engine.connect() as conn:
        # Get all customers
        customers_result = conn.execute(
            text("SELECT customer_id, address FROM customers")).fetchall()
        print(f"\nFetched {len(customers_result)} customers")

        # Get all stores
        stores_result = conn.execute(
            text("SELECT store_id, store_name, address FROM stores")).fetchall()
        print(f"Fetched {len(stores_result)} stores")

        if not customers_result or not stores_result:
            print("❌ No data to populate!")
            return

        # Insert distance records
        insert_count = 0
        for customer in customers_result:
            customer_id = customer[0]
            customer_address = customer[1]

            for store in stores_result:
                store_id = store[0]
                store_name = store[1]
                store_address = store[2]

                # Generate random distance between 0.5 and 15 km
                distance = round(random.uniform(0.5, 15.0), 2)

                insert_sql = text("""
                    INSERT INTO distance 
                    (customer_id, customer_address, store_id, store_name, store_address, distance)
                    VALUES (:customer_id, :customer_address, :store_id, :store_name, :store_address, :distance)
                """)

                conn.execute(insert_sql, {
                    "customer_id": customer_id,
                    "customer_address": customer_address,
                    "store_id": store_id,
                    "store_name": store_name,
                    "store_address": store_address,
                    "distance": distance
                })

                insert_count += 1

        conn.commit()
        print(f"\n✓ Inserted {insert_count} distance records!")

        # Verify
        total = conn.execute(text("SELECT COUNT(*) FROM distance")).scalar()
        print(f"✓ Total records in distance table: {total}")

        # Show sample
        sample = conn.execute(
            text("SELECT * FROM distance LIMIT 5")).fetchall()
        print("\n📊 Sample data:")
        print("-" * 120)
        for row in sample:
            print(
                f"ID: {row[0]} | Customer: {row[1]} | Store: {row[3]} ({row[4]}) | Distance: {row[6]} km")


if __name__ == "__main__":
    print("🔍 Checking existing data...\n")
    customers, stores = check_data()

    if customers == 0 or stores == 0:
        print("\n❌ Cannot populate distance table - customers or stores table is empty!")
    else:
        print("\n🗑️  Dropping and recreating distance table...")
        drop_and_recreate_distance()

        print("\n📝 Populating distance table...")
        populate_distance()

        print("\n✅ Done!")
