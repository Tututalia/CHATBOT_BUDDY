from intelligent_agent_graph import payment_agent, create_pending_cart
from crud import product_crud, customer_crud, cart_crud, order_history_crud, store_keeper_transaction_crud
from database import get_db_session
import time


def run():
    # pick a product and customer from DB
    with get_db_session() as s:
        products = product_crud.get_all(s, limit=5)
        customers = customer_crud.get_all(s, limit=5)

    if not products:
        print("No products found in DB - aborting test")
        return

    product_id = products[0].product_id
    customer_id = customers[0].customer_id if customers else None

    print(f"Using product_id={product_id}, customer_id={customer_id}")

    print("\n1) Simulate user selecting ONLINE option (create pending cart)")
    out = create_pending_cart.invoke(
        {"product_id": product_id, "customer_id": customer_id})
    print(out)

    time.sleep(1)
    with get_db_session() as s:
        pendings = cart_crud.filter(s, filters={"product_id": product_id, "channel": "online"}, operators={
                                    "product_id": "==", "channel": "=="}, limit=1, order_by="created_at", order_desc=True)
        pending = pendings[0] if pendings else None
    print("Pending cart row after selection:", pending)

    print("\n2) Simulate payment completion (process payment)")
    out2 = payment_agent.invoke(
        {"product_id": product_id, "payment_method": "upi", "customer_id": customer_id})
    print(out2)

    time.sleep(1)
    with get_db_session() as s:
        pend = cart_crud.filter(s, filters={"product_id": product_id, "channel": "online", "status": "pending"}, operators={
                                "product_id": "==", "channel": "==", "status": "=="}, limit=1)
        pending_after = pend[0] if pend else None

        order_hist_list = order_history_crud.filter(
            s, filters={"product_id": product_id}, order_by="order_dates", order_desc=True, limit=1)
        order_hist = order_hist_list[0] if order_hist_list else None

        sk_list = store_keeper_transaction_crud.filter(
            s, filters={"product_id": product_id}, order_by="date", order_desc=True, limit=1)
        sk_tx = sk_list[0] if sk_list else None

    print("Pending after payment (should be None):", pending_after)
    print("Order history record:", order_hist)
    print("Store keeper transaction record:", sk_tx)


if __name__ == '__main__':
    run()
