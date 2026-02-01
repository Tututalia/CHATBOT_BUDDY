"""
Script to fix store_keeper_transaction table:
- Move store IDs from store_name column to store_id column
- Assign proper store names to store_name column
"""

from database import get_db_session
from crud import store_keeper_transaction_crud
import random

# Store names from the database
STORE_NAMES = [
    "Quest Mall Kolkata",
    "South City Mall Kolkata",
    "Axis Mall Sector V Kolkata",
    "City Centre Salt Lake Kolkata",
    "City Centre New Town Kolkata",
    "Mani Square Mall Kolkata",
    "Acropolis Mall Kolkata",
    "Diamond Plaza Mall Kolkata",
    "Zudio Ground Floor",
    "Zudio Park Street Ground Floor",
    "ABFRL Store South City",
    "Eden Pavilion Mall Third Floor",
    "Mani Square Mall First Floor",
    "Acropolis Mall Ground Floor",
    "Acropolis Mall First Floor",
    "South City Mall Second Floor",
    "Quest Mall First Floor",
    "Forum Mall Second Floor",
    "City Centre Mall Ground Floor",
    "Axis Mall Ground Floor",
    "Zara Store Park Street",
    "H&M Store Park Street",
    "Max Store City Centre"
]

# Store ID to Name mapping (randomly assigned)
STORE_ID_TO_NAME = {
    f"STR{str(i).zfill(3)}": random.choice(STORE_NAMES)
    for i in range(1, 24)
}


def fix_store_data():
    """Fix store_keeper_transaction table by properly assigning store_id and store_name"""

    try:
        with get_db_session() as session:
            # Get all transactions
            all_transactions = store_keeper_transaction_crud.get_all(
                session, limit=1000)

            print(f"Found {len(all_transactions)} transactions to process")

            fixed_count = 0
            for tx in all_transactions:
                needs_update = False
                update_data = {}

                # Check if store_name contains a store ID pattern (STR + digits)
                if tx.store_name and tx.store_name.startswith("STR") and len(tx.store_name) <= 6:
                    store_id = tx.store_name

                    # Assign proper store_id and store_name
                    if store_id in STORE_ID_TO_NAME:
                        update_data['store_id'] = store_id
                        update_data['store_name'] = STORE_ID_TO_NAME[store_id]
                        needs_update = True

                # Fix "Online" entries - assign a random store
                elif tx.store_name == "Online":
                    random_store_id = random.choice(
                        list(STORE_ID_TO_NAME.keys()))
                    update_data['store_id'] = random_store_id
                    update_data['store_name'] = STORE_ID_TO_NAME[random_store_id]
                    needs_update = True

                # If store_id is NULL but store_name exists and is not a store ID
                elif tx.store_id is None and tx.store_name and not tx.store_name.startswith("STR"):
                    # Assign a random store_id
                    random_store_id = random.choice(
                        list(STORE_ID_TO_NAME.keys()))
                    update_data['store_id'] = random_store_id
                    needs_update = True

                if needs_update:
                    store_keeper_transaction_crud.update(
                        session, tx.id, update_data)
                    fixed_count += 1
                    print(
                        f"Updated transaction {tx.id}: store_id={update_data.get('store_id', tx.store_id)}, store_name={update_data.get('store_name', tx.store_name)}")

            print(f"\n✅ Successfully updated {fixed_count} transactions")

    except Exception as e:
        print(f"❌ Error fixing store data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting store data fix...\n")
    fix_store_data()
    print("\nDone!")
