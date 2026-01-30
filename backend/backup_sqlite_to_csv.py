import sqlite3
import csv
import os

# Path to your SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'data.db')
# Output directory for CSV backups
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backup_csv')

# List of tables to backup (add/remove as needed)
TABLES = [
    'customers',
    'products',
    'stores',
    'order_history',
    'store_keeper_transactions',
    'cart',
    'admin_dashboard_data'
]


def backup_table_to_csv(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]
    out_path = os.path.join(BACKUP_DIR, f'{table_name}.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(col_names)
        writer.writerows(rows)
    print(f'Backed up {table_name} to {out_path}')


def main():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    conn = sqlite3.connect(DB_PATH)
    try:
        for table in TABLES:
            try:
                backup_table_to_csv(conn, table)
            except Exception as e:
                print(f'Warning: Could not backup table {table}: {e}')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
