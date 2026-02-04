"""
Migration script to add customer_type and type_justification columns to customers table
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os

# Database configuration
DATABASE_URL = "sqlite:///./retail_agent.db"


def add_customer_type_columns():
    """
    Add customer_type and type_justification columns to the customers table
    """
    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)

    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("PRAGMA table_info(customers)"))
            columns = [row[1] for row in result.fetchall()]

            print(f"\nExisting columns in customers table: {columns}\n")

            # Add customer_type column if it doesn't exist
            if 'customer_type' not in columns:
                print("Adding customer_type column...")
                conn.execute(text(
                    "ALTER TABLE customers ADD COLUMN customer_type TEXT"
                ))
                conn.commit()
                print("✓ customer_type column added successfully!")
            else:
                print("✓ customer_type column already exists")

            # Add type_justification column if it doesn't exist
            if 'type_justification' not in columns:
                print("Adding type_justification column...")
                conn.execute(text(
                    "ALTER TABLE customers ADD COLUMN type_justification TEXT"
                ))
                conn.commit()
                print("✓ type_justification column added successfully!")
            else:
                print("✓ type_justification column already exists")

            # Verify columns were added
            result = conn.execute(text("PRAGMA table_info(customers)"))
            updated_columns = [row[1] for row in result.fetchall()]
            print(f"\nUpdated columns in customers table: {updated_columns}\n")

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
    print("Starting migration: Add customer_type and type_justification columns")
    print("=" * 60)

    # Check if database file exists
    if not os.path.exists("retail_agent.db"):
        print("Warning: retail_agent.db not found in current directory!")
        print("Make sure you're running this script from the backend folder.")
        exit(1)

    add_customer_type_columns()

    print("\n" + "=" * 60)
    print("Migration script finished!")
    print("=" * 60)
