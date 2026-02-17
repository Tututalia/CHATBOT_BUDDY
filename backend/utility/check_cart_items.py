"""Check all cart items in database"""
from database import get_db_session
from models import Cart

with get_db_session() as session:
    carts = session.query(Cart).all()
    print(f"\n{'='*60}")
    print(f"TOTAL CART ITEMS IN DATABASE: {len(carts)}")
    print(f"{'='*60}\n")
    
    if len(carts) == 0:
        print("✅ Cart is empty!")
    else:
        for i, c in enumerate(carts, 1):
            print(f"{i}. Customer: {c.customer_id}, Product: {c.product_id}, Qty: {c.quantity}, Status: {c.status}, OrderID: {c.order_id}")
