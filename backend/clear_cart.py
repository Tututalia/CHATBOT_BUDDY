"""
Script to empty/clear all entries from the cart table
Use this to reset the cart for testing purposes
"""

from database import get_db_session
from crud import cart_crud
from sqlalchemy import delete
from models import Cart


def clear_cart_table():
    """Clear all entries from the cart table"""
    try:
        with get_db_session() as session:
            # Get count before deletion
            all_items = cart_crud.get_all(session, limit=1000)
            count_before = len(all_items)

            print(f"Found {count_before} items in cart table")

            if count_before == 0:
                print("✅ Cart table is already empty")
                return

            # Delete all entries
            stmt = delete(Cart)
            session.execute(stmt)
            session.commit()

            # Verify deletion
            remaining = cart_crud.get_all(session, limit=10)

            if len(remaining) == 0:
                print(
                    f"✅ Successfully cleared {count_before} items from cart table")
            else:
                print(
                    f"⚠️ Warning: {len(remaining)} items still remain in cart table")

    except Exception as e:
        print(f"❌ Error clearing cart table: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("CLEAR CART TABLE")
    print("="*60)

    confirmation = input(
        "\n⚠️  This will DELETE ALL entries from the cart table. Continue? (yes/no): ")

    if confirmation.lower() in ['yes', 'y']:
        clear_cart_table()
    else:
        print("❌ Operation cancelled")

    print("\n" + "="*60)
