"""Test adding items to cart with different quantities"""
from database import get_db_session
from crud import cart_crud
from intelligent_agent_graph import add_to_cart_agent
import time

# Clear existing test cart
print("Clearing existing cart for CUST001...")
with get_db_session() as session:
    items = cart_crud.filter(session, {"customer_id": "CUST001"}, {
                             "customer_id": "=="}, limit=50)
    for item in items:
        cart_crud.delete(session, item.order_id)
    print(f"✅ Cleared {len(items)} items")

# Test 1: Add PRD049 with quantity 4
print("\n" + "="*60)
print("TEST 1: Adding PRD049 with quantity 4")
print("="*60)
result = add_to_cart_agent.invoke({
    "product_id": "PRD049",
    "quantity": 4,
    "customer_id": "CUST001"
})
print(result)

time.sleep(1)

# Test 2: Add PRD056 with quantity 2
print("\n" + "="*60)
print("TEST 2: Adding PRD056 with quantity 2")
print("="*60)
result = add_to_cart_agent.invoke({
    "product_id": "PRD056",
    "quantity": 2,
    "customer_id": "CUST001"
})
print(result)

time.sleep(1)

# Verify cart contents
print("\n" + "="*60)
print("VERIFICATION: Cart contents")
print("="*60)
with get_db_session() as session:
    items = cart_crud.filter(session, {"customer_id": "CUST001"}, {
                             "customer_id": "=="}, limit=50)
    for item in items:
        print(f"Order: {item.order_id}")
        print(f"  Product: {item.product_id}")
        print(f"  Quantity: {item.quantity}")
        print(f"  Status: {item.status}")
        print()

print("Test complete!")
