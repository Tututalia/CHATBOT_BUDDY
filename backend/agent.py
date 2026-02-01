"""
Intelligent Sales Agent System using LangGraph
LLM decides which agent tools to call based on user query
"""

from unittest import result
from crud import (
    product_crud, store_crud, customer_crud, order_history_crud,
    ProductCRUD, StoreCRUD, CustomerCRUD, OrderHistoryCRUD, cart_crud,
    store_keeper_transaction_crud, admin_dashboard_data_crud
)
from models import Product, Store, Customer, OrderHistory, Cart
from database import engine, get_db_session
from typing import TypedDict, Annotated, List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
import json
import random
from datetime import datetime
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and CRUD modules


# ============ State Definition ============
class AgentState(TypedDict):
    """State for the agent workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    customer_id: str
    selected_product: Dict[str, Any] | None
    inventory_status: str | None
    purchase_channel: str | None  # "online" or "offline"
    order_id: str | None
    payment_completed: bool
    loyalty_points: int


# ============ Agent Tools ============

def load_products_from_db(
    category: str = None,
    gender: str = None,
    season: str = None,
    max_price: float = None,
    search_query: str = None
) -> List[Product]:
    """
    Load product data from database with optional filters

    Args:
        category: Filter by category
        gender: Filter by gender
        season: Filter by season
        max_price: Filter by maximum price
        search_query: Search in product name, category, etc.

    Returns:
        List of Product objects from database
    """
    try:
        with get_db_session() as session:
            # Build filters
            filters = {}
            operators = {}

            if category:
                filters['category'] = category.lower()
                operators['category'] = 'contains'
            if gender:
                filters['gender'] = gender
            if season:
                filters['season'] = season
                operators['season'] = 'contains'

            # Get products with filters
            if filters:
                products = product_crud.filter(
                    session, filters, operators, limit=100)
            else:
                products = product_crud.get_all(session, limit=100)

            # Apply max_price filter if specified
            if max_price is not None:
                products = [p for p in products if p.price <= max_price]

            # Apply search query if specified (search across multiple fields)
            if search_query:
                query_lower = search_query.lower()
                keywords = query_lower.split()
                filtered = []
                for p in products:
                    match = False
                    for keyword in keywords:
                        if (keyword in p.product_name.lower() or
                            keyword in p.category.lower() or
                            keyword in p.season.lower() or
                            keyword in p.gender.lower() or
                                (p.festival and keyword in p.festival.lower())):
                            match = True
                            break
                    if match:
                        filtered.append(p)
                products = filtered if filtered else products

            return products
    except Exception as e:
        print(f"Error loading products from database: {e}")
        return []


def get_product_by_id(product_id: str) -> Product:
    """Get a single product by ID from database"""
    try:
        with get_db_session() as session:
            return product_crud.get_by_id(session, product_id)
    except Exception as e:
        print(f"Error getting product {product_id}: {e}")
        return None


def deduct_product_quantity(product_id: str, quantity: int = 1) -> bool:
    """
    Deduct quantity from a product after successful purchase.

    Args:
        product_id: The product ID to update
        quantity: Number of units to deduct (default: 1)

    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_session() as session:
            product = product_crud.get_by_id(session, product_id)
            if product:
                new_quantity = max(0, product.quantity - quantity)
                product_crud.update(session, product_id, {
                                    "quantity": new_quantity})
                print(
                    f"✅ Deducted {quantity} unit(s) from {product.product_name}. New quantity: {new_quantity}")
                return True
            return False
    except Exception as e:
        print(f"Error deducting quantity for product {product_id}: {e}")
        return False


def get_store_by_id(store_id: str) -> Store:
    """Get a single store by ID from database"""
    try:
        with get_db_session() as session:
            return store_crud.get_by_id(session, store_id)
    except Exception as e:
        print(f"Error getting store {store_id}: {e}")
        return None


def get_all_stores() -> List[Store]:
    """Get all stores from database"""
    try:
        with get_db_session() as session:
            return store_crud.get_all(session, limit=100)
    except Exception as e:
        print(f"Error getting stores: {e}")
        return []


def get_customer_by_id(customer_id: str) -> Customer:
    """Get a customer by ID from database"""
    try:
        with get_db_session() as session:
            return customer_crud.get_by_id(session, customer_id)
    except Exception as e:
        print(f"Error getting customer {customer_id}: {e}")
        return None


def get_customer_orders(customer_id: str) -> List[OrderHistory]:
    """Get order history for a customer from database"""
    try:
        with get_db_session() as session:
            return order_history_crud.filter(session, {'customer_id': customer_id})
    except Exception as e:
        print(f"Error getting orders for customer {customer_id}: {e}")
        return []


@tool
def customer_info_agent(customer_id: str, info_type: str = "profile") -> str:
    """
    Fetches customer information from the database.
    Use this when user asks about their profile, orders, address, contact info, or loyalty points.

    Args:
        customer_id: The customer ID
        info_type: Type of info to fetch - "profile" (name, address, phone, loyalty points) 
                   or "orders" (order history)

    Returns:
        Customer information formatted as text
    """
    try:
        customer = get_customer_by_id(customer_id)

        if not customer:
            return f"❌ Customer with ID {customer_id} not found in database."

        if info_type == "orders":
            # Get order history
            orders = get_customer_orders(customer_id)

            if not orders:
                return f"📦 **Order History for {customer.customer_name}:**\n\nYou haven't placed any orders yet. Would you like to browse our products?"

            result = f"📦 **Order History for {customer.customer_name}:**\n\n"
            for order in orders[:5]:  # Show last 5 orders
                result += f"- **{order.product_name}** (ID: {order.product_id})\n"
                result += f"  Transaction ID: {order.transaction_id}\n"
                result += f"  Quantity: {order.quantity} | Date: {order.order_dates}\n"
                result += f"  Loyalty Points Earned: {order.loyalty_points}\n\n"

            if len(orders) > 5:
                result += f"...and {len(orders) - 5} more orders.\n\n"

            result += "Would you like to reorder any item or browse new products?"
            return result

        else:  # profile info
            result = f"👤 **Customer Profile:**\n\n"
            result += f"**Name:** {customer.customer_name}\n"
            result += f"**Customer ID:** {customer.customer_id}\n"
            result += f"**Phone:** {customer.phone}\n"
            result += f"**Address:** {customer.address}\n"
            result += f"**Loyalty Points:** {customer.loyalty_points} points 🎁\n\n"

            # Count orders
            orders = get_customer_orders(customer_id)
            result += f"**Total Orders:** {len(orders)}\n\n"

            result += "How can I assist you today?"
            return result

    except Exception as e:
        return f"❌ Error fetching customer information: {str(e)}"


@tool
def recommendation_agent(query: str) -> str:
    """
    Shows product recommendations based on user query.
    Use this when user asks for products, recommendations, or wants to browse items.

    Args:
        query: User's product search query

    Returns:
        List of recommended products
    """
    # Load products from database with search
    products = load_products_from_db(search_query=query)

    if not products:
        # If no matches, get all products and show random sample
        all_products = load_products_from_db()
        if not all_products:
            return json.dumps({
                "name": "Recommendation Agent",
                "id": "recommendation_agent",
                "responses": {
                    "default": "❌ Failed to load product database. Please try again.",
                    "recommendation": []
                }
            })
        products = random.sample(all_products, min(4, len(all_products)))
    else:
        products = products[:4]  # Limit to 4 products

    # Build recommendation list
    recommendations = []
    for product in products:
        recommendations.append({
            "product_name": product.product_name,
            "price": int(product.price),
            # Placeholder logic
            "image": f"/images/{product.product_name.replace(' ', '_').lower()}.avif",
            "description": f"Recommended {product.category} for you.",
            "sku": product.product_id
        })

    # Default message (can be improved with context)
    default_msg = f"I recommend these {products[0].category if products else 'products'} based on your preferences. {products[0].product_name if products else ''} is ₹{int(products[0].price) if products else ''} and trending — want me to check availability?"

    response_obj = {
        "name": "Recommendation Agent",
        "id": "recommendation_agent",
        "responses": {
            "default": default_msg,
            "recommendation": recommendations
        }
    }
    print(json.dumps(response_obj, indent=2))
    return json.dumps(response_obj)


@tool
def inventory_agent(product_id: str) -> str:
    """
    Checks if a product is available in inventory and shows buying options.
    Use this when user selects a product or asks about availability.
    If quantity is 0, suggests similar products using the recommendation agent.

    Args:
        product_id: The product ID to check (e.g., P001)

    Returns:
        Availability status and purchase options (online/offline) with store locations
    """
    # Load product from database
    product = get_product_by_id(product_id)

    if product is None:
        return f"❌ Product {product_id} not found. Please check the product ID and try again."

    # Check quantity first - if 0, product is out of stock
    if product.quantity <= 0:
        result = f"❌ **Sorry, {product.product_name} (ID: {product_id}) is OUT OF STOCK**\n\n"
        result += f"Current stock: 0 units\n\n"

        # Find similar products in the same category
        similar_products = load_products_from_db(
            category=product.category,
            gender=product.gender if product.gender else None
        )

        # Filter out the current product and products with 0 quantity
        similar_products = [p for p in similar_products
                            if p.product_id != product_id and p.quantity > 0]

        if similar_products:
            # Limit to top 4 similar products
            similar_products = similar_products[:4]
            result += "🔄 **Similar Products You Might Like:**\n\n"
            for p in similar_products:
                result += f"- **{p.product_name}** (ID: {p.product_id})\n"
                result += f"  Price: ₹{int(p.price):,} | In Stock: {p.quantity} units\n\n"
            result += "\nWould you like to select any of these alternatives?"
        else:
            result += "Unfortunately, no similar products are currently available.\n"
            result += "Would you like to browse other categories?"

        return result

    # Check availability channels
    online_available = str(product.online_available).lower() == 'yes'
    offline_available = str(product.offline_available).lower() == 'yes'

    if not online_available and not offline_available:
        result = f"❌ **Sorry, Product {product_id} is currently unavailable for purchase**\n"
        result += "Would you like to see alternative products?"
        return result

    result = f"✅ **Product {product_id} is IN STOCK!**\n\n"
    result += f"**{product.product_name}** - ₹{int(product.price):,}\n"
    result += f"**Available Quantity:** {product.quantity} units\n\n"
    result += "📦 **Purchase Options:**\n\n"

    if online_available:
        result += "1. 🌐 **Online** - Get it delivered to your home\n\n"

    if offline_available:
        result += "2. 🏪 **Offline** - Pick up from nearest store\n\n"
        result += "📍 **Available Stores for Pickup:**\n\n"

        # Get stores from database based on product's store_ids
        if product.store_ids:
            store_ids = [s.strip() for s in product.store_ids.split(';')]
            for i, store_id in enumerate(store_ids[:4], 1):
                store = get_store_by_id(store_id)
                if store:
                    result += f"   • **{store.store_name}** (ID: {store.store_id})\n"
                    result += f"     {store.address} - {random.uniform(2.0, 8.0):.1f} km away\n\n"
                else:
                    result += f"   • **Store {store_id}** - {random.uniform(2.0, 8.0):.1f} km away\n\n"
        elif product.offline_stores:
            # Fallback to offline_stores string if store_ids not available
            stores = [store.strip()
                      for store in product.offline_stores.split(';')]
            for i, store_name in enumerate(stores[:4], 1):
                result += f"   • **{store_name}** (ID: S{i:03d})\n"
                result += f"     {random.choice(['123 Main St', '456 West Ave', '789 Airport Rd', '321 Center Blvd'])} - {random.uniform(2.0, 8.0):.1f} km away\n\n"

    result += "\n**How would you like to proceed?**\n"
    result += "- Type 'online' to buy online with home delivery\n"
    if offline_available:
        result += "- To pick up from a store, reply with the store ID (e.g., STR016) or type 'offline'\n"
    return result


@tool
def payment_agent(product_id: str, payment_method: str = "", customer_id: str = None) -> str:
    """
    Shows available payment methods and processes online payment for the selected product.
    Use this when user chooses online purchase option.

    Args:
        product_id: The product ID being purchased
        payment_method: Payment method selected by user (upi, credit card, debit card, net banking). 
                       Leave empty to show available payment methods.

    Returns:
        Payment options (if method not provided) or payment confirmation details
    """
    # Get product from database to get actual price
    product = get_product_by_id(product_id)
    product_name = product.product_name if product else f"Product {product_id}"
    amount = int(product.price) if product else random.choice(
        [1299, 1999, 2499, 4999])

    # If no payment method specified, just show available methods.
    # For online purchase, create a pending cart entry automatically (not as a tool call).
    if not payment_method:
        try:
            with get_db_session() as session:
                # Avoid duplicate pending entries for same customer/product
                existing = None
                if customer_id:
                    existing_list = cart_crud.filter(session, filters={"customer_id": customer_id, "product_id": product_id, "channel": "online", "status": "pending"}, operators={
                                                     "customer_id": "==", "product_id": "==", "channel": "==", "status": "=="}, limit=1, order_by="created_at", order_desc=True)
                    existing = existing_list[0] if existing_list else None

                if not existing:
                    # Determine a valid store_id to satisfy FK constraints.
                    store_id_val = None
                    try:
                        prod = product_crud.get_by_id(session, product_id)
                        if prod and getattr(prod, "store_ids", None):
                            ids = [s.strip()
                                   for s in prod.store_ids.split(";") if s.strip()]
                            if ids:
                                store_id_val = ids[0]
                        if not store_id_val:
                            stores = store_crud.get_all(session, limit=1)
                            if stores:
                                store_id_val = stores[0].store_id
                    except Exception:
                        store_id_val = None

                    cart_data = {
                        "order_id": f"ORD{random.randint(100000, 999999)}",
                        "customer_id": customer_id,
                        "product_id": product_id,
                        "store_id": store_id_val,
                        "channel": "online",
                        "status": "pending",
                        "created_at": datetime.utcnow().isoformat()
                    }
                    cart_crud.create(session, cart_data)
        except Exception as e:
            print(f"Error creating pending cart (online): {e}")

        result = f"💳 **Payment Methods for {product_name}:**\n\n"
        result += f"Amount: ₹{amount:,}\n\n"
        result += "Please choose your preferred payment method:\n\n"
        result += "1. 📱 **UPI** - Pay using any UPI app (Google Pay, PhonePe, Paytm, etc.)\n"
        result += "2. 💳 **Credit Card** - Visa, Mastercard, American Express, etc.\n"
        result += "3. 💳 **Debit Card** - All major banks supported\n"
        result += "4. 🏦 **Net Banking** - Direct bank transfer\n\n"
        result += "Which payment method would you like to use?"
        return result

    # Process payment with selected method
    payment_id = f"PAY{random.randint(10000, 99999)}"

    result = f"💳 **Processing Payment...**\n\n"
    result += f"Product: {product_name}\n"
    result += f"Product ID: {product_id}\n"
    result += f"Amount: ₹{amount:,}\n"
    result += f"Method: {payment_method.upper()}\n"
    result += f"Payment ID: {payment_id}\n\n"
    result += "✅ **Payment Successful!**\n"

    # On successful payment, remove the pending online cart entry and add to order_history and store_keeper_transaction
    try:
        with get_db_session() as session:
            pending = None
            if customer_id:
                pending_list = cart_crud.filter(session, filters={"customer_id": customer_id, "product_id": product_id, "channel": "online", "status": "pending"}, operators={
                                                "customer_id": "==", "product_id": "==", "channel": "==", "status": "=="}, limit=1, order_by="created_at", order_desc=True)
                pending = pending_list[0] if pending_list else None

            if pending:
                try:
                    cart_crud.delete(session, pending.order_id)
                except Exception as e:
                    print(f"Warning: failed to delete pending cart: {e}")
                transaction_id = pending.order_id
            else:
                transaction_id = f"TRX{random.randint(100000, 999999)}"

            # Add to order_history
            try:
                customer = customer_crud.get_by_id(
                    session, customer_id) if customer_id else None
                customer_name = customer.customer_name if customer else ''
                prod = product
                loyalty_pts = prod.loyalty_points if prod and getattr(
                    prod, 'loyalty_points', None) else 0

                order_record = {
                    "transaction_id": transaction_id,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "product_id": product_id,
                    "product_name": product_name,
                    "quantity": 1,
                    "order_dates": datetime.utcnow().isoformat(),
                    "loyalty_points": loyalty_pts
                }
                order_history_crud.create(session, order_record)
            except Exception as e:
                print(f"Warning: failed to create order_history record: {e}")

            # Add to store_keeper_transaction
            try:
                tx_id = int(time.time() * 1000) % 100000000
                store_tx = {
                    "id": tx_id,
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "date": datetime.utcnow().isoformat(),
                    "user_name": customer.customer_name if customer else '',
                    "product": product_name,
                    "qty": 1,
                    "mode": "Online",
                    "store_name": "Online",
                    "store_id": None,
                    "status": "Complete",
                    "amount": float(amount),
                    "address": customer.address if customer else '',
                    "phone": customer.phone if customer else ''
                }
                # Prefer store_id from pending cart if available
                try:
                    if pending and getattr(pending, 'store_id', None):
                        store_tx['store_id'] = pending.store_id
                    else:
                        stores = store_crud.get_all(session, limit=1)
                        if stores:
                            store_tx['store_id'] = stores[0].store_id
                except Exception:
                    pass
                try:
                    store_keeper_transaction_crud.create(session, store_tx)
                except IntegrityError as ie:
                    print(
                        f"IntegrityError inserting store_keeper_transaction: {ie}")
                    try:
                        session.rollback()
                    except Exception:
                        pass
                    try:
                        stores = store_crud.get_all(session, limit=1)
                        fallback_store_id = stores[0].store_id if stores else None
                        if fallback_store_id:
                            store_tx["store_id"] = fallback_store_id
                        with get_db_session() as retry_sess:
                            store_keeper_transaction_crud.create(
                                retry_sess, store_tx)
                    except Exception as e:
                        print(
                            f"Warning: failed to create store_keeper_transaction after fallback: {e}")
                except Exception as e:
                    print(
                        f"Warning: failed to create store_keeper_transaction: {e}")
            except Exception as e:
                print(
                    f"Warning: failed to prepare store_keeper_transaction: {e}")

    except Exception as e:
        print(f"Warning during payment post-processing: {e}")

    result += "Your order is being processed..."

    return result


@tool
def fulfillment_agent(product_id: str, purchase_type: str = "online", store_name: str = "", customer_id: str = None, order_id: str = None) -> str:
    """
    Handles order fulfillment - delivery for online, store pickup for offline.
    For ONLINE: Call this after payment is complete.
    For OFFLINE: Call this ONLY after user has explicitly selected a store. The store_name parameter is REQUIRED for offline.

    IMPORTANT: For offline purchases, the LLM must first ask the user to select a specific store from the available options
    shown by inventory_agent. Do NOT call this tool until user provides the store name.

    Args:
        product_id: The product ID being fulfilled
        purchase_type: Either 'online' or 'offline'
        store_name: Name of the selected store (REQUIRED for offline, leave empty for online)

    Returns:
        Fulfillment details and order tracking info
    """
    if not order_id:
        order_id = f"ORD{random.randint(100000, 999999)}"

    # Get product details from database
    product = get_product_by_id(product_id)
    product_name = product.product_name if product else f"Product {product_id}"
    product_price = int(product.price) if product else 0

    # Deduct quantity from inventory after successful order
    deduct_product_quantity(product_id, quantity=1)

    if purchase_type.lower() == "online":
        # Add delay for online purchases before showing fulfillment
        print("⏳ Confirming your order...")
        time.sleep(2.5)

        delivery_date = "3-5 business days"
        result = f"📦 **Order Confirmed!**\n\n"
        # Use provided order_id (from pending cart created at selection time)
        result += f"Order ID: {order_id}\n"
        result += f"Product: {product_name} ({product_id})\n"
        result += f"Amount: ₹{product_price:,}\n"
        result += f"Delivery Type: Home Delivery\n"
        result += f"Expected Delivery: {delivery_date}\n\n"
        result += "You can track your order with the Order ID.\n\n"
        # NOTE: Do NOT create a cart record here for online flows.
        # The pending cart entry should already have been created when the user selected the ONLINE option
        # (payment phase). After payment completes, this tool is called to finalize fulfillment.
        # Instruction for LLM to automatically call loyalty_agent using the current `order_id`
        result += f"[SYSTEM: Now call loyalty_agent with order_id='{order_id}' and product_id='{product_id}' to award loyalty rewards automatically]"
    else:
        # Offline purchase
        if not store_name or store_name == "Store":
            # If no store selected yet, prompt user to select
            return "⚠️ Please select a specific store from the available options above for pickup. Which store would you like to visit?"

        # Try to get store details from database
        store_details = None
        all_stores = get_all_stores()
        for store in all_stores:
            if store_name.lower() in store.store_name.lower() or store_name == store.store_id:
                store_details = store
                break

        store_display_name = store_details.store_name if store_details else store_name
        store_address = store_details.address if store_details else "Please check store location"

        # Create cart record for offline pickup (channel=offline, status=pending)
        try:
            with get_db_session() as session:
                cart_data = {
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "store_id": store_details.store_id if store_details else None,
                    "channel": "offline",
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat()
                }
                cart_crud.create(session, cart_data)
        except Exception as e:
            print(
                f"Warning: failed to create cart record for offline order {order_id}: {e}")

        result = f"🏪 **In-Store Pickup Confirmed!**\n\n"
        result += f"Order ID: {order_id}\n"
        result += f"Product: {product_name} ({product_id})\n"
        result += f"Amount: ₹{product_price:,}\n"
        result += f"Pickup Store: {store_display_name}\n"
        result += f"Store Address: {store_address}\n"
        result += f"Status: Ready for pickup in 2 hours\n\n"
        result += "Please visit the store to complete your purchase.\n"
        result += "💡 Show this Order ID at the store kiosk.\n\n"
        result += "Thank you for choosing us! Have a great day! 🛍️\n\n"
        # Signal to end conversation for offline purchases
        result += "[SYSTEM: CONVERSATION_COMPLETE - This is an offline store pickup. The session will be transferred to the in-store kiosk. Do NOT respond further or accept new queries. End the conversation now.]"

    return result


@tool
def loyalty_agent(order_id: str, product_id: str) -> str:
    """
    Awards loyalty points and provides coupon codes after successful order.
    Use this after fulfillment is complete (online purchases only).
    After awarding loyalty points, AUTOMATICALLY call post_purchase_agent with the same order_id.

    Args:
        order_id: The order ID to award points for
        product_id: The product ID to fetch loyalty points from

    Returns:
        Loyalty points earned and coupon codes
    """
    # Add 2-3 seconds delay before showing loyalty rewards
    print("⏳ Calculating your rewards...")
    time.sleep(2.5)

    # Fetch product from database to get actual loyalty points
    product = get_product_by_id(product_id)

    # Use actual loyalty points from product database
    points = product.loyalty_points if product and product.loyalty_points else random.randint(
        50, 200)

    coupon_codes = [
        {"code": f"SAVE{random.randint(10, 50)}", "discount": "10% off"},
        {"code": f"WELCOME{random.randint(100, 999)}", "discount": "₹100 off"},
    ]

    result = f"🎉 **Loyalty Rewards Unlocked!**\n\n"
    result += f"Order ID: {order_id}\n"
    result += f"Points Earned: {points} points 🌟\n\n"
    result += "**Coupon Codes for Next Purchase:**\n"
    for coupon in coupon_codes:
        result += f"- Code: `{coupon['code']}` - {coupon['discount']}\n"

    result += "\nThank you for shopping with us!\n\n"
    # Instruction for LLM to automatically call post_purchase_agent
    result += f"[SYSTEM: Now call post_purchase_agent with order_id='{order_id}' to show post-purchase services automatically]"
    return result


@tool
def post_purchase_agent(order_id: str) -> str:
    """
    Provides post-purchase services like feedback, support, and order tracking.
    Use this as the final step after loyalty rewards (online flow).

    Args:
        order_id: The order ID for post-purchase services

    Returns:
        Feedback link and support information
    """
    # Add 2-3 seconds delay before showing post-purchase services
    print("⏳ Processing your request...")
    time.sleep(2.5)

    result = f"📝 **Post-Purchase Services**\n\n"
    result += f"Order ID: {order_id}\n\n"
    result += "**Available Services:**\n"
    result += "- 📊 Track Order: https://example.com/track/" + order_id + "\n"
    result += "- ⭐ Leave Feedback: https://example.com/feedback\n"
    result += "- 💬 Customer Support: support@example.com\n"
    result += "- 🔄 Return/Exchange: Available within 7 days\n\n"
    result += "We'd love to hear your feedback! Please rate your experience."

    return result


# ============ Agent Tools List ============
tools = [
    customer_info_agent,
    recommendation_agent,
    inventory_agent,
    payment_agent,
    fulfillment_agent,
    loyalty_agent,
    post_purchase_agent
]


# ============ LLM Configuration ============
def create_llm():
    """Create OpenAI GPT-4 mini LLM"""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        streaming=True
    )


# ============ Agent Node ============
def agent_node(state: AgentState):
    """
    Main agent node that uses LLM to decide which tools to call
    The LLM intelligently chooses tools based on conversation context
    """
    llm = create_llm()
    llm_with_tools = llm.bind_tools(tools)

    # Always add system message with customer context at the beginning
    from langchain_core.messages import SystemMessage
    customer_id = state.get("customer_id", "UNKNOWN")
    system_message = SystemMessage(
        content=f"""
You are a helpful, proactive AI shopping assistant for an e-commerce platform.

CRITICAL INSTRUCTIONS (STRICT):

1. TOOL USAGE IS MANDATORY:
    - You MUST ALWAYS use the available agent tools for every user request related to product recommendations, inventory/availability, payment, fulfillment, loyalty, and post-purchase information.
    - NEVER generate product lists, availability, payment, order, or fulfillment responses yourself. ALWAYS call the appropriate tool for each action.

2. INVENTORY CHECKS:
    - For ANY purchase intent (e.g., "I want to buy", "buy online", "add to cart", "purchase", "order now", etc.) or when a product is selected, you MUST call `inventory_agent` FIRST to check stock, availability, and purchase options—even if the product seems obvious from context.
    - If the product is NOT explicitly mentioned in the user's message, you MUST clarify or confirm the product with the user before calling `inventory_agent`.

3. PRODUCT RECOMMENDATIONS:
    - Use `recommendation_agent` for any product suggestions, browsing, or when the user asks for options.

4. PAYMENT FLOWS:
    - Use `payment_agent` for ALL payment-related actions. Do NOT describe payment steps yourself.

5. ORDER FULFILLMENT:
    - Use `fulfillment_agent` for delivery (online) or store pickup (offline). For offline, ensure the user has selected a specific store before calling the tool.
    - When calling `fulfillment_agent`, you MUST pass `customer_id` as the current customer id ({customer_id}).

6. LOYALTY & POST-PURCHASE:
    - Use `loyalty_agent` after fulfillment to award points and coupons.
    - Use `post_purchase_agent` after loyalty rewards for feedback, support, and tracking.

7. CLARIFY & CONFIRM:
    - If any required information (product, payment method, store, etc.) is missing or ambiguous, ASK the user to clarify before proceeding with tool calls.

8. RESPONSE QUALITY:
    - Be friendly, concise, and proactive. Guide the user through each step, always using the tools for information and actions.
    - Do NOT make assumptions—always confirm details if not explicit.

9. EXAMPLES:
    - If user says "I want to buy online" but does not specify the product, ask "Which product would you like to buy?" before calling `inventory_agent`.
    - If user says "Show me hoodies", call `recommendation_agent`.
    - If user says "Is this in stock?", call `inventory_agent` for the referenced product.
    - If user says "Proceed to payment", call `payment_agent`.

You must strictly follow these instructions for every user query. Do NOT skip tool calls or generate information yourself.
"""
    )

    # Prepend system message to all messages
    messages = [system_message] + state["messages"]

    # Removed heuristic that injected inventory info as a SystemMessage.

    # Call LLM with tools
    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response]
    }


# ============ Tool Executor Node ============
def tool_node(state: AgentState):
    """
    Executes the tools that the LLM decided to call
    """
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = _execute_tool(tool_call)
        outputs.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"]
            )
        )
    return {"messages": outputs}


def _execute_tool(tool_call: dict) -> str:
    """Helper function to execute a single tool"""
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    # Find and execute the tool
    for tool in tools:
        if tool.name == tool_name:
            return tool.invoke(tool_args)

    return f"Error: Tool {tool_name} not found"


# ============ Routing Logic ============
def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Determines whether to continue to tools or end the conversation
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If LLM makes tool calls, route to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise end the conversation
    return "__end__"


# ============ Build Graph ============
def create_agent_graph():
    """
    Create the LangGraph StateGraph for intelligent agent system
    """
    # Initialize graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)  # LLM decides which tools to call
    workflow.add_node("tools", tool_node)  # Executes the tools

    # Add edges
    workflow.add_edge(START, "agent")  # Start with agent

    # Conditional edge: agent decides to call tools or end
    workflow.add_conditional_edges(
        "agent",
        should_continue,  # Our custom routing function
        {
            "tools": "tools",
            "__end__": END
        }
    )

    # After tools execute, go back to agent to process results
    workflow.add_edge("tools", "agent")

    # Compile graph
    graph = workflow.compile()

    return graph


# ============ Visualization ============
def visualize_graph():
    """Print the graph structure"""
    graph = create_agent_graph()

    print("\n" + "="*60)
    print("INTELLIGENT SALES AGENT GRAPH STRUCTURE")
    print("="*60)
    print("\nGraph Flow:")
    print("  START")
    print("    ↓")
    print("  [AGENT NODE]")
    print("    ↓")
    print("  LLM decides: Call tools OR End conversation")
    print("    ↓")
    print("  [TOOLS NODE] (if tools needed)")
    print("    ↓")
    print("  Back to [AGENT NODE] (process tool results)")
    print("    ↓")
    print("  Loop continues until conversation ends")
    print("    ↓")
    print("  END")

    print("\n" + "="*60)
    print("AVAILABLE AGENT TOOLS (LLM calls as needed)")
    print("="*60)
    print("\n1. customer_info_agent")
    print("   → Fetches customer profile and order history")
    print("   → Used when: User asks about their info, orders, or loyalty points")

    print("\n2. recommendation_agent")
    print("   → Shows product recommendations")
    print("   → Used when: User wants to browse/see products")

    print("\n3. inventory_agent")
    print("   → Checks product availability")
    print("   → Shows online/offline purchase options")
    print("   → Used when: User selects a product")

    print("\n4. payment_agent")
    print("   → Processes online payment")
    print("   → Used when: User chooses online purchase")

    print("\n5. fulfillment_agent")
    print("   → Handles order delivery (online) or store pickup (offline)")
    print("   → Used when: After payment OR offline selection")

    print("\n6. loyalty_agent")
    print("   → Awards loyalty points and coupons")
    print("   → Used when: After order fulfillment")

    print("\n7. post_purchase_agent")
    print("   → Sends feedback link and support info")
    print("   → Used when: Final step after loyalty rewards")

    print("\n" + "="*60)
    print("LLM MODEL: OpenAI GPT-4 mini")
    print("="*60)
    print("\nHow it works:")
    print("• User sends a query")
    print("• LLM analyzes the query and conversation history")
    print("• LLM intelligently decides which agent tools to call")
    print("• Tools execute and return results")
    print("• LLM processes results and responds to user")
    print("• Process repeats until conversation naturally ends")
    print("\n" + "="*60 + "\n")

    try:
        # Try to generate visual graph
        from IPython.display import Image, display
        display(Image(graph.get_graph().draw_mermaid_png()))
        print("✓ Graph visualization generated above")
    except Exception as e:
        print(f"Note: Visual graph generation requires additional setup")
        print(f"Graph structure printed in text format above")


# ============ Run Agent ============
async def run_agent(customer_id: str, query: str):
    """
    Run the intelligent agent system

    Args:
        customer_id: Customer ID
        query: User's query

    Returns:
        Final state after agent execution
    """
    graph = create_agent_graph()

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "customer_id": customer_id,
        "selected_product": None,
        "inventory_status": None,
        "purchase_channel": None,
        "order_id": None,
        "payment_completed": False,
        "loyalty_points": 0
    }

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    return final_state


# ============ Main Execution ============
if __name__ == "__main__":
    import asyncio

    # Visualize the graph structure
    visualize_graph()

    # Example usage
    print("\n" + "="*60)
    print("EXAMPLE CONVERSATION")
    print("="*60)

    async def test_conversation():
        # Test query
        result = await run_agent(
            customer_id="CUST001",
            query="Hi! I'm looking for a winter hoodie. Can you show me some options?"
        )

        print("\n📝 Conversation Messages:")
        for msg in result["messages"]:
            if isinstance(msg, HumanMessage):
                print(f"\n👤 User: {msg.content}")
            elif isinstance(msg, AIMessage):
                if msg.content:
                    print(f"\n🤖 Agent: {msg.content}")
            elif isinstance(msg, ToolMessage):
                print(f"\n🔧 Tool Result: {msg.content[:200]}...")

    # Run example
    # asyncio.run(test_conversation())
    print("\nTo run the agent:")
    print("  result = await run_agent('CUST001', 'Show me some hoodies')")
