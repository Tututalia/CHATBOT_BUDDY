from database import engine
import sqlite3


def run():
    conn = sqlite3.connect('retail_agent.db')
    cur = conn.cursor()

    print('PRAGMA table_info(stores)')
    for row in cur.execute("PRAGMA table_info('stores')"):
        print(row)

    print('\nPRAGMA table_info(store_keeper_transactions)')
    for row in cur.execute("PRAGMA table_info('store_keeper_transactions')"):
        print(row)

    print('\nPRAGMA foreign_key_list(store_keeper_transactions)')
    for row in cur.execute("PRAGMA foreign_key_list('store_keeper_transactions')"):
        print(row)

    # Check existence of a sample store id
    print('\nChecking sample store STR001 exists:')
    for row in cur.execute("SELECT store_id FROM stores WHERE store_id = 'STR001'"):
        print('Found', row)

    conn.close()


if __name__ == '__main__':
    run()
