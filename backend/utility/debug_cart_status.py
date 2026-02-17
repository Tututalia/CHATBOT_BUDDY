"""
Debug script to show ALL cart items with their status and channel
"""
from database import get_db_session
from crud import cart_crud
from models import Cart

def debug_cart():
    with get_db_session() as session:
        # Get ALL cart items regardless of status
        all_items = session.query(Cart).all()
        
        print(f"\n{'='*80}")
        print(f"TOTAL CART ITEMS IN DATABASE: {len(all_items)}")
        print(f"{'='*80}\n")
        
        if not all_items:
            print("✅ Cart is empty!")
            return
        
        # Group by status and channel
        by_status = {}
        for item in all_items:
            key = f"{item.status} | {item.channel}"
            if key not in by_status:
                by_status[key] = []
            by_status[key].append(item)
        
        for status_channel, items in by_status.items():
            print(f"\n📊 Status: {status_channel} ({len(items)} items)")
            print("-" * 80)
            for item in items:
                print(f"  Order ID: {item.order_id}")
                print(f"  Customer: {item.customer_id}")
                print(f"  Product: {item.product_id}")
                print(f"  Quantity: {getattr(item, 'quantity', 1)}")
                print(f"  Created: {getattr(item, 'created_at', 'N/A')}")
                print()

if __name__ == "__main__":
    debug_cart()
