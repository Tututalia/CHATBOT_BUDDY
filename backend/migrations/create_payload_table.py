"""
Migration script to create payload table
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from pathlib import Path

# Database configuration - look in parent directory (backend folder)
DB_PATH = Path(__file__).parent.parent / "retail_agent.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


def create_payload_table():
    """
    Create the payload table to store conversation log data
    """
    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)

    try:
        with engine.connect() as conn:
            # Check if table already exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='payload'"
            ))
            table_exists = result.fetchone() is not None

            if table_exists:
                print("✓ payload table already exists")
            else:
                print("Creating payload table...")
                conn.execute(text("""
                    CREATE TABLE payload (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    )
                """))
                
                # Create index on customer_id for faster queries
                conn.execute(text(
                    "CREATE INDEX idx_payload_customer_id ON payload(customer_id)"
                ))
                
                conn.commit()
                print("✓ payload table created successfully!")

            # Verify table structure
            result = conn.execute(text("PRAGMA table_info(payload)"))
            columns = [row[1] for row in result.fetchall()]
            print(f"\nColumns in payload table: {columns}\n")

            print("Migration completed successfully! ✓")

    except OperationalError as e:
        print(f"Error during migration: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Starting migration: Create payload table")
    print("=" * 60)

    # Check if database file exists
    if not DB_PATH.exists():
        print(f"Warning: retail_agent.db not found at {DB_PATH}")
        print("Make sure the database file exists in the backend folder.")
        exit(1)

    print(f"Database found at: {DB_PATH}\n")

    create_payload_table()

    print("\n" + "=" * 60)
    print("Migration script finished!")
    print("=" * 60)
