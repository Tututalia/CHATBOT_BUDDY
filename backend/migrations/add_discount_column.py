"""
Migration script to add discount column to products table
and populate it with random discount values (0-80)
"""
from models import Product
from database import engine
from sqlmodel import Session, select
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def add_discount_column():
    """
    Add discount column to products table and populate with random values (0-80)
    """
    print("Starting discount column migration...")

    with Session(engine) as session:
        try:
            # First, try to add the column using raw SQL
            # SQLite doesn't support ALTER COLUMN, so we add it if not exists
            try:
                session.exec(
                    text("ALTER TABLE products ADD COLUMN discount INTEGER DEFAULT 0"))
                session.commit()
                print("✓ Added discount column to products table")
            except Exception as e:
                # Column might already exist
                print(f"Note: {e}")
                print("Column might already exist, proceeding with population...")

            # Fetch all products
            products = session.exec(select(Product)).all()
            print(f"Found {len(products)} products to update")

            # Update each product with a random discount (0-80)
            updated_count = 0
            for product in products:
                # Generate random discount between 0 and 80
                random_discount = random.randint(0, 80)
                product.discount = random_discount
                session.add(product)
                updated_count += 1

                if updated_count % 10 == 0:
                    print(f"Updated {updated_count} products...")

            # Commit all changes
            session.commit()
            print(
                f"\n✓ Successfully updated {updated_count} products with random discounts (0-80)")

            # Display some sample products with their discounts
            print("\nSample products with discounts:")
            sample_products = session.exec(select(Product).limit(10)).all()
            for product in sample_products:
                print(
                    f"  - {product.product_name}: {product.discount}% off (Price: ${product.price})")

        except Exception as e:
            session.rollback()
            print(f"✗ Error during migration: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


if __name__ == "__main__":
    # Import text for raw SQL
    from sqlalchemy import text

    print("=" * 60)
    print("Product Discount Column Migration")
    print("=" * 60)

    success = add_discount_column()

    if success:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)
