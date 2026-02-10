"""
Script to update loyalty_points column in products and customers tables with random values
"""
import random
from database import get_db_session
from crud import ProductCRUD, CustomerCRUD


def update_loyalty_points():
    """Update loyalty_points for all products with random values between 1 and 6"""
    try:
        with get_db_session() as session:
            # Get all products
            products = ProductCRUD.get_all(session, skip=0, limit=10000)

            print(f"Found {len(products)} products to update")

            updated_count = 0
            for product in products:
                # Generate random loyalty points between 1 and 6
                new_loyalty_points = random.randint(1, 6)

                # Update only the loyalty_points field
                ProductCRUD.update(session, product.product_id, {
                    "loyalty_points": new_loyalty_points
                })

                updated_count += 1
                print(
                    f"Updated {product.product_id} - {product.product_name}: loyalty_points = {new_loyalty_points}")

            print(
                f"\n✅ Successfully updated loyalty_points for {updated_count} products!")
            print("All loyalty points are now randomly set between 1-6.")

    except Exception as e:
        print(f"❌ Error updating loyalty points: {e}")
        import traceback
        traceback.print_exc()


def update_customer_loyalty_points():
    """Update loyalty_points for all customers with random values between 2 and 8"""
    try:
        with get_db_session() as session:
            # Get all customers
            customers = CustomerCRUD.get_all(session, skip=0, limit=10000)

            print(f"Found {len(customers)} customers to update")

            updated_count = 0
            for customer in customers:
                # Generate random loyalty points between 2 and 8
                new_loyalty_points = random.randint(2, 8)

                # Update only the loyalty_points field
                CustomerCRUD.update(session, customer.customer_id, {
                    "loyalty_points": new_loyalty_points
                })

                updated_count += 1
                print(
                    f"Updated {customer.customer_id} - {customer.customer_name}: loyalty_points = {new_loyalty_points}")

            print(
                f"\n✅ Successfully updated loyalty_points for {updated_count} customers!")
            print("All customer loyalty points are now randomly set between 2-8.")

    except Exception as e:
        print(f"❌ Error updating customer loyalty points: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting loyalty points update...")
    print("=" * 60)

    print("\n📦 UPDATING PRODUCTS TABLE...")
    print("-" * 60)
    update_loyalty_points()

    print("\n👥 UPDATING CUSTOMERS TABLE...")
    print("-" * 60)
    update_customer_loyalty_points()

    print("\n" + "=" * 60)
    print("✅ All updates complete!")
