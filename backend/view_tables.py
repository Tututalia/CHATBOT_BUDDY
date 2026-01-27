"""
Utility script to initialize database and view tables
"""
import sqlite3
from database import init_db, DATABASE_URL


def create_tables():
    """Create all tables in the database"""
    print("Creating database tables...")
    init_db()
    print("✓ All tables created successfully!")


def show_tables():
    """Display all tables in the database"""
    # Extract the database file path from the URL
    db_path = DATABASE_URL.replace("sqlite:///./", "")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("\n" + "="*60)
        print("DATABASE TABLES")
        print("="*60)

        if not tables:
            print("No tables found. Run create_tables() first.")
            return

        for idx, (table_name,) in enumerate(tables, 1):
            print(f"\n{idx}. {table_name.upper()}")
            print("-" * 60)

            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            print(f"{'Column':<25} {'Type':<15} {'PK':<5} {'Not Null':<10}")
            print("-" * 60)

            for col in columns:
                col_id, name, col_type, not_null, default_val, pk = col
                pk_mark = "✓" if pk else ""
                not_null_mark = "✓" if not_null else ""
                print(f"{name:<25} {col_type:<15} {pk_mark:<5} {not_null_mark:<10}")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"\nTotal rows: {count}")

        print("\n" + "="*60)
        conn.close()

    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        print("\nDatabase not found. Run create_tables() first.")


if __name__ == "__main__":
    # Create tables first
    create_tables()

    # Show table structure
    show_tables()
