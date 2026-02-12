

from database import get_db_session
from models import Store
from sqlmodel import select
import re


def update_store_names_to_abfrl():
    session = get_db_session()
    brands = ["H&M", "Zara", "Max", "Zudio"]
    stores = session.exec(select(Store)).all()
    updated_count = 0
    for store in stores:
        original_name = store.store_name
        new_name = original_name
        for brand in brands:
            # Replace brand with ABFRL, case-insensitive, anywhere in the string
            new_name = re.sub(brand, "ABFRL", new_name, flags=re.IGNORECASE)
        if new_name != original_name:
            store.store_name = new_name
            updated_count += 1
    session.commit()
    session.close()
    print(
        f"Updated {updated_count} store names to ABFRL for specified brands.")


if __name__ == "__main__":
    update_store_names_to_abfrl()
