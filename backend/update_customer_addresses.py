"""
Script to update specific customer addresses in the customers table
"""
from database import get_db_session
from models import Customer
from sqlmodel import select

# Data to update
customer_updates = {
    "CUST001": "Nabapally, Kolkata, West Bengal",
    "CUST007": "Barasat Road, Anandalok, H B Town, Sodepur, Panihati, West Bengal",
    "CUST009": "Hijalpukuria, RMQ4+5G3, Habra, West Bengal 743271"
}


def update_customer_addresses():
    """Update customer addresses in the database"""
    session = get_db_session()

    try:
        print("=== Updating Customer Addresses ===\n")

        updates_made = 0
        for customer_id, new_address in customer_updates.items():
            # Find the customer
            statement = select(Customer).where(
                Customer.customer_id == customer_id)
            customer = session.exec(statement).first()

            if customer:
                old_address = customer.address
                customer.address = new_address

                print(f"Customer {customer_id} ({customer.customer_name}):")
                print(f"  Old: {old_address}")
                print(f"  New: {new_address}")
                print()

                updates_made += 1
            else:
                print(f"WARNING: Customer {customer_id} not found in database")
                print()

        # Commit changes
        session.commit()
        print(f"✓ Successfully updated {updates_made} customer addresses!")

        # Display updated customers
        print("\n=== Verification ===")
        for customer_id in customer_updates.keys():
            statement = select(Customer).where(
                Customer.customer_id == customer_id)
            customer = session.exec(statement).first()
            if customer:
                print(f"{customer.customer_id}: {customer.customer_name}")
                print(f"  Address: {customer.address}")
                print()

    except Exception as e:
        session.rollback()
        print(f"Error updating customer addresses: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    update_customer_addresses()
