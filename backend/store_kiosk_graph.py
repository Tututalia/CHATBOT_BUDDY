"""
Store Kiosk Chatbot Workflow (Linear LangGraph)
- Customer logs in at store kiosk
- System checks for pending offline orders in cart DB
- LLM prompts for payment, then processes payment, fulfillment, loyalty, and post-purchase in a linear flow
"""

import random
import time
from datetime import datetime

from crud import cart_crud, product_crud
from models import Cart
from database import get_db_session
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from intelligent_agent_graph import payment_agent, fulfillment_agent, loyalty_agent, post_purchase_agent


def _get_offline_store_id_for_customer(customer_id: str) -> str | None:
    """Resolve the customer's current offline store context from the cart table."""
    if not customer_id:
        return None
    try:
        with get_db_session() as session:
            recent = cart_crud.filter(
                session,
                filters={"customer_id": customer_id, "channel": "offline"},
                operators={"customer_id": "==", "channel": "=="},
                order_by="created_at",
                order_desc=True,
                limit=50,
            )

        for item in recent or []:
            store_id = getattr(item, "store_id", None)
            if store_id:
                return store_id
        # return None
        return "STR011"  # Default store ID if none found
    except Exception as e:
        print(f"Error resolving offline store_id for {customer_id}: {e}")
        # return None
        return "STR011"


@tool
def kiosk_add_to_cart_agent(
    product_id: str,
    quantity: int,
    customer_id: str,
    size: Optional[str] = None,
    store_id: Optional[str] = None,
) -> str:
    """Kiosk-only add-to-cart.

    Requirements:
    - MUST set channel='offline'
    - MUST set store_id based on the customer's existing offline cart context
    - MUST NOT call intelligent_agent_graph.add_to_cart_agent
    """
    product_id = (product_id or "").strip()
    if not product_id:
        return "❌ Please provide a valid product ID."

    try:
        quantity = int(quantity)
    except Exception:
        quantity = 1

    if quantity <= 0:
        return "❌ Please specify a valid quantity (greater than 0)."

    if not customer_id:
        return "❌ Missing customer_id."

    normalized_size: Optional[str] = None
    if isinstance(size, str):
        s = size.strip()
        if s:
            normalized_size = s

    # Use the explicitly provided store_id if available, otherwise resolve from cart context
    if not store_id:
        store_id = _get_offline_store_id_for_customer(customer_id)
    if not store_id:
        return (
            "❌ I couldn't determine your pickup store for this offline session. "
            "Please ask staff for assistance or restart the offline pickup flow."
        )

    try:
        with get_db_session() as session:
            product = product_crud.get_by_id(session, product_id)
            if not product:
                return f"❌ Product {product_id} not found."

            if getattr(product, "quantity", 0) < quantity:
                return (
                    f"❌ Sorry, only {getattr(product, 'quantity', 0)} units of {product.product_name} "
                    "are available in stock."
                )

            # If the same product is already in the offline cart for the same store, increment quantity.
            existing = cart_crud.filter(
                session,
                filters={
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "store_id": store_id,
                    "channel": "offline",
                    "status": "pending",
                },
                operators={
                    "customer_id": "==",
                    "product_id": "==",
                    "store_id": "==",
                    "channel": "==",
                    "status": "==",
                },
                limit=1,
            )
            if existing:
                cart_item = existing[0]
                new_qty = int(getattr(cart_item, "quantity", 1)
                              or 1) + quantity
                if getattr(product, "quantity", 0) < new_qty:
                    return (
                        f"❌ Sorry, only {getattr(product, 'quantity', 0)} units of {product.product_name} "
                        "are available in stock."
                    )
                cart_crud.update(session, cart_item.order_id,
                                 {"quantity": new_qty})
                return (
                    f"✅ Updated cart: {product.product_name} quantity is now {new_qty} "
                    f"for pickup store {store_id}."
                )

            order_id = f"KIOSK{int(time.time() * 1000) % 1000000}{random.randint(100, 999)}"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cart = Cart(
                order_id=order_id,
                customer_id=customer_id,
                product_id=product_id,
                store_id=store_id,
                channel="offline",
                status="pending",
                created_at=now,
                quantity=quantity,
                size=normalized_size,
            )
            cart_crud.create(session, cart)

            return (
                f"✅ Added to offline cart for store {store_id}: {product.product_name} "
                f"(ID: {product_id}) × {quantity}."
            )
    except Exception as e:
        print(f"Error in kiosk_add_to_cart_agent: {e}")
        return "❌ Error adding product to kiosk cart. Please try again."


@tool
def switch_channel_instore_to_online(customer_id: str, store_id: Optional[str] = None) -> str:
    """Switch customer's offline cart items to pending channel for later payment.

    This allows customers to move their in-store cart to pending so they can pay later.
    Updates offline cart items for the customer (filtered by store_id if provided):
    - Sets store_id to NULL
    - Changes channel from 'offline' to 'pending'
    - Keeps status as 'pending'
    """
    if not customer_id:
        return "❌ Customer ID is required."

    try:
        with get_db_session() as session:
            # Find offline cart items for this customer, optionally filtered by store
            filters = {"customer_id": customer_id, "channel": "offline"}
            operators = {"customer_id": "==", "channel": "=="}
            if store_id:
                filters["store_id"] = store_id
                operators["store_id"] = "=="
            offline_items = cart_crud.filter(
                session,
                filters=filters,
                operators=operators,
                limit=100,
            )

            if not offline_items:
                return "❌ No offline cart items found to switch to pending."

            # Update each item
            updated_count = 0
            for item in offline_items:
                cart_crud.update(
                    session,
                    item.order_id,
                    {"store_id": None, "channel": "pending"}
                )
                updated_count += 1

            session.commit()

            # --- Send WhatsApp notification only for CUST082 ---
            if customer_id == "CUST038":
                try:
                    from intelligent_whatsapp_graph import send_whatsapp_text
                    import logging

                    wa_phone = "+919339712883"
                    print(
                        f"[SwitchChannel] 📱 Sending WhatsApp cart-switch notification to {wa_phone} for CUST038...")

                    # Fetch customer name
                    from intelligent_agent_graph import get_customer_by_id
                    customer = get_customer_by_id(customer_id)
                    customer_name = getattr(
                        customer, 'customer_name', 'Valued Customer') if customer else 'Valued Customer'

                    # Build item details
                    items_text = ""
                    from intelligent_agent_graph import get_product_by_id
                    total_amount = 0
                    for idx, item in enumerate(offline_items, 1):
                        product = get_product_by_id(item.product_id)
                        if product:
                            qty = getattr(item, 'quantity', 1)
                            discount = getattr(product, 'discount', 0) or 0
                            price = round(
                                product.price * (1 - discount / 100), 2) if discount > 0 else product.price
                            item_total = price * qty
                            total_amount += item_total
                            items_text += f"   {idx}. {product.product_name} × {qty} — ₹{int(item_total):,}\n"
                        else:
                            items_text += f"   {idx}. {item.product_id} × {getattr(item, 'quantity', 1)}\n"

                    total_amount = round(total_amount)

                    wa_msg = (
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🛒  *RetailBuddy — Cart Moved Online*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"Hi *{customer_name}*,\n\n"
                        f"Your in-store cart has been successfully\n"
                        f"moved to your online account! 🎉\n\n"
                        f"📋  *Cart Summary*\n"
                        f"┌──────────────────────\n"
                        f"│  📦  Items Moved:  *{updated_count}*\n"
                        f"│  💰  Total Value:  *₹{total_amount:,}*\n"
                        f"└──────────────────────\n\n"
                    )
                    if items_text:
                        wa_msg += (
                            f"🧾  *Your Items*\n"
                            f"{items_text}\n"
                        )
                    wa_msg += (
                        f"*Please Note:* Your selected products will be reserved for the next 6 hours. Beyond this window, availability will be subject to real-time inventory levels. We recommend completing your purchase at your earliest convenience to ensure availability.\n\n"
                        # f"💡 _You can now complete your purchase_\n"
                        # f"   _anytime from the comfort of your home._\n\n"
                        f"Happy Shopping! 🛍️\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━"
                    )

                    send_whatsapp_text(wa_phone, wa_msg)

                    # Send quick-action buttons so the customer can act immediately
                    from whatsapp import send_quick_reply_buttons
                    send_quick_reply_buttons(wa_phone, "cart_moved_online")

                    print(
                        f"[SwitchChannel] ✅ WhatsApp cart-switch notification sent to {wa_phone} (CUST011)")
                except Exception as wa_err:
                    print(
                        f"[SwitchChannel] ❌ Failed to send WhatsApp cart-switch notification: {wa_err}")
                    import traceback
                    traceback.print_exc()

            return (
                f"✅ Successfully switched {updated_count} item(s) from in-store to pending cart. "
                f"You can now pay for these items later at your convenience."
            )
    except Exception as e:
        print(f"Error in switch_channel_instore_to_online: {e}")
        return "❌ Error switching cart to pending. Please try again."


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


def get_pending_offline_orders(customer_id: str, store_id: str | None = None) -> list[Cart]:
    try:
        with get_db_session() as session:
            filters = {"customer_id": customer_id,
                       "channel": "offline", "status": "pending"}
            operators = {"customer_id": "==",
                         "channel": "==", "status": "=="}
            if store_id:
                filters["store_id"] = store_id
                operators["store_id"] = "=="
            pending = cart_crud.filter(
                session,
                filters=filters,
                operators=operators,
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
    kiosk_store_id = state.get("kiosk_store_id") or None
    pending_orders = get_pending_offline_orders(
        customer_id, store_id=kiosk_store_id)
    if not pending_orders:
        return {"messages": [AIMessage(content="Your cart is empty. Please contact staff for assistance.")], "order_id": None, "product_id": None}

    # Show all pending orders and ask user to select one
    msg = "Welcome back!\n\nYou have the following items in your cart:\n"
    order_map = {}
    total_amount = 0
    try:
        from intelligent_agent_graph import get_product_by_id, get_store_by_id
        for idx, order in enumerate(pending_orders, 1):
            product = get_product_by_id(order.product_id)
            store = get_store_by_id(order.store_id) if order.store_id else None
            qty = getattr(order, 'quantity', 1)
            item_size = getattr(order, 'size', None) or ""

            # Calculate discount price
            if product:
                original_price = product.price
                discount = getattr(product, 'discount', 0) or 0
                discount_price = round(
                    original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                item_total = discount_price * qty
                total_amount += item_total

                # Format price info with discount
                size_line = f"\nSize: {item_size}" if item_size else ""
                if discount > 0:
                    product_info = f"Product: {product.product_name}\nCategory: {product.category}\nProduct ID: {order.product_id}{size_line}\nOriginal Price: ₹{int(original_price)}\nDiscount: {int(discount)}% off\n**Discounted Price: ₹{discount_price:.2f}**\nQuantity: {qty}\nItem Total: ₹{item_total:.2f}\n"
                else:
                    product_info = f"Product: {product.product_name}\nCategory: {product.category}\nProduct ID: {order.product_id}{size_line}\nPrice: ₹{int(original_price)}\nQuantity: {qty}\nItem Total: ₹{item_total:.2f}\n"
            else:
                item_total = 0
                product_info = f"Product ID: {order.product_id}\nQuantity: {qty}\n"

            store_info = f"Store: {store.store_name if store else order.store_id} (ID: {order.store_id})\n" if order.store_id else ""
            msg += f"\n{idx}. Order ID: {order.order_id}\n{product_info}{store_info}"
            order_map[str(idx)] = order
    except Exception as e:
        print(f"Error formatting cart items: {e}")
        for idx, order in enumerate(pending_orders, 1):
            msg += f"\n{idx}. Order ID: {order.order_id}\nProduct ID: {order.product_id}\nStore ID: {order.store_id}\n"
            order_map[str(idx)] = order
    msg += f"\n{'='*50}\n**Total Amount to Pay: ₹{total_amount:.2f}**\n{'='*50}\n\nWould you like to proceed with payment?"
    # Save order_map in state for selection
    state["_order_map"] = order_map
    return {"messages": [AIMessage(content=msg)], "order_id": None, "product_id": None, "store_id": None}

# ============ Node 2: Payment Agent ============


def payment_prompt_node(state: KioskState):
    # Wait for user to confirm payment or select an order number
    last_msg = state["messages"][-1] if state["messages"] else None
    if last_msg and isinstance(last_msg, HumanMessage):
        content = last_msg.content.strip()
        content_lower = content.lower()

        # Check if user wants to proceed with all items
        if "proceed" in content_lower or "pay" in content_lower or "yes" in content_lower:
            # User confirmed - proceed with all items in cart
            return {
                "messages": [AIMessage(content="Great! Please type your payment method (UPI, Credit Card, Debit Card, Cash on Delivery) to proceed.")],
                "pay_all": True  # Flag to indicate paying for all items
            }

        # If user selects a specific order number
        if "_order_map" in state and content in state["_order_map"]:
            selected_order = state["_order_map"][content]
            # Update state with selected order details - return them so they persist
            print(
                f"[DEBUG] Selected order: {selected_order.order_id}, product: {selected_order.product_id}, store: {selected_order.store_id}")
            return {
                "messages": [AIMessage(content=f"You selected Order ID: {selected_order.order_id}. Please type your payment method (UPI, Credit Card, Debit Card, Cash on Delivery) to proceed.")],
                "order_id": selected_order.order_id,
                "product_id": selected_order.product_id,
                "store_id": selected_order.store_id,
                "pay_all": False
            }
        else:
            # User didn't select a valid option
            return {"messages": [AIMessage(content="Please type 'yes' to proceed with payment, or type a number to select a specific item.")]}
    return {"messages": []}


def payment_method_node(state: KioskState):
    # Check if user wants to pay for all items or specific item
    pay_all = state.get("pay_all", False)

    # Fallback: if no specific order was selected, default to paying for all items
    if not pay_all and not state.get("order_id"):
        pay_all = True

    # Wait for user to select a payment method
    last_msg = state["messages"][-1] if state["messages"] else None
    if last_msg and isinstance(last_msg, HumanMessage):
        content = last_msg.content.lower()
        method_selected = None
        if "cash on delivery" in content or content.strip() == "cod" or " cod" in content:
            method_selected = "cash on delivery"
        else:
            for method in ["upi", "credit", "debit", "net banking"]:
                if method in content:
                    method_selected = method
                    break

        if method_selected:
            customer_id = state["customer_id"]

            try:
                from intelligent_agent_graph import get_product_by_id
                with get_db_session() as session:
                    if pay_all:
                        # Process all items in cart
                        kiosk_store_id = state.get("kiosk_store_id") or None

                        # Query pending offline orders directly in this session
                        # so that status updates are tracked and committed properly.
                        filters = {"customer_id": customer_id,
                                   "channel": "offline", "status": "pending"}
                        operators = {"customer_id": "==",
                                     "channel": "==", "status": "=="}
                        if kiosk_store_id:
                            filters["store_id"] = kiosk_store_id
                            operators["store_id"] = "=="
                        pending_orders = cart_crud.filter(
                            session,
                            filters=filters,
                            operators=operators,
                            order_by="created_at",
                            order_desc=True,
                            limit=100
                        )
                        if not pending_orders:
                            return {"messages": [AIMessage(content="❌ No items found in cart.")]}

                        total_amount = 0
                        order_details = []

                        for order in pending_orders:
                            # Get product details
                            product = get_product_by_id(order.product_id)
                            if product:
                                qty = getattr(order, 'quantity', 1)
                                # Calculate discount price
                                original_price = product.price
                                discount = getattr(
                                    product, 'discount', 0) or 0
                                discount_price = round(
                                    original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                                item_total = discount_price * qty
                                total_amount += item_total
                                order_details.append(
                                    f"- {product.product_name} (x{qty}): ₹{item_total:.2f}")

                            # Update cart status to 'paid' (tracked by this session)
                            order.status = 'paid'

                        session.commit()

                        payment_msg = f"""✅ **Payment Successful!**

Payment Method: {method_selected.upper()}
Items Paid:
{chr(10).join(order_details)}

Total Amount Paid: ₹{total_amount:.2f}

Your orders are now ready for pickup. Please proceed to the store counter."""

                        # Store first order details for subsequent nodes
                        first_order = pending_orders[0]
                        return {
                            "messages": [AIMessage(content=payment_msg)],
                            "payment_completed": True,
                            "order_id": first_order.order_id,
                            "product_id": first_order.product_id,
                            "store_id": first_order.store_id,
                            "all_orders": [{"order_id": o.order_id, "product_id": o.product_id, "store_id": o.store_id} for o in pending_orders]
                        }
                    else:
                        # Process single item
                        product_id = state["product_id"]
                        order_id = state["order_id"]

                        # Get cart item
                        cart_item = cart_crud.get_by_id(session, order_id)
                        if not cart_item:
                            return {"messages": [AIMessage(content="❌ Order not found. Please try again.")]}

                        # Get product details
                        product = get_product_by_id(product_id)
                        if not product:
                            return {"messages": [AIMessage(content="❌ Product not found. Please try again.")]}

                        qty = getattr(cart_item, 'quantity', 1)
                        # Calculate discount price
                        original_price = product.price
                        discount = getattr(product, 'discount', 0) or 0
                        discount_price = round(
                            original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                        total_amount = discount_price * qty

                        # Update cart status to 'paid' but keep channel as 'offline'
                        cart_item.status = 'paid'
                        session.commit()

                        payment_msg = f"""✅ **Payment Successful!**

Payment Method: {method_selected.upper()}
Order ID: {order_id}
Product: {product.product_name}
Quantity: {qty}
Amount Paid: ₹{total_amount:.2f}

Your order is now ready for pickup. Please proceed to the store counter."""

                        return {"messages": [AIMessage(content=payment_msg)], "payment_completed": True}

            except Exception as e:
                print(f"Error processing payment: {e}")
                import traceback
                traceback.print_exc()
                return {"messages": [AIMessage(content=f"❌ Payment processing failed: {str(e)}. Please try again.")]}

        return {"messages": [AIMessage(content="Please select a valid payment method: UPI, Credit Card, Debit Card, Cash on Delivery, or Net Banking.")]}
    return {"messages": []}

# ============ Node 3: Fulfillment Agent ============


def fulfillment_node(state: KioskState):
    # After payment, auto-run fulfillment
    customer_id = state["customer_id"]
    product_id = state.get("product_id")
    order_id = state.get("order_id")
    store_id = state.get("store_id")
    all_orders = state.get("all_orders", [])

    # Validate required data
    if not order_id or not product_id:
        print(f"[ERROR] fulfillment_node: Missing order_id or product_id")
        return {"messages": [AIMessage(content="⚠️ Order information missing. Please start over.")], "fulfillment_done": False}

    # Fetch store name if possible
    try:
        from intelligent_agent_graph import get_store_by_id, get_product_by_id

        if all_orders:
            # Multiple items - show summary
            total_amount = 0
            item_list = []
            store_name = None
            store_address = None

            for order_data in all_orders:
                curr_product_id = order_data["product_id"]
                curr_order_id = order_data["order_id"]
                curr_store_id = order_data.get("store_id")

                product = get_product_by_id(curr_product_id)
                if not store_name and curr_store_id:
                    store = get_store_by_id(curr_store_id)
                    if store:
                        store_name = store.store_name
                        store_address = store.address

                if product:
                    with get_db_session() as session:
                        cart_item = cart_crud.get_by_id(session, curr_order_id)
                        if cart_item:
                            qty = getattr(cart_item, 'quantity', 1)
                            # Calculate discount price
                            original_price = product.price
                            discount = getattr(product, 'discount', 0) or 0
                            discount_price = round(
                                original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                            item_total = discount_price * qty
                            total_amount += item_total
                            item_list.append(
                                f"- {product.product_name} (x{qty})")

            fulfillment_msg = f"""🏪 **In-Store Pickup Confirmed!**

Items Ready for Pickup:
{chr(10).join(item_list)}

Total Amount: ₹{total_amount:.2f}
Pickup Store: {store_name or 'Store'}
Store Address: {store_address or 'N/A'}
Status: Ready for pickup now

Please show your order details at the store counter to collect your items.

Thank you for shopping with us! 🛍️"""
        else:
            # Single item
            store = get_store_by_id(store_id) if store_id else None
            store_name = store.store_name if store else store_id or "Store"
            store_address = store.address if store else "N/A"

            # Get product details for quantity
            product = get_product_by_id(product_id)
            qty = 1
            total_amount = 0
            if product:
                # Get quantity from cart
                with get_db_session() as session:
                    cart_item = cart_crud.get_by_id(session, order_id)
                    if cart_item:
                        qty = getattr(cart_item, 'quantity', 1)
                        # Calculate discount price
                        original_price = product.price
                        discount = getattr(product, 'discount', 0) or 0
                        discount_price = round(
                            original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                        total_amount = discount_price * qty

            fulfillment_msg = f"""🏪 **In-Store Pickup Confirmed!**

Order ID: {order_id}
Product: {product.product_name if product else product_id}
Quantity: {qty}
Total Amount: ₹{total_amount:.2f}
Pickup Store: {store_name}
Store Address: {store_address}
Status: Ready for pickup now

Please show this Order ID at the store counter to collect your items.

Thank you for shopping with us! 🛍️"""

    except Exception as e:
        print(f"Error in fulfillment_node: {e}")
        fulfillment_msg = f"""🏪 **In-Store Pickup Confirmed!**

Status: Ready for pickup

Please show your order details at the store counter."""

    return {"messages": [AIMessage(content=fulfillment_msg)], "fulfillment_done": True}

# ============ Node 4: Loyalty Agent ============


def loyalty_node(state: KioskState):
    order_id = state.get("order_id")
    product_id = state.get("product_id")
    customer_id = state["customer_id"]
    all_orders = state.get("all_orders", [])

    # Validate required data
    if not order_id or not product_id:
        print(f"[ERROR] loyalty_node: Missing order_id or product_id")
        return {"messages": [AIMessage(content="✅ Thank you for your purchase!")], "loyalty_done": True}

    try:
        from intelligent_agent_graph import get_product_by_id
        from crud import CustomerCRUD

        with get_db_session() as session:
            # Calculate total loyalty points for all items
            total_points_earned = 0

            # Process all orders if paying for all, otherwise just the selected one
            orders_to_process = all_orders if all_orders else [
                {"order_id": order_id, "product_id": product_id}]

            for order_data in orders_to_process:
                curr_order_id = order_data["order_id"]
                curr_product_id = order_data["product_id"]

                # Get product and cart item for loyalty calculation
                product = get_product_by_id(curr_product_id)
                cart_item = cart_crud.get_by_id(session, curr_order_id)

                if product and cart_item:
                    qty = getattr(cart_item, 'quantity', 1)
                    # Calculate loyalty points from product.loyalty_points field
                    product_loyalty_points = getattr(
                        product, 'loyalty_points', 0) or 0
                    points_earned = product_loyalty_points * qty
                    total_points_earned += points_earned

            # Update customer loyalty points
            if total_points_earned > 0:
                customer = CustomerCRUD.get_by_id(session, customer_id)
                if customer:
                    current_points = getattr(customer, 'loyalty_points', 0)
                    customer.loyalty_points = current_points + total_points_earned
                    session.commit()

                    loyalty_msg = f"""🎁 **Loyalty Points Earned!**

Points Earned: {total_points_earned}
Total Points: {customer.loyalty_points}

Keep shopping to earn more rewards!"""
                else:
                    loyalty_msg = f"""🎁 **Loyalty Points Earned!**

Points Earned: {total_points_earned}

Thank you for your purchase!"""
            else:
                loyalty_msg = "✅ Thank you for your purchase!"

    except Exception as e:
        print(f"Error in loyalty_node: {e}")
        loyalty_msg = "✅ Thank you for your purchase!"

    return {"messages": [AIMessage(content=loyalty_msg)], "loyalty_done": True}

# ============ Node 5: Post-Purchase Agent ============


def post_purchase_node(state: KioskState):
    order_id = state.get("order_id")
    product_id = state.get("product_id")
    customer_id = state["customer_id"]
    all_orders = state.get("all_orders", [])

    # Validate required data
    if not order_id or not product_id:
        print(f"[ERROR] post_purchase_node: Missing order_id or product_id")
        return {"messages": [AIMessage(content="📧 Thank you for visiting! Have a great day! 🎉")], "post_purchase_done": True}

    # Generate post-purchase message
    try:
        from intelligent_agent_graph import get_product_by_id

        if all_orders:
            # Multiple items processed
            post_msg = f"""📧 **Orders Complete!**

Thank you for your purchase! All {len(all_orders)} items have been successfully processed.

📝 We'd love to hear your feedback. Please rate your experience at the store.

🔔 You'll receive updates about new products and exclusive offers.

Have a great day! 🎉"""
        else:
            # Single item processed
            product = get_product_by_id(product_id)
            product_name = product.product_name if product else "your purchase"

            post_msg = f"""📧 **Order Complete!**

Thank you for your purchase! Your order {order_id} has been successfully processed.

We hope you enjoy {product_name}!

📝 We'd love to hear your feedback. Please rate your experience at the store.

🔔 You'll receive updates about new products and exclusive offers.

Have a great day! 🎉"""
    except Exception as e:
        print(f"Error generating post-purchase message: {e}")
        post_msg = f"""📧 **Order Complete!**

Thank you for your purchase!

Have a great day! 🎉"""

    # === DB operations after post-purchase agent ===
    try:
        from crud import CartCRUD, OrderHistoryCRUD, StoreKeeperTransactionCRUD, ProductCRUD, StoreCRUD, CustomerCRUD
        from models import OrderHistory, StoreKeeperTransaction
        from database import get_db_session
        import datetime

        # Process all orders if paying for all, otherwise just the selected one
        orders_to_process = all_orders if all_orders else [
            {"order_id": order_id, "product_id": product_id, "store_id": state.get("store_id")}]

        with get_db_session() as session:
            for order_data in orders_to_process:
                curr_order_id = order_data["order_id"]
                curr_product_id = order_data["product_id"]
                curr_store_id = order_data.get("store_id")

                print(
                    f"[DEBUG] post_purchase_node: order_id={curr_order_id}, product_id={curr_product_id}, customer_id={customer_id}, store_id={curr_store_id}")

                print("[DEBUG] Fetching product, customer, store from DB...")
                product = ProductCRUD.get_by_id(session, curr_product_id)
                customer = CustomerCRUD.get_by_id(session, customer_id)
                store = StoreCRUD.get_by_id(
                    session, curr_store_id) if curr_store_id else None
                cart_item = CartCRUD.get_by_id(session, curr_order_id)
                print(f"[DEBUG] Product: {product}")
                print(f"[DEBUG] Customer: {customer}")
                print(f"[DEBUG] Store: {store}")
                print(f"[DEBUG] Cart Item: {cart_item}")

                # Only proceed if product and customer exist
                if product and customer and cart_item:
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    qty = getattr(cart_item, 'quantity', 1)
                    size = getattr(cart_item, 'size', None)

                    # Calculate discount price (same logic as welcome_node / fulfillment_node)
                    original_price = product.price
                    discount = getattr(product, 'discount', 0) or 0
                    discount_price = round(
                        original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                    item_discounted_total = round(discount_price * qty)
                    item_discount_amount = round(
                        (original_price * qty) - item_discounted_total, 2)
                    # Kiosk flow does not apply loyalty points
                    final_price = item_discounted_total

                    print("[DEBUG] Creating OrderHistory record...")
                    order_history = OrderHistory(
                        transaction_id=curr_order_id,
                        customer_id=customer_id,
                        customer_name=customer.customer_name,
                        product_id=curr_product_id,
                        product_name=product.product_name,
                        quantity=qty,
                        size=size,
                        order_dates=now,
                        loyalty_points=getattr(customer, 'loyalty_points', 0),
                        discount_amount=item_discount_amount,
                        loyalty_applied=0,
                        final_price=final_price
                    )
                    OrderHistoryCRUD.create(session, order_history)
                    print("[DEBUG] OrderHistory record created.")

                    print("[DEBUG] Creating StoreKeeperTransaction record...")
                    store_keeper_txn = StoreKeeperTransaction(
                        customer_id=customer_id,
                        product_id=curr_product_id,
                        date=now,
                        user_name=customer.customer_name,
                        product=product.product_name,
                        qty=qty,
                        size=size,
                        mode="Offline",
                        store_name=store.store_name if store else "",
                        store_id=curr_store_id,
                        status="Complete",
                        amount=final_price,
                        address=getattr(customer, 'address', ""),
                        phone=getattr(customer, 'phone', "")
                    )
                    StoreKeeperTransactionCRUD.create(
                        session, store_keeper_txn)
                    print("[DEBUG] StoreKeeperTransaction record created.")
                    session.flush()  # Ensure ORM flushes inserts before delete
                else:
                    print(
                        f"[ERROR] Product, Customer, or Cart Item not found for order_id: {curr_order_id}")

                # Remove from cart after all details fetched
                if cart_item:
                    print(
                        f"[DEBUG] Deleting cart entry with order_id: {curr_order_id}")
                    CartCRUD.delete(session, curr_order_id)
                    print(
                        f"[DEBUG] Cart entry deleted for order_id: {curr_order_id}")

            session.commit()  # Commit all changes
            print(f"[DEBUG] DB commit successful for all orders")
    except Exception as e:
        import traceback
        print(f"[ERROR] Post-purchase DB operations failed: {e}")
        traceback.print_exc()

    return {"messages": [AIMessage(content=post_msg)], "post_purchase_done": True}

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

        # Step 2: Wait for user to select order number
        user = input("\nYou: ")
        state["messages"].append(HumanMessage(content=user))
        result = payment_prompt_node(state)
        msgs = result.get("messages", [])
        for msg in msgs:
            if isinstance(msg, ToolMessage):
                print(f"\n🔧: {msg.content[:400]}...")
            elif isinstance(msg, AIMessage):
                print(f"\n🤖: {msg.content}")
        # Update state with all returned values
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
