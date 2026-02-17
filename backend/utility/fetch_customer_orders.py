"""
Script to fetch all customers and their product orders
Outputs structured JSON format with customer nodes, product details, and customer tier classification
"""

from sqlmodel import Session, create_engine, select
from models import Customer, OrderHistory, Product
import json

# Create engine without echo to avoid SQL query logs
DATABASE_URL = "sqlite:///./retail_agent.db"
engine = create_engine(DATABASE_URL, echo=False)


def calculate_customer_tier(products_data):
    """
    Calculate customer tier based on purchasing behavior

    tier_1: Premium customers - buy expensive products with low discounts
    tier_2: Middle class - mixed behavior or no purchase history
    tier_3: Budget conscious - buy cheaper products with high discounts
    """
    if not products_data:
        return "tier_2", "No purchase history - classified as middle tier customer"

    # Calculate average metrics
    avg_price = sum(p["price"] for p in products_data) / len(products_data)
    avg_discount = sum(p["discount"]
                       for p in products_data) / len(products_data)
    avg_final_price = sum(p["final_price"]
                          for p in products_data) / len(products_data)

    # Classification logic
    # tier_1: High price (>4000) AND low discount (<20%)
    if avg_price > 4000 and avg_discount < 20:
        justification = f"Premium customer: High avg price (₹{avg_price:.2f}) with low avg discount ({avg_discount:.1f}%)"
        return "tier_1", justification

    # tier_3: Low price (<2000) AND high discount (>40%)
    elif avg_price < 2000 and avg_discount > 40:
        justification = f"Budget-conscious customer: Low avg price (₹{avg_price:.2f}) with high avg discount ({avg_discount:.1f}%)"
        return "tier_3", justification

    # tier_3: High discount seeker (>50%) regardless of price
    elif avg_discount > 50:
        justification = f"Discount-focused customer: Very high avg discount ({avg_discount:.1f}%) on purchases"
        return "tier_3", justification

    # tier_1: Consistently high spender (>5000) even with some discount
    elif avg_price > 5000:
        justification = f"High-value customer: Consistently high avg price (₹{avg_price:.2f})"
        return "tier_1", justification

    # tier_2: Everything in between
    else:
        justification = f"Middle-tier customer: Moderate avg price (₹{avg_price:.2f}) and discount ({avg_discount:.1f}%)"
        return "tier_2", justification


if __name__ == "__main__":
    with Session(engine) as session:
        # Fetch all customers
        customers = session.exec(select(Customer)).all()

        # Build JSON structure
        output_data = {
            "customers": []
        }

        # For each customer, fetch their orders
        for customer in customers:
            # Fetch all orders for this customer
            orders = session.exec(
                select(OrderHistory).where(
                    OrderHistory.customer_id == customer.customer_id)
            ).all()

            customer_node = {
                "customer_id": customer.customer_id,
                "products": []
            }

            if orders:
                # Get unique product_ids
                unique_product_ids = list(
                    set([order.product_id for order in orders]))

                # Fetch product details for each product
                for product_id in unique_product_ids:
                    product = session.exec(
                        select(Product).where(Product.product_id == product_id)
                    ).first()

                    if product:
                        # Calculate discounted price
                        discounted_price = round(
                            product.price * (1 - product.discount / 100), 2)

                        product_node = {
                            "product_id": product.product_id,
                            "price": float(product.price),
                            "discount": product.discount,
                            "final_price": float(discounted_price)
                        }

                        customer_node["products"].append(product_node)

            # Calculate customer tier based on products
            customer_type, type_justification = calculate_customer_tier(
                customer_node["products"])
            customer_node["customer_type"] = customer_type
            customer_node["type_justification"] = type_justification

            # Update customer record in database
            customer.customer_type = customer_type
            customer.type_justification = type_justification
            session.add(customer)

            # Add all customers (even those without orders)
            output_data["customers"].append(customer_node)

        # Commit all updates to database
        session.commit()
        print("✓ Successfully updated customer_type and type_justification in database\n")

        # Print JSON output with proper Unicode handling
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
