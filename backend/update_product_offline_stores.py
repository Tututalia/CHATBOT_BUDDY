"""
Script to update offline_stores in products table based on store_ids and updated store names
"""
from database import get_db_session
from models import Product, Store
from sqlmodel import select


def update_product_offline_stores():
    """Update offline_stores column to match the updated store names"""
    session = get_db_session()

    try:
        # Get all stores and create a mapping of store_id -> store_name
        stores = session.exec(select(Store)).all()
        store_map = {store.store_id: store.store_name for store in stores}

        print(f"Loaded {len(store_map)} stores")
        print("\nStore mapping:")
        for store_id, store_name in sorted(store_map.items())[:5]:
            print(f"  {store_id}: {store_name}")
        print(f"  ... and {len(store_map) - 5} more\n")

        # Get all products
        products = session.exec(select(Product)).all()
        print(f"Found {len(products)} products to update\n")

        updates_made = 0
        skipped = 0

        for product in products:
            if product.store_ids:
                # Parse store IDs (semicolon-separated, may have spaces)
                store_ids = [sid.strip()
                             for sid in product.store_ids.split(';')]

                # Map store IDs to updated store names
                new_store_names = []
                for store_id in store_ids:
                    if store_id in store_map:
                        new_store_names.append(store_map[store_id])
                    else:
                        print(
                            f"  WARNING: Store ID {store_id} not found for product {product.product_id}")

                # Update offline_stores with new names
                old_offline_stores = product.offline_stores
                product.offline_stores = "; ".join(new_store_names)

                if old_offline_stores != product.offline_stores:
                    print(
                        f"Product {product.product_id} ({product.product_name[:30]}...):")
                    print(f"  Old: {old_offline_stores}")
                    print(f"  New: {product.offline_stores}")
                    print()
                    updates_made += 1
                else:
                    skipped += 1
            else:
                skipped += 1

        # Commit changes
        session.commit()
        print(f"\n✓ Successfully updated {updates_made} products!")
        print(
            f"  Skipped {skipped} products (no changes needed or no store_ids)")

        # Show sample of updated products
        print("\n=== Sample Updated Products ===")
        sample_products = session.exec(select(Product).limit(5)).all()
        for product in sample_products:
            print(f"\n{product.product_id}: {product.product_name}")
            print(f"  Store IDs: {product.store_ids}")
            print(f"  Offline Stores: {product.offline_stores}")

    except Exception as e:
        session.rollback()
        print(f"Error updating products: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=== Updating Product Offline Stores ===\n")
    update_product_offline_stores()
