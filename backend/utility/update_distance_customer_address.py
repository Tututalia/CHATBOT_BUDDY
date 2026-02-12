from database import get_db_session
from models import Customer, Distance
from sqlmodel import select


def update_distance_customer_addresses():
    session = get_db_session()
    distances = session.exec(select(Distance)).all()
    updated_count = 0
    for dist in distances:
        customer_id = dist.customer_id
        customer = session.exec(select(Customer).where(
            Customer.customer_id == customer_id)).first()
        if customer and dist.customer_address != customer.address:
            dist.customer_address = customer.address
            updated_count += 1
    session.commit()
    session.close()
    print(
        f"Updated {updated_count} customer_address values in distance table.")


if __name__ == "__main__":
    update_distance_customer_addresses()
