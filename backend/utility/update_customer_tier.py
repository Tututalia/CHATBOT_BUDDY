"""
Script to update customer_type for a specific customer
"""

from sqlmodel import Session, create_engine, select
from models import Customer

# Create engine without echo to avoid SQL query logs
DATABASE_URL = "sqlite:///./retail_agent.db"
engine = create_engine(DATABASE_URL, echo=False)


def update_customer_tier(customer_id: str, new_tier: str):
    """
    Update customer_type for a specific customer

    Args:
        customer_id: The customer ID to update
        new_tier: The new tier value (tier_1, tier_2, or tier_3)
    """
    with Session(engine) as session:
        # Fetch the customer
        customer = session.exec(
            select(Customer).where(Customer.customer_id == customer_id)
        ).first()

        if not customer:
            print(f"❌ Customer {customer_id} not found")
            return False

        # Update customer_type
        old_tier = customer.customer_type
        customer.customer_type = new_tier
        customer.type_justification = f"Manually updated to {new_tier}"

        session.add(customer)
        session.commit()

        print(f"✅ Successfully updated customer {customer_id}")
        print(f"   Old tier: {old_tier}")
        print(f"   New tier: {new_tier}")
        print(f"   Customer name: {customer.customer_name}")
        return True


if __name__ == "__main__":
    # Update CUST001 to tier_1
    update_customer_tier("CUST001", "tier_1")
