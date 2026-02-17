"""
Script to create and populate the distance table.
This table stores distances between customers and stores.
"""

import random
from sqlalchemy import text
from database import engine, get_db_session


def create_distance_table():
    """Create the distance table with required columns"""

    # SQL to create the distance table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS distance (
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

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
        print("✓ Distance table created successfully!")


def populate_distance_table():
    """Populate the distance table with customer-store combinations and random distances"""

    session = get_db_session()

    try:
        # Get all customers
        customers_query = text("SELECT customer_id, address FROM customers")
        customers = session.execute(customers_query).fetchall()

        # Get all stores
        stores_query = text("SELECT store_id, store_name, address FROM stores")
        stores = session.execute(stores_query).fetchall()

        print(f"Found {len(customers)} customers and {len(stores)} stores")

        # Clear existing data in distance table
        session.execute(text("DELETE FROM distance"))
        session.commit()

        # Create distance entries for each customer-store combination
        insert_count = 0
        for customer in customers:
            customer_id = customer[0]
            customer_address = customer[1]

            for store in stores:
                store_id = store[0]
                store_name = store[1]
                store_address = store[2]

                # Generate random distance between 0.5 and 15 km
                distance = round(random.uniform(0.5, 15.0), 2)

                # Insert the distance record
                insert_sql = text("""
                    INSERT INTO distance 
                    (customer_id, customer_address, store_id, store_name, store_address, distance)
                    VALUES (:customer_id, :customer_address, :store_id, :store_name, :store_address, :distance)
                """)

                session.execute(insert_sql, {
                    "customer_id": customer_id,
                    "customer_address": customer_address,
                    "store_id": store_id,
                    "store_name": store_name,
                    "store_address": store_address,
                    "distance": distance
                })

                insert_count += 1

        session.commit()
        print(f"✓ Successfully inserted {insert_count} distance records!")

        # Show sample data
        sample_query = text("SELECT * FROM distance LIMIT 10")
        sample_data = session.execute(sample_query).fetchall()

        print("\n📊 Sample distance data:")
        print("-" * 120)
        for row in sample_data:
            print(
                f"Customer ID: {row[1]} | Store ID: {row[3]} | Store Name: {row[4]} | Distance: {row[6]} km")

    except Exception as e:
        print(f"❌ Error populating distance table: {e}")
        session.rollback()
    finally:
        session.close()


def view_distance_stats():
    """View statistics about the distance table"""

    session = get_db_session()

    try:
        # Get total count
        count_query = text("SELECT COUNT(*) FROM distance")
        total_count = session.execute(count_query).scalar()

        # Get min, max, avg distance
        stats_query = text("""
            SELECT 
                MIN(distance) as min_distance,
                MAX(distance) as max_distance,
                AVG(distance) as avg_distance
            FROM distance
        """)
        stats = session.execute(stats_query).fetchone()

        print("\n📈 Distance Table Statistics:")
        print("-" * 50)
        print(f"Total Records: {total_count}")
        print(f"Min Distance: {stats[0]:.2f} km")
        print(f"Max Distance: {stats[1]:.2f} km")
        print(f"Avg Distance: {stats[2]:.2f} km")

    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Creating distance table...")
    create_distance_table()

    print("\n📝 Populating distance table with data...")
    populate_distance_table()

    print("\n📊 Viewing statistics...")
    view_distance_stats()

    print("\n✅ Done!")
