"""
Examples of using the new UniversalCRUD class

This file demonstrates how to use the dynamic CRUD operations.
"""

from database import get_session, init_db
from crud import UniversalCRUD, customer_crud, product_crud
from models import Customer, Product


def example_basic_operations():
    """Basic CRUD operations"""

    # Initialize database
    init_db()

    # Get a session
    session = next(get_session())

    # === Example 1: Using pre-configured CRUD instances ===

    # Create a customer
    new_customer = Customer(
        customer_id="CUST999",
        customer_name="John Doe",
        gender="Male",
        phone="9999999999",
        address="123 Test Street",
        loyalty_points=100
    )
    created = customer_crud.create(session, new_customer)
    print(f"Created customer: {created.customer_name}")

    # Get by ID
    customer = customer_crud.get_by_id(session, "CUST999")
    print(f"Retrieved customer: {customer.customer_name}")

    # Update
    updated = customer_crud.update(session, "CUST999", {
        "loyalty_points": 200,
        "address": "456 New Street"
    })
    print(f"Updated customer loyalty points: {updated.loyalty_points}")

    # Delete
    deleted = customer_crud.delete(session, "CUST999")
    print(f"Customer deleted: {deleted}")


def example_dynamic_filtering():
    """Advanced filtering with dynamic operators"""

    session = next(get_session())

    # === Example 2: Dynamic filtering ===

    # Filter products by multiple criteria
    products = product_crud.filter(
        session=session,
        filters={
            "category": "Shirt",
            "price": 1500,
            "gender": "Male"
        },
        operators={
            "price": ">="  # Get products with price >= 1500
        },
        order_by="price",
        order_desc=True,
        limit=10
    )

    for product in products:
        print(f"{product.product_name}: ₹{product.price}")

    # Filter with contains operator
    customers = customer_crud.filter(
        session=session,
        filters={
            "customer_name": "Arjun",
            "loyalty_points": 300
        },
        operators={
            "customer_name": "contains",
            "loyalty_points": ">="
        }
    )

    for customer in customers:
        print(f"{customer.customer_name}: {customer.loyalty_points} points")


def example_custom_model():
    """Using UniversalCRUD with a new model dynamically"""

    session = next(get_session())

    # === Example 3: Create CRUD for any model dynamically ===

    # Create a CRUD instance for Product with custom primary key
    product_operations = UniversalCRUD(Product, primary_key="product_id")

    # Get all products
    all_products = product_operations.get_all(session, limit=5)
    print(f"Total products fetched: {len(all_products)}")

    # Count products
    total_count = product_operations.count(session)
    print(f"Total products in database: {total_count}")

    # Check if a product exists
    exists = product_operations.exists(session, "PRD001")
    print(f"Product PRD001 exists: {exists}")


def example_custom_queries():
    """Using custom queries for exceptional cases"""

    from sqlmodel import select, func
    from models import Product, Customer

    session = next(get_session())

    # === Example 4: Custom queries for complex scenarios ===

    # Custom query: Get products with price between range
    custom_statement = select(Product).where(
        (Product.price >= 1000) & (Product.price <= 3000)
    ).order_by(Product.price.desc())

    results = product_crud.execute_custom_query(session, custom_statement)
    print(f"Products in price range 1000-3000: {len(results)}")

    # Custom aggregation: Average loyalty points
    avg_query = select(func.avg(Customer.loyalty_points))
    avg_loyalty = customer_crud.execute_custom_scalar_query(session, avg_query)
    print(f"Average loyalty points: {avg_loyalty}")


def example_bulk_operations():
    """Bulk create operations"""

    session = next(get_session())

    # === Example 5: Bulk create ===

    customers_data = [
        {
            "customer_id": f"CUST99{i}",
            "customer_name": f"Test User {i}",
            "gender": "Male" if i % 2 == 0 else "Female",
            "phone": f"999999999{i}",
            "address": f"{i} Test Street",
            "loyalty_points": i * 10
        }
        for i in range(1, 6)
    ]

    # Create multiple customers at once
    created_customers = customer_crud.bulk_create(session, customers_data)
    print(f"Bulk created {len(created_customers)} customers")

    # Cleanup
    for customer in created_customers:
        customer_crud.delete(session, customer.customer_id)


def example_advanced_filtering():
    """Advanced filtering examples"""

    session = next(get_session())

    # === Example 6: Advanced filtering with 'in' and 'like' operators ===

    # Filter products by multiple categories using 'in' operator
    products = product_crud.filter(
        session=session,
        filters={
            "category": ["Shirt", "Jeans", "Jacket"]
        },
        operators={
            "category": "in"
        },
        limit=20
    )
    print(f"Products in specified categories: {len(products)}")

    # Filter using 'like' operator (SQL LIKE pattern)
    products_like = product_crud.filter(
        session=session,
        filters={
            "product_name": "%Nike%"  # Products containing 'Nike'
        },
        operators={
            "product_name": "like"
        }
    )
    print(f"Products matching pattern: {len(products_like)}")


if __name__ == "__main__":
    print("=" * 60)
    print("UniversalCRUD Usage Examples")
    print("=" * 60)

    print("\n### Example 1: Basic Operations ###")
    try:
        example_basic_operations()
    except Exception as e:
        print(f"Error: {e}")

    print("\n### Example 2: Dynamic Filtering ###")
    try:
        example_dynamic_filtering()
    except Exception as e:
        print(f"Error: {e}")

    print("\n### Example 3: Custom Model Operations ###")
    try:
        example_custom_model()
    except Exception as e:
        print(f"Error: {e}")

    print("\n### Example 4: Custom Queries ###")
    try:
        example_custom_queries()
    except Exception as e:
        print(f"Error: {e}")

    print("\n### Example 5: Bulk Operations ###")
    try:
        example_bulk_operations()
    except Exception as e:
        print(f"Error: {e}")

    print("\n### Example 6: Advanced Filtering ###")
    try:
        example_advanced_filtering()
    except Exception as e:
        print(f"Error: {e}")
