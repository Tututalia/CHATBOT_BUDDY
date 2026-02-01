"""
Migration: Add quantity column to cart table
Run this to fix cart quantity tracking
"""

import sqlite3
import os


def add_quantity_column():
    """Add quantity column to cart table"""

    # Path to database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'retail_agent.db')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 Adding quantity column to cart table...")

        # Check if column already exists
        cursor.execute("PRAGMA table_info(cart)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'quantity' in columns:
            print("✅ Quantity column already exists!")
            return

        # Add quantity column with default value 1
        cursor.execute("""
            ALTER TABLE cart ADD COLUMN quantity INTEGER DEFAULT 1
        """)

        conn.commit()
        print("✅ Successfully added quantity column to cart table!")
        print("📊 You can now track product quantities in cart.")

        # Show current cart structure
        cursor.execute("PRAGMA table_info(cart)")
        columns = cursor.fetchall()
        print("\n📋 Updated cart table structure:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

    except sqlite3.Error as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CART TABLE MIGRATION - ADD QUANTITY COLUMN")
    print("="*60 + "\n")

    add_quantity_column()

    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE")
    print("="*60 + "\n")
