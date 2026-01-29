from database import get_db_session
from crud import product_crud, store_crud
import sys


def get_stores_for_product(product_identifier: str):
    with get_db_session() as s:
        # Try by exact product_id first
        prod = product_crud.get_by_id(s, product_identifier)
        if not prod:
            # Fallback to name search (contains)
            prods = product_crud.filter(s, filters={"product_name": product_identifier}, operators={
                                        "product_name": "contains"}, limit=5)
            prod = prods[0] if prods else None

        if not prod:
            print(f"No product found matching '{product_identifier}'")
            return

        print(f"Product: {prod.product_name} (ID: {prod.product_id})")

        store_ids = []
        if getattr(prod, 'store_ids', None):
            store_ids = [s_.strip()
                         for s_ in prod.store_ids.split(';') if s_.strip()]

        if store_ids:
            print('\nStores from product.store_ids:')
            for sid in store_ids:
                st = store_crud.get_by_id(s, sid)
                if st:
                    print(
                        f" - {st.store_name} (ID: {st.store_id}) — {st.address}")
                else:
                    print(f" - {sid} (not found in stores table)")
        elif getattr(prod, 'offline_stores', None):
            print('\nStores from product.offline_stores:')
            for i, name in enumerate([n.strip() for n in prod.offline_stores.split(';') if n.strip()], 1):
                print(f" - {name} (ID: S{i:03d})")
        else:
            print('\nNo store info associated with this product')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python get_product_stores.py <product_id|name_substring>')
        sys.exit(1)
    # CLI entrypoint: call the actual function
    get_stores_for_product(sys.argv[1])
