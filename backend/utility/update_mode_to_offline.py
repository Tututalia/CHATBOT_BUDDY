"""
Script to update all store keeper transactions mode to Offline
"""
from sqlmodel import Session, select
from database import engine
from models import StoreKeeperTransaction
from crud import store_keeper_transaction_crud


def update_all_to_offline():
    """Update all transactions to have mode = 'Offline'"""
    with Session(engine) as session:
        # Get all transactions
        all_transactions = store_keeper_transaction_crud.get_all(
            session, skip=0, limit=100000)

        updated_count = 0

        for transaction in all_transactions:
            if transaction.mode != "Offline":
                try:
                    store_keeper_transaction_crud.update(
                        session,
                        transaction.id,
                        {"mode": "Offline"}
                    )
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating transaction {transaction.id}: {e}")

        print(
            f"✅ Successfully updated {updated_count} transactions to Offline mode")
        print(f"📊 Total transactions in table: {len(all_transactions)}")


if __name__ == "__main__":
    print("Updating all store keeper transactions to Offline mode...")
    update_all_to_offline()
    print("Done!")
