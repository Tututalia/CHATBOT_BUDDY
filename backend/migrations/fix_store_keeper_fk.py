import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'retail_agent.db')


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    print('Starting migration: fix FK on store_keeper_transactions')
    # Disable FK checks while altering
    cur.execute('PRAGMA foreign_keys=OFF')

    # Create new table with correct FK mapping: store_id -> stores(store_id)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS store_keeper_transactions_new (
        id INTEGER PRIMARY KEY,
        customer_id VARCHAR NOT NULL,
        product_id VARCHAR NOT NULL,
        date VARCHAR NOT NULL,
        user_name VARCHAR NOT NULL,
        product VARCHAR NOT NULL,
        qty INTEGER NOT NULL,
        mode VARCHAR NOT NULL,
        store_name VARCHAR NOT NULL,
        store_id VARCHAR,
        status VARCHAR NOT NULL,
        amount FLOAT NOT NULL,
        address VARCHAR NOT NULL,
        phone VARCHAR NOT NULL,
        FOREIGN KEY(store_id) REFERENCES stores(store_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )
    ''')

    # Copy data, try to populate store_id from existing store_id if present,
    # else if store_name matches a store_id, use that. Otherwise NULL.
    cur.execute('''
    INSERT INTO store_keeper_transactions_new (id, customer_id, product_id, date, user_name, product, qty, mode, store_name, store_id, status, amount, address, phone)
    SELECT id, customer_id, product_id, date, user_name, product, qty, mode, store_name,
        CASE
            WHEN store_id IS NOT NULL THEN store_id
            WHEN store_name IN (SELECT store_id FROM stores) THEN store_name
            ELSE NULL
        END as store_id,
        status, amount, address, phone
    FROM store_keeper_transactions;
    ''')

    # Drop old table and rename new
    cur.execute('DROP TABLE store_keeper_transactions')
    cur.execute(
        'ALTER TABLE store_keeper_transactions_new RENAME TO store_keeper_transactions')

    # Re-enable FK checks
    cur.execute('PRAGMA foreign_keys=ON')
    conn.commit()
    conn.close()
    print('Migration complete: store_keeper_transactions FK fixed')


if __name__ == '__main__':
    run_migration()
