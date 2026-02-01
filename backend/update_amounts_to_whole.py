"""
Script to update all store keeper transactions amounts to whole numbers
"""
from sqlmodel import Session
from database import engine
from models import StoreKeeperTransaction
from crud import store_keeper_transaction_crud


def update_amounts_to_whole_numbers():
    """Update all transaction amounts to whole numbers"""
    with Session(engine) as session:
        # Get all transactions
        all_transactions = store_keeper_transaction_crud.get_all(
            session, skip=0, limit=100000)

        updated_count = 0

        for transaction in all_transactions:
            # Round amount to whole number
            whole_amount = int(round(transaction.amount))

            if transaction.amount != whole_amount:
                try:
                    store_keeper_transaction_crud.update(
                        session,
                        transaction.id,
                        {"amount": whole_amount}
                    )
                    updated_count += 1

                    if updated_count % 50 == 0:
                        print(f"Updated {updated_count} transactions...")

                except Exception as e:
                    print(f"Error updating transaction {transaction.id}: {e}")

        print(
            f"\n✅ Successfully updated {updated_count} transaction amounts to whole numbers")
        print(f"📊 Total transactions in table: {len(all_transactions)}")


if __name__ == "__main__":
    print("Updating all store keeper transaction amounts to whole numbers...")
    update_amounts_to_whole_numbers()
    print("Done!")
