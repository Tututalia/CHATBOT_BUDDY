"""
Store Kiosk Chatbot Workflow (Linear LangGraph)
- Customer logs in at store kiosk
- System checks for pending offline orders in cart DB
- LLM prompts for payment, then processes payment, fulfillment, loyalty, and post-purchase in a linear flow
"""

from crud import cart_crud
from models import Cart
from database import get_db_session
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from intelligent_agent_graph import payment_agent, fulfillment_agent, loyalty_agent, post_purchase_agent

# ============ State Definition ============


class KioskState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    customer_id: str
    order_id: str | None
    product_id: str | None
    payment_completed: bool
    fulfillment_done: bool
    loyalty_done: bool
    post_purchase_done: bool

# ============ Helper: Fetch Pending Offline Order ============


def get_pending_offline_orders(customer_id: str) -> list[Cart]:
    try:
        with get_db_session() as session:
            pending = cart_crud.filter(
                session,
                filters={"customer_id": customer_id,
                         "channel": "offline", "status": "pending"},
                operators={"customer_id": "==",
                           "channel": "==", "status": "=="},
                order_by="created_at",
                order_desc=True,
                limit=100
            )
            return pending
    except Exception as e:
        print(f"Error fetching pending offline orders: {e}")
        return []

# ============ Node 1: Welcome & Prompt Payment ============


def welcome_node(state: KioskState):
    customer_id = state["customer_id"]
    pending_orders = get_pending_offline_orders(customer_id)
    if not pending_orders:
        return {"messages": [AIMessage(content="No pending offline orders found for your account. Please contact staff for assistance.")], "order_id": None, "product_id": None}

    # Show all pending orders and ask user to select one
    msg = "Welcome back!\n\nWe found the following pending offline orders linked to your account:\n"
    order_map = {}
    try:
        from intelligent_agent_graph import get_product_by_id, get_store_by_id
        for idx, order in enumerate(pending_orders, 1):
            product = get_product_by_id(order.product_id)
            store = get_store_by_id(order.store_id) if order.store_id else None
            product_info = f"Product: {product.product_name if product else order.product_id}\nCategory: {product.category if product else ''}\nPrice: ₹{int(product.price) if product else ''}\nQuantity: {product.quantity if product else ''}\n"
            store_info = f"Store: {store.store_name if store else order.store_id} (ID: {order.store_id})\n" if order.store_id else ""
            msg += f"\n{idx}. Order ID: {order.order_id}\n{product_info}{store_info}"
            order_map[str(idx)] = order
    except Exception:
        for idx, order in enumerate(pending_orders, 1):
            msg += f"\n{idx}. Order ID: {order.order_id}\nProduct ID: {order.product_id}\nStore ID: {order.store_id}\n"
            order_map[str(idx)] = order
    msg += "\nPlease type the number of the order you want to pay for."
    # Save order_map in state for selection
    state["_order_map"] = order_map
    return {"messages": [AIMessage(content=msg)], "order_id": None, "product_id": None, "store_id": None}

# ============ Node 2: Payment Agent ============


def payment_prompt_node(state: KioskState):
    # Wait for user to say 'proceed with payment' or similar
    last_msg = state["messages"][-1] if state["messages"] else None
    if last_msg and isinstance(last_msg, HumanMessage):
        content = last_msg.content.strip()
        # If user selects an order number
        if "_order_map" in state and content in state["_order_map"]:
            selected_order = state["_order_map"][content]
            # Update state with selected order details
            state["order_id"] = selected_order.order_id
            state["product_id"] = selected_order.product_id
            state["store_id"] = selected_order.store_id
            # Prompt for payment method
            return {"messages": [AIMessage(content=f"You selected Order ID: {selected_order.order_id}. Please type your payment method (UPI, Credit, Debit, Net Banking) to proceed.")]}
        # Fallback: old proceed logic
        content_lower = content.lower()
        if "proceed" in content_lower or "pay" in content_lower or "yes" in content_lower:
            customer_id = state["customer_id"]
            product_id = state["product_id"]
            payment_msg = payment_agent.invoke({
                "product_id": product_id,
                "payment_method": "",
                "customer_id": customer_id
            })
            return {"messages": [ToolMessage(content=payment_msg, tool_call_id="payment_agent")]}
        else:
            return {"messages": [AIMessage(content="Please type the number of the order you want to pay for.")]}
    return {"messages": []}


def payment_method_node(state: KioskState):
    # Wait for user to select a payment method
    last_msg = state["messages"][-1] if state["messages"] else None
    if last_msg and isinstance(last_msg, HumanMessage):
        content = last_msg.content.lower()
        for method in ["upi", "credit", "debit", "net banking"]:
            if method in content:
                customer_id = state["customer_id"]
                product_id = state["product_id"]
                order_id = state["order_id"]
                store_id = state.get("store_id")
                # 1. Process payment
                payment_msg = payment_agent.invoke({
                    "product_id": product_id,
                    "payment_method": method,
                    "customer_id": customer_id
                })

                # 2. Remove from cart, add to order history and storekeeper transaction
                from crud import CartCRUD, OrderHistoryCRUD, StoreKeeperTransactionCRUD, ProductCRUD, StoreCRUD, CustomerCRUD
                from models import OrderHistory, StoreKeeperTransaction
                from database import get_db_session
                import datetime
                with get_db_session() as session:
                    # Debug print for order_id being deleted
                    print(
                        f"[DEBUG] Deleting cart entry with order_id: {order_id}")
                    CartCRUD.delete(session, order_id)

                    # Fetch product, customer, store details
                    product = ProductCRUD.get_by_id(session, product_id)
                    customer = CustomerCRUD.get_by_id(session, customer_id)
                    store = StoreCRUD.get_by_id(
                        session, store_id) if store_id else None

                    # Add to order history
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    order_history = OrderHistory(
                        transaction_id=order_id,
                        customer_id=customer_id,
                        customer_name=customer.customer_name if customer else "",
                        product_id=product_id,
                        product_name=product.product_name if product else "",
                        quantity=product.quantity if product else 1,
                        order_dates=now,
                        loyalty_points=product.loyalty_points if product else 0
                    )
                    OrderHistoryCRUD.create(session, order_history)

                    # Add to storekeeper transaction
                    store_keeper_txn = StoreKeeperTransaction(
                        customer_id=customer_id,
                        product_id=product_id,
                        date=now,
                        user_name=customer.customer_name if customer else "",
                        product=product.product_name if product else "",
                        qty=1,
                        mode="Offline",
                        store_name=store.store_name if store else "",
                        store_id=store_id,
                        status="Complete",
                        amount=product.price if product else 0.0,
                        address=customer.address if customer else "",
                        phone=customer.phone if customer else ""
                    )
                    StoreKeeperTransactionCRUD.create(
                        session, store_keeper_txn)

                return {"messages": [ToolMessage(content=payment_msg, tool_call_id="payment_agent")], "payment_completed": True}
        return {"messages": [AIMessage(content="Please select a valid payment method: UPI, Credit Card, Debit Card, or Net Banking.")]}
    return {"messages": []}

# ============ Node 3: Fulfillment Agent ============


def fulfillment_node(state: KioskState):
    # After payment, auto-run fulfillment
    customer_id = state["customer_id"]
    product_id = state["product_id"]
    order_id = state["order_id"]
    store_id = state.get("store_id")
    # Fetch store name if possible
    try:
        from intelligent_agent_graph import get_store_by_id
        store = get_store_by_id(store_id) if store_id else None
        store_name = store.store_name if store else store_id or "Store"
    except Exception:
        store_name = store_id or "Store"
    fulfillment_msg = fulfillment_agent.invoke({
        "product_id": product_id,
        "purchase_type": "offline",
        "store_name": store_name,
        "customer_id": customer_id,
        "order_id": order_id
    })
    return {"messages": [ToolMessage(content=fulfillment_msg, tool_call_id="fulfillment_agent")], "fulfillment_done": True}

# ============ Node 4: Loyalty Agent ============


def loyalty_node(state: KioskState):
    order_id = state["order_id"]
    product_id = state["product_id"]
    loyalty_msg = loyalty_agent.invoke({
        "order_id": order_id,
        "product_id": product_id
    })
    return {"messages": [ToolMessage(content=loyalty_msg, tool_call_id="loyalty_agent")], "loyalty_done": True}

# ============ Node 5: Post-Purchase Agent ============


def post_purchase_node(state: KioskState):
    order_id = state["order_id"]
    post_msg = post_purchase_agent.invoke({
        "order_id": order_id
    })
    return {"messages": [ToolMessage(content=post_msg, tool_call_id="post_purchase_agent")], "post_purchase_done": True}

# ============ Build Linear Graph ============


def create_kiosk_graph():
    workflow = StateGraph(KioskState)
    workflow.add_node("welcome", welcome_node)
    workflow.add_node("payment_prompt", payment_prompt_node)
    workflow.add_node("payment_method", payment_method_node)
    workflow.add_node("fulfillment", fulfillment_node)
    workflow.add_node("loyalty", loyalty_node)
    workflow.add_node("post_purchase", post_purchase_node)
    workflow.add_edge(START, "welcome")
    workflow.add_edge("welcome", "payment_prompt")
    workflow.add_edge("payment_prompt", "payment_method")
    # After payment method selection and payment, auto-run fulfillment, loyalty, post-purchase
    workflow.add_edge("payment_method", "fulfillment")
    workflow.add_edge("fulfillment", "loyalty")
    workflow.add_edge("loyalty", "post_purchase")
    workflow.add_edge("post_purchase", END)
    return workflow.compile()

# ============ Run Kiosk Chatbot ============


async def run_kiosk_chatbot(customer_id: str):
    graph = create_kiosk_graph()
    initial_state = {
        "messages": [],
        "customer_id": customer_id,
        "order_id": None,
        "product_id": None,
        "payment_completed": False,
        "fulfillment_done": False,
        "loyalty_done": False,
        "post_purchase_done": False
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state

# ============ Example Usage ============
if __name__ == "__main__":
    import asyncio
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    async def interactive_kiosk():
        customer_id = input("Enter customer ID: ").strip() or "CUST001"
        state = {
            "messages": [],
            "customer_id": customer_id,
            "order_id": None,
            "product_id": None,
            "payment_completed": False,
            "fulfillment_done": False,
            "loyalty_done": False,
            "post_purchase_done": False
        }
        # Step 1: Welcome node
        result = welcome_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        for k, v in result.items():
            if k != "messages":
                state[k] = v
        state["messages"].extend(msgs)

        # Step 2: Wait for user to proceed with payment
        user = input("\nYou: ")
        state["messages"].append(HumanMessage(content=user))
        result = payment_prompt_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, ToolMessage):
                print(f"\n🔧: {msg.content[:400]}...")
            elif isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        for k, v in result.items():
            if k != "messages":
                state[k] = v
        state["messages"].extend(msgs)

        # Step 3: Wait for user to select payment method
        user = input("\nYou (select payment method): ")
        state["messages"].append(HumanMessage(content=user))
        result = payment_method_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, ToolMessage):
                print(f"\n🔧: {msg.content[:400]}...")
            elif isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        for k, v in result.items():
            if k != "messages":
                state[k] = v
        state["messages"].extend(msgs)

        # Step 4: Fulfillment
        result = fulfillment_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, ToolMessage):
                print(f"\n🔧: {msg.content[:400]}...")
            elif isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        for k, v in result.items():
            if k != "messages":
                state[k] = v
        state["messages"].extend(msgs)

        # Step 5: Loyalty
        result = loyalty_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, ToolMessage):
                print(f"\n🔧: {msg.content[:400]}...")
            elif isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        for k, v in result.items():
            if k != "messages":
                state[k] = v
        state["messages"].extend(msgs)

        # Step 6: Post-purchase
        result = post_purchase_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, ToolMessage):
                print(f"\n🔧: {msg.content[:400]}...")
            elif isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        print("\n✅ Kiosk chatbot session complete.")

    asyncio.run(interactive_kiosk())
