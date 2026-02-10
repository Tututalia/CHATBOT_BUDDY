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
import re
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
    # Track products added to cart with quantities
    cart_items: List[Dict[str, Any]]


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

            # NOTE: The products table can contain more than 100 rows.
            # If we only load the first page, keyword searches can miss matching items.
            chunk_size = 500
            max_rows = 5000 if search_query else 1000

            products: List[Product] = []
            skip = 0
            while len(products) < max_rows:
                remaining = max_rows - len(products)
                limit = min(chunk_size, remaining)

                if filters:
                    batch = product_crud.filter(
                        session,
                        filters,
                        operators,
                        skip=skip,
                        limit=limit,
                    )
                else:
                    batch = product_crud.get_all(
                        session, skip=skip, limit=limit)

                if not batch:
                    break

                products.extend(batch)
                skip += len(batch)

                # If we got fewer than requested, we've reached the end.
                if len(batch) < limit:
                    break

            # Apply max_price filter if specified
            if max_price is not None:
                products = [p for p in products if p.price <= max_price]

            # Apply search query if specified (search across multiple fields)
            if search_query:
                query_lower = search_query.lower()
                keywords = query_lower.split()

                # Filter out common words that don't help with product search
                common_words = {'show', 'me', 'find', 'search', 'get',
                                'want', 'looking', 'for', 'a', 'an', 'the', 'some', 'any'}
                keywords = [k for k in keywords if k not in common_words]

                if keywords:
                    # Score products based on relevance
                    scored_products = []
                    for p in products:
                        score = 0

                        for keyword in keywords:
                            # Handle plural/singular variations (e.g., kurtis -> kurti, hoodies -> hoodie)
                            keyword_variations = [keyword]
                            if keyword.endswith('s'):
                                keyword_variations.append(
                                    keyword[:-1])  # Remove 's'
                            if keyword.endswith('ies'):
                                keyword_variations.append(
                                    keyword[:-3] + 'y')  # parties -> party

                            # Check all variations
                            matched = False
                            for kw in keyword_variations:
                                # Exact match in product name or category (highest priority)
                                if kw in p.product_name.lower():
                                    score += 10
                                    matched = True
                                if kw in p.category.lower():
                                    score += 8
                                    matched = True
                                # Partial matches in other fields
                                if kw in (getattr(p, 'season', '') or '').lower():
                                    score += 3
                                    matched = True
                                if kw in (getattr(p, 'gender', '') or '').lower():
                                    score += 2
                                    matched = True
                                if p.festival and kw in p.festival.lower():
                                    score += 2
                                    matched = True

                                if matched:
                                    break  # Stop checking variations once we have a match

                        if score > 0:
                            scored_products.append((score, p))

                    # Sort by score (descending) and take products
                    scored_products.sort(key=lambda x: x[0], reverse=True)
                    products = [p for score, p in scored_products]

                    # If no matches found, products list will be empty
                    # This is intentional - we don't show random products

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


def get_customer_purchased_product_ids(customer_id: str) -> set[str]:
    """Return a set of product_ids previously purchased by the customer."""
    if not customer_id:
        return set()
    try:
        orders = get_customer_orders(customer_id)
        return {o.product_id for o in orders if getattr(o, "product_id", None)}
    except Exception as e:
        print(
            f"Error getting purchased product IDs for customer {customer_id}: {e}")
        return set()


# In-memory memory of what we've already shown per customer+query.
# Keeps the inventory_agent from recommending the same products again when the customer asks
# to see more products of the same category/query.
_SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY: dict[tuple[str, str], set[str]] = {}


def _normalize_inventory_query_key(search_query: str) -> str:
    if not search_query:
        return ""

    q = "".join(ch.lower() if ch.isalnum() or ch.isspace()
                else " " for ch in search_query)
    tokens = [t for t in q.split() if t]

    # Drop generic filler words so: "show me some more kurtis" and "kurti" map to same key.
    stop = {
        "show", "me", "find", "search", "get", "want", "looking", "for", "a", "an", "the", "some", "any",
        "more", "another", "next", "different", "products", "product", "items", "item", "category", "same", "again",
        "please", "pls", "kindly",
    }
    tokens = [t for t in tokens if t not in stop]

    return " ".join(tokens) if tokens else q.strip()


def _product_canonical_id(p: Product) -> str | None:
    return getattr(p, "sku", None) or getattr(p, "product_id", None) or getattr(p, "id", None)


def _parse_price_band_from_query(query: str) -> tuple[bool, float | None, float | None, str]:
    """Parse price-band intent from a natural language query.

    Returns:
        (is_price_band, min_price, max_price, cleaned_query)

    Examples:
        "watches above 1000" -> (True, 1000, None, "watches")
        "kurtis between 1500-2000" -> (True, 1500, 2000, "kurtis")
        "shirts under 999" -> (True, None, 999, "shirts")
    """
    if not query or not query.strip():
        return (False, None, None, query or "")

    q = query.strip()
    q_lower = q.lower()

    def _to_number(num_str: str | None, has_k: str | None) -> float | None:
        if not num_str:
            return None
        cleaned = num_str.replace(",", "").replace("₹", "").strip()
        try:
            val = float(cleaned)
        except ValueError:
            return None
        if has_k:
            val *= 1000
        return val

    # 1) BETWEEN / RANGE patterns
    between_pat = re.compile(
        r"\bbetween\b[^0-9₹]*"
        r"(₹?\s*(\d[\d,]*(?:\.\d+)?))\s*(k)?\s*(?:and|to|-)\s*"
        r"(₹?\s*(\d[\d,]*(?:\.\d+)?))\s*(k)?\b",
        flags=re.IGNORECASE,
    )
    m = between_pat.search(q)
    if m:
        min_price = _to_number(m.group(2), m.group(3))
        max_price = _to_number(m.group(5), m.group(6))
        if min_price is not None and max_price is not None:
            if max_price < min_price:
                min_price, max_price = max_price, min_price
            cleaned_query = (q[: m.span(0)[0]] + " " +
                             q[m.span(0)[1]:]).strip()
            cleaned_query = re.sub(
                r"\b(?:rs|inr|rupees|price)\b", " ", cleaned_query, flags=re.IGNORECASE)
            cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
            return (True, min_price, max_price, cleaned_query)

    # 2) HYphen range patterns like 1500-2000 (without explicit 'between')
    hyphen_pat = re.compile(
        r"(₹?\s*(\d[\d,]*(?:\.\d+)?))\s*(k)?\s*-\s*"
        r"(₹?\s*(\d[\d,]*(?:\.\d+)?))\s*(k)?\b",
        flags=re.IGNORECASE,
    )
    m = hyphen_pat.search(q)
    if m:
        min_price = _to_number(m.group(2), m.group(3))
        max_price = _to_number(m.group(5), m.group(6))
        if min_price is not None and max_price is not None:
            if max_price < min_price:
                min_price, max_price = max_price, min_price
            cleaned_query = (q[: m.span(0)[0]] + " " +
                             q[m.span(0)[1]:]).strip()
            cleaned_query = re.sub(
                r"\b(?:rs|inr|rupees|price)\b", " ", cleaned_query, flags=re.IGNORECASE)
            cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
            return (True, min_price, max_price, cleaned_query)

    # 3) ABOVE / OVER / MORE THAN patterns
    above_pat = re.compile(
        r"\b(?:above|over|more\s+than|greater\s+than|>=)\b[^0-9₹]*"
        r"(₹?\s*(\d[\d,]*(?:\.\d+)?))\s*(k)?\b",
        flags=re.IGNORECASE,
    )
    m = above_pat.search(q)
    if m:
        min_price = _to_number(m.group(2), m.group(3))
        if min_price is not None:
            cleaned_query = (q[: m.span(0)[0]] + " " +
                             q[m.span(0)[1]:]).strip()
            cleaned_query = re.sub(
                r"\b(?:rs|inr|rupees|price)\b", " ", cleaned_query, flags=re.IGNORECASE)
            cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
            return (True, min_price, None, cleaned_query)

    # 4) BELOW / UNDER / LESS THAN patterns
    below_pat = re.compile(
        r"\b(?:below|under|less\s+than|<=)\b[^0-9₹]*"
        r"(₹?\s*(\d[\d,]*(?:\.\d+)?))\s*(k)?\b",
        flags=re.IGNORECASE,
    )
    m = below_pat.search(q)
    if m:
        max_price = _to_number(m.group(2), m.group(3))
        if max_price is not None:
            cleaned_query = (q[: m.span(0)[0]] + " " +
                             q[m.span(0)[1]:]).strip()
            cleaned_query = re.sub(
                r"\b(?:rs|inr|rupees|price)\b", " ", cleaned_query, flags=re.IGNORECASE)
            cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()
            return (True, None, max_price, cleaned_query)

    # Not a price-band query
    return (False, None, None, q)


def _safe_price_value(p: Product) -> float | None:
    """Best-effort numeric price extraction."""
    try:
        val = getattr(p, "price", None)
        if val is None:
            return None
        return float(val)
    except Exception:
        return None


def format_products_for_recommendation(products: List[Product]) -> str:
    """
    Format a list of products into recommendation JSON structure.
    This helper function avoids duplicate database queries.

    Args:
        products: List of Product objects already fetched from database

    Returns:
        JSON string with formatted product recommendations
    """
    if not products:
        return json.dumps({
            "name": "Recommendation Agent",
            "id": "recommendation_agent",
            "responses": {
                "default": "❌ No products found matching your query. Please try a different search.",
                "recommendation": []
            }
        })

    # Limit to 4 products for display
    display_products = products[:4]

    # Build recommendation list with image_reference
    recommendations = []
    for product in display_products:
        recommendations.append({
            "product_id": getattr(product, "sku", None) or getattr(product, "product_id", None) or getattr(product, "id", None),
            "product_name": product.product_name,
            "price": product.price,
            "category": getattr(product, "category", None),
            "description": getattr(product, "description", None),
            "image_reference": getattr(product, "image_reference", None),
        })

    # Default message
    default_msg = f"I recommend these {display_products[0].category if display_products else 'products'} based on your preferences. {display_products[0].product_name if display_products else ''} is ₹{int(display_products[0].price) if display_products else ''} and trending — want me to check availability?"

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
def recommendation_agent(inventory_data: str) -> str:
    """
    Shows product recommendations from inventory agent's search results.
    Call this AFTER inventory_agent has searched products.
    Displays products in UI-friendly format with add-to-cart option.

    Args:
        inventory_data: JSON string from inventory_agent containing product details

    Returns:
        Formatted product recommendations with message asking to add to cart or browse more
    """
    try:
        # Parse inventory data
        inventory_json = json.loads(inventory_data)

        if inventory_json.get("status") == "no_products":
            return json.dumps({
                "name": "Recommendation Agent",
                "id": "recommendation_agent",
                "responses": {
                    "default": "❌ No products found matching your search. Would you like to try a different search?",
                    "recommendation": []
                }
            })

        products = inventory_json.get("products", [])

        if not products:
            return json.dumps({
                "name": "Recommendation Agent",
                "id": "recommendation_agent",
                "responses": {
                    "default": "❌ No products available at the moment. Please try again later.",
                    "recommendation": []
                }
            })

        # Build recommendation list with discount information
        recommendations = []
        for product in products:
            original_price = product.get("price", 0)
            discount = product.get("discount", 0) or 0
            discount_price = round(
                original_price * (1 - discount / 100), 2) if discount > 0 else original_price

            recommendations.append({
                "product_id": product.get("product_id"),
                "product_name": product.get("product_name"),
                "price": original_price,
                "discount": discount,
                "discount_price": discount_price,
                "category": product.get("category"),
                "quantity": product.get("quantity"),
                "description": product.get("description"),
                "image_reference": product.get("image_reference"),
            })

        # Message with add-to-cart prompt including discount information
        first_product = products[0]
        first_original_price = first_product['price']
        first_discount = first_product.get('discount', 0) or 0
        first_discount_price = round(first_original_price * (
            1 - first_discount / 100), 2) if first_discount > 0 else first_original_price

        default_msg = f"🛍️ Here are {len(products)} products I found for you! "
        if first_discount > 0:
            default_msg += f"**{first_product['product_name']}** is ₹{int(first_discount_price):,} (Original: ₹{int(first_original_price):,}, {int(first_discount)}% off) and in stock ({first_product['quantity']} available). "
        else:
            default_msg += f"**{first_product['product_name']}** is ₹{int(first_original_price):,} and in stock ({first_product['quantity']} available). "
        default_msg += "\\n\\nWould you like to **add any of these to your cart** with quantity, or do you want to **browse more products**?"

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

    except json.JSONDecodeError:
        return json.dumps({
            "name": "Recommendation Agent",
            "id": "recommendation_agent",
            "responses": {
                "default": "❌ Error parsing product data. Please try searching again.",
                "recommendation": []
            }
        })


@tool
def inventory_agent(search_query: str = None, product_id: str = None, customer_id: str = None) -> str:
    """
    Searches and fetches products from database based on user query or checks specific product availability.
    Uses customer tier to personalize product recommendations.
    This is the FIRST tool to call when user asks for products.
    Returns product details (name, category, quantity, price, image) in JSON format.

    CUSTOMER TIER-BASED PRODUCT FILTERING:
    - tier_1 (Premium): Products >₹1500 with <5% discount, with fallbacks for >₹3000
    - tier_3 (Budget): Products <₹1000 with >15% discount, with fallbacks for high discounts (>10%) or low prices (<₹1100)
    - tier_2 (Middle): No filtering - shows all products

    Args:
        search_query: User's product search query (e.g., "hoodies", "winter wear")
        product_id: Specific product ID to check (optional, use when checking specific product)
        customer_id: Customer ID to personalize recommendations based on their tier

    Returns:
        JSON string with product details or availability status
    """
    # If product_id is provided, check specific product availability
    if product_id:
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

        # Product is available - show details
        if offline_available:
            # Show only the top 3 nearest stores for this customer from the distance table (do not use products table)
            from database import get_db_session
            from models import Distance
            from sqlmodel import select

            session = get_db_session()
            query = select(Distance).where(Distance.customer_id == customer_id)
            distances = session.exec(query).all()
            distances = sorted(
                [d for d in distances if d.distance is not None], key=lambda d: d.distance)
            nearest = distances[:3]
            stores_list = []
            for d in nearest:
                stores_list.append({
                    "store_name": d.store_name,
                    "distance": d.distance,
                    "map_url": d.map_url,
                    "availability": "Available"
                })
            session.close()
            return json.dumps({
                "tool": "inventory_agent",
                "type": "store_selection",
                "storeSelection": {
                    "title": "Select a store for pickup",
                    "stores": stores_list
                }
            })

        # If only online available, fallback to original string
        result = f"✅ **Product {product_id} is IN STOCK!**\n\n"
        result += f"**{product.product_name}** - ₹{int(product.price):,}\n"
        result += f"**Available Quantity:** {product.quantity} units\n\n"
        result += "📦 **Purchase Options:**\n\n"
        if online_available:
            result += "1. 🌐 **Online** - Get it delivered to your home\n\n"
        result += "\n**How would you like to proceed?**\n"
        result += "- Type 'online' to buy online with home delivery\n"
        return result

    # If search_query is provided, search products from database
    if search_query:
        # Special case: if user asked for a specific price band (above/below/between),
        # apply that band strictly and SKIP tier-based segmentation for this query.
        is_price_band, min_price, max_price, cleaned_query = _parse_price_band_from_query(
            search_query
        )

        # Strip price tokens from keyword search so "watches above 1000" searches for "watches".
        # If the cleaned query becomes empty, pass whitespace so we still load a larger page
        # (but the keyword filter won't run because it produces no keywords).
        effective_search_query = cleaned_query
        if is_price_band and not (effective_search_query or "").strip():
            effective_search_query = " "

        products = load_products_from_db(search_query=effective_search_query)

        # Filter products to only show items with quantity > 0 (in stock)
        products = [p for p in products if p.quantity > 0]

        # Apply price band filter (special case). This must happen BEFORE tier segmentation.
        if is_price_band and (min_price is not None or max_price is not None):
            if min_price is not None:
                products = [
                    p for p in products
                    if (_safe_price_value(p) is not None and _safe_price_value(p) >= min_price)
                ]
            if max_price is not None:
                products = [
                    p for p in products
                    if (_safe_price_value(p) is not None and _safe_price_value(p) <= max_price)
                ]

        # Apply tier-based filtering if customer_id is provided
        if customer_id and not is_price_band:
            customer = get_customer_by_id(customer_id)
            if customer and customer.customer_type:
                customer_tier = customer.customer_type
                print(f"[DEBUG] Customer {customer_id} tier: {customer_tier}")

                # tier_1 (Premium): Products >₹4000 with <20% discount, fallback >₹3000
                if customer_tier == "tier_1":
                    filtered_products = [
                        p for p in products
                        if p.price > 1500 and (getattr(p, 'discount', 0) or 0) < 5
                    ]
                    if not filtered_products:
                        # Fallback: Products >₹3000
                        filtered_products = [
                            p for p in products if p.price > 3000]

                    if filtered_products:
                        products = filtered_products
                        print(
                            f"[DEBUG] Filtered {len(products)} premium products for tier_1 customer")

                # tier_3 (Budget): Products <₹1000 with >15% discount, fallbacks for >10% discount or <₹1100
                elif customer_tier == "tier_3":
                    filtered_products = [
                        p for p in products
                        if p.price < 1000 and (getattr(p, 'discount', 0) or 0) > 15
                    ]
                    if not filtered_products:
                        # Fallback 1: Products with >10% discount
                        filtered_products = [
                            p for p in products
                            if (getattr(p, 'discount', 0) or 0) > 10
                        ]
                    if not filtered_products:
                        # Fallback 2: Products <₹1100
                        filtered_products = [
                            p for p in products if p.price < 1100]

                    if filtered_products:
                        products = filtered_products
                        print(
                            f"[DEBUG] Filtered {len(products)} budget products for tier_3 customer")

                # tier_2 (Middle): No filtering - shows all products
                elif customer_tier == "tier_2":
                    print(
                        f"[DEBUG] tier_2 customer - showing all {len(products)} products (no filtering)")

        # Avoid recommending products the customer already purchased.
        # Recommend previously purchased items ONLY if all matched items were already purchased.
        if customer_id:
            purchased_product_ids = get_customer_purchased_product_ids(
                customer_id)
            if purchased_product_ids:
                unpurchased_products = [
                    p for p in products
                    if getattr(p, "product_id", None) not in purchased_product_ids
                ]

                if unpurchased_products:
                    products = unpurchased_products
                    print(
                        f"[DEBUG] Filtered out previously purchased products for {customer_id}. Remaining: {len(products)}")
                else:
                    print(
                        f"[DEBUG] All matched products were already purchased by {customer_id}; allowing repeats")

        # Avoid recommending the same products again for the same customer + query.
        # If the customer asks for "more" items of the same category/query, this surfaces the next items.
        if customer_id:
            # For price-band queries, include band bounds in the key so different bands
            # don't incorrectly share the same "already shown" set.
            cache_source_query = search_query
            if is_price_band:
                band_bits = []
                if min_price is not None:
                    band_bits.append(
                        f"min{int(min_price) if float(min_price).is_integer() else min_price}")
                if max_price is not None:
                    band_bits.append(
                        f"max{int(max_price) if float(max_price).is_integer() else max_price}")
                cache_source_query = f"{cleaned_query} {' '.join(band_bits)}".strip(
                )

            query_key = _normalize_inventory_query_key(cache_source_query)
            if query_key:
                cache_key = (customer_id, query_key)
                already_shown = _SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY.get(
                    cache_key, set())

                if already_shown:
                    unseen_products = [
                        p for p in products
                        if (_product_canonical_id(p) not in already_shown)
                    ]
                    if unseen_products:
                        products = unseen_products
                        print(
                            f"[DEBUG] Removed already-shown products for {customer_id} query='{query_key}'. Remaining: {len(products)}")
                    else:
                        # Exhausted: reset this query so browsing can cycle again.
                        _SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY[cache_key] = set(
                        )
                        print(
                            f"[DEBUG] No unseen products left for {customer_id} query='{query_key}'. Resetting shown cache for this query")

        if not products:
            # No matches for the user's query (do not recommend random products)
            return json.dumps({
                "status": "no_products",
                "message": f"❌ No products found matching '{search_query}'. Try a different keyword or category.",
                "products": []
            })

        # Limit to 4 products
        products = products[:4]

        # Update shown cache AFTER selecting the 4 items.
        if customer_id:
            query_key = _normalize_inventory_query_key(search_query)
            if query_key:
                cache_key = (customer_id, query_key)
                shown = _SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY.setdefault(
                    cache_key, set())
                for p in products:
                    pid = _product_canonical_id(p)
                    if pid:
                        shown.add(pid)

        # Format products as JSON with customer tier info
        product_list = []
        for p in products:
            product_list.append({
                "product_id": getattr(p, "sku", None) or getattr(p, "product_id", None) or getattr(p, "id", None),
                "product_name": p.product_name,
                "category": getattr(p, "category", None),
                "quantity": p.quantity,
                "price": p.price,
                "discount": getattr(p, "discount", 0) or 0,
                "image_reference": getattr(p, "image_reference", None),
                "description": getattr(p, "description", None)
            })

        # Include customer tier in response if available
        response_data = {
            "status": "success",
            "message": f"✅ Found {len(products)} products matching your search",
            "products": product_list
        }

        if customer_id:
            customer = get_customer_by_id(customer_id)
            if customer and customer.customer_type:
                response_data["customer_tier"] = customer.customer_type

        return json.dumps(response_data)

    # If neither product_id nor search_query provided, return error
    return "❌ Please provide either a search_query or product_id to check inventory."


@tool
def add_to_cart_agent(product_id: str, quantity: int, customer_id: str, size: str | None = None) -> str:
    """
    Adds a product to the customer's cart with specified quantity.
    Stores the product in the cart table as 'pending' status.
    Use this when user wants to add a product to cart.

    Args:
        product_id: The product ID to add to cart
        quantity: Number of units to add (must be > 0)
        customer_id: The customer ID

    Returns:
        Confirmation message with cart update
    """
    if quantity <= 0:
        return "❌ Please specify a valid quantity (greater than 0)."

    # Get product details
    product = get_product_by_id(product_id)
    if not product:
        return f"❌ Product {product_id} not found."

    # Check if enough quantity available
    if product.quantity < quantity:
        return f"❌ Sorry, only {product.quantity} units of {product.product_name} are available in stock."

    # Add to cart database as pending
    try:
        with get_db_session() as session:
            # Leave store_id as None initially
            # It will be populated only when user selects offline mode with a specific store

            # Create unique order_id for this cart item
            order_id = f"CART{int(time.time() * 1000) % 1000000}{random.randint(100, 999)}"

            cart_data = {
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "store_id": None,  # Will be set when user chooses offline mode
                "channel": "pending",  # Mark as pending until user decides online/offline
                "status": "pending",
                "quantity": quantity,
                "size": size,
                "created_at": datetime.utcnow().isoformat()
            }

            cart_crud.create(session, cart_data)

            # Calculate discount price
            original_price = product.price
            discount = getattr(product, 'discount', 0) or 0
            discount_price = round(
                original_price * (1 - discount / 100), 2) if discount > 0 else original_price

            total_original = original_price * quantity
            total_discounted = discount_price * quantity
            total_savings = total_original - total_discounted

            result = f"✅ **Added to Cart!**\\n\\n"
            result += f"Product: {product.product_name} (ID: {product_id})\\n"
            result += f"Quantity: {quantity} units\\n"

            if discount > 0:
                result += f"Price per unit: ₹{int(discount_price):,} (Original: ₹{int(original_price):,}, {int(discount)}% off)\\n"
                result += f"Subtotal: ₹{int(total_discounted):,}\\n"
                result += f"💰 You save: ₹{int(total_savings):,}\\n\\n"
            else:
                result += f"Price per unit: ₹{int(original_price):,}\\n"
                result += f"Total: ₹{int(total_original):,}\\n\\n"

            result += "Would you like to **add more products** to your cart or **proceed to view your cart**?"

            return result

    except Exception as e:
        print(f"Error adding to cart: {e}")
        return f"❌ Error adding product to cart. Please try again."


@tool
def view_cart_agent(customer_id: str) -> str:
    """
    Shows all products currently in the customer's cart with quantities and total amount.
    Gives options to modify cart (remove items, add more) or proceed to payment.
    Use this when user wants to view cart or proceed to checkout.

    Args:
        customer_id: The customer ID

    Returns:
        Cart summary with total amount and action options
    """
    try:
        with get_db_session() as session:
            # Get all pending cart items for this customer
            cart_items = cart_crud.filter(
                session,
                filters={"customer_id": customer_id, "status": "pending"},
                operators={"customer_id": "==", "status": "=="},
                limit=50
            )

            if not cart_items:
                return "🛒 Your cart is empty. Would you like to browse products?"

            result = f"🛒 **Your Shopping Cart**\\n\\n"
            result += f"Total Items: {len(cart_items)}\\n\\n"

            total_amount = 0
            total_discount = 0
            cart_details = []

            for item in cart_items:
                product = get_product_by_id(item.product_id)
                if product:
                    qty = getattr(item, 'quantity', 1)
                    size = getattr(item, 'size', None)
                    original_price = product.price
                    discount = getattr(product, 'discount', 0) or 0
                    discount_price = round(
                        original_price * (1 - discount / 100), 2) if discount > 0 else original_price

                    item_total_original = original_price * qty
                    item_total_discounted = discount_price * qty
                    total_amount += item_total_discounted
                    total_discount += (item_total_original -
                                       item_total_discounted)

                    result += f"📦 **{product.product_name}** (ID: {item.product_id})\\n"

                    if discount > 0:
                        result += f"   Price: ₹{int(discount_price):,} each (Original: ₹{int(original_price):,}, {int(discount)}% off)\\n"
                        result += f"   Quantity: {qty} × ₹{int(discount_price):,} = ₹{int(item_total_discounted):,}\\n"
                        result += f"   💰 Saved: ₹{int(item_total_original - item_total_discounted):,}\\n"
                    else:
                        result += f"   Quantity: {qty} × ₹{int(original_price):,} = ₹{int(item_total_original):,}\\n"

                    result += f"   Order ID: {item.order_id}\\n\\n"

                    cart_details.append({
                        "order_id": item.order_id,
                        "product_id": item.product_id,
                        "product_name": product.product_name,
                        "quantity": qty,
                        "size": size,
                        "price": discount_price,
                        "original_price": original_price,
                        "discount": discount,
                        "total": item_total_discounted,
                        "image_reference": product.image_reference,
                        "savings": item_total_original - item_total_discounted if discount > 0 else 0
                    })

            result += f"════════════════════════════════\\n"
            if total_discount > 0:
                result += f"💚 **Total Savings: ₹{int(total_discount):,}**\\n"
            result += f"💰 **Total Amount: ₹{int(total_amount):,}**\\n\\n"
            result += "**What would you like to do?**\\n"
            result += "- Type 'proceed' to continue to payment\\n"
            result += "- Type 'add more' to browse more products\\n"
            result += "- To remove an item, provide the Order ID\\n"

            # Return structured JSON with both text and cart items array
            import json
            return json.dumps({
                "id": "view_cart_agent",
                "response": result,
                "cart_items": cart_details,
                "total_amount": total_amount,
                "total_savings": total_discount,
                "total_items": len(cart_items)
            })

    except Exception as e:
        print(f"Error viewing cart: {e}")
        return f"❌ Error loading cart. Please try again."


@tool
def remove_from_cart_agent(order_id: str, customer_id: str) -> str:
    """
    Removes a specific item from the customer's cart.
    Use this when user wants to remove a product from cart.

    Args:
        order_id: The order_id of the cart item to remove
        customer_id: The customer ID (for verification)

    Returns:
        Confirmation message
    """
    try:
        with get_db_session() as session:
            # Verify the cart item belongs to this customer
            cart_item = cart_crud.get_by_id(session, order_id)

            if not cart_item:
                return f"❌ Cart item {order_id} not found."

            if cart_item.customer_id != customer_id:
                return "❌ This cart item doesn't belong to you."

            # Get product name for confirmation message
            product = get_product_by_id(cart_item.product_id)
            product_name = product.product_name if product else cart_item.product_id

            # Delete from cart
            cart_crud.delete(session, order_id)

            result = f"✅ Removed **{product_name}** from your cart.\\n\\n"
            result += "Would you like to view your updated cart?"

            return result

    except Exception as e:
        print(f"Error removing from cart: {e}")
        return f"❌ Error removing item from cart. Please try again."


@tool
def choose_channel_agent(customer_id: str) -> str:
    """
    Asks customer to choose between ONLINE (home delivery) or OFFLINE (store pickup) purchase.
    Call this after user views cart and wants to proceed to checkout.

    Args:
        customer_id: The customer ID

    Returns:
        Message asking user to choose online or offline channel
    """
    try:
        with get_db_session() as session:
            # Get pending cart items to show summary
            cart_items = cart_crud.filter(
                session,
                filters={"customer_id": customer_id, "status": "pending"},
                operators={"customer_id": "==", "status": "=="},
                limit=50
            )

            if not cart_items:
                return "🛒 Your cart is empty. Please add products first."

            # Calculate total with discount prices
            total_amount = 0
            for item in cart_items:
                product = get_product_by_id(item.product_id)
                if product:
                    qty = getattr(item, 'quantity', 1)
                    original_price = product.price
                    discount = getattr(product, 'discount', 0) or 0
                    discount_price = round(
                        original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                    total_amount += discount_price * qty

            result = f"🛍️ **Choose Your Purchase Channel**\\n\\n"
            result += f"Total Items: {len(cart_items)}\\n"
            result += f"Total Amount: ₹{int(total_amount):,}\\n\\n"
            result += "How would you like to complete your purchase?\\n\\n"
            result += "1. 🌐 **ONLINE** - Home delivery (3-5 business days)\\n"
            result += "   • Secure online payment\\n"
            result += "   • Track your order\\n"
            result += "   • Earn loyalty points & coupons\\n\\n"
            result += "2. 🏪 **OFFLINE** - Store pickup (Ready in 2 hours)\\n"
            result += "   • Pay at store\\n"
            result += "   • Pick up from nearest location\\n"
            result += "   • Instant product availability check\\n\\n"
            result += "Please type **'online'** or **'offline'** to continue."

            return result

    except Exception as e:
        print(f"Error in choose_channel_agent: {e}")
        return "❌ Error loading checkout options. Please try again."


@tool
def payment_agent(customer_id: str, payment_method: str = "") -> str:
    """
    Shows available payment methods and processes online payment for all items in customer's cart.
    Use this after user confirms cart and chooses ONLINE purchase option.

    STEP 1: If payment_method is empty, show 4 payment methods (UPI, Credit Card, Debit Card, Net Banking)
    STEP 2: If payment_method is provided, process payment for all cart items

    Args:
        customer_id: The customer ID
        payment_method: Payment method selected by user (upi, credit card, debit card, net banking). 
                       Leave empty to show available payment methods.

    Returns:
        Payment options (if method not provided) or payment confirmation details
    """
    try:
        with get_db_session() as session:
            # Fetch cart items with status 'pending' and channel is NULL or empty (not set)
            cart_items = cart_crud.filter(
                session,
                filters={"customer_id": customer_id, "status": "pending"},
                operators={"customer_id": "==", "status": "=="},
                limit=50
            )
            # Only include items where channel is None or empty string (not set yet)
            # cart_items = [item for item in cart_items if not getattr(
            #     item, 'channel', None)]
            # Include items that are pending and not yet paid
            cart_items = [
                item for item in cart_items
                if item.status == "pending"
            ]

            print(customer_id)

            if not cart_items:
                return "🛒 Your cart is empty. Please add products to cart first."

            # Calculate total amount with discount prices
            total_amount = 0
            cart_summary = []
            for item in cart_items:
                product = get_product_by_id(item.product_id)
                if product:
                    qty = getattr(item, 'quantity', 1)
                    original_price = product.price
                    discount = getattr(product, 'discount', 0) or 0
                    discount_price = round(
                        original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                    item_total = discount_price * qty
                    total_amount += item_total
                    cart_summary.append({
                        "order_id": item.order_id,
                        "product_id": item.product_id,
                        "product_name": product.product_name,
                        "quantity": qty,
                        "price": discount_price
                    })

    except Exception as e:
        print(f"Error in payment_agent: {e}")
        return f"❌ Error loading cart for payment. Please try again."

    # If no payment method specified, show available methods
    if not payment_method:
        result = f"💳 **Payment for Your Cart**\\n\\n"
        result += f"Total Items: {len(cart_items)}\\n"
        result += f"**Total Amount: ₹{int(total_amount):,}**\\n\\n"
        result += "Please choose your preferred payment method:\\n\\n"
        result += "1. 📱 **UPI** - Pay using any UPI app (Google Pay, PhonePe, Paytm, etc.)\\n"
        result += "2. 💳 **Credit Card** - Visa, Mastercard, American Express, etc.\\n"
        result += "3. 💳 **Debit Card** - All major banks supported\\n"
        result += "4. 🏦 **Net Banking** - Direct bank transfer\\n\\n"
        result += "Which payment method would you like to use?"
        return result

    # Process payment with selected method
    payment_id = f"PAY{random.randint(10000, 99999)}"
    order_id = f"ORD{random.randint(100000, 999999)}"

    result = f"💳 **Processing Payment...**\\n\\n"
    result += f"Order ID: {order_id}\\n"
    result += f"Total Items: {len(cart_items)}\\n"
    result += f"Amount: ₹{int(total_amount):,}\\n"
    result += f"Method: {payment_method.upper()}\\n"
    result += f"Payment ID: {payment_id}\\n\\n"
    result += "✅ **Payment Successful!**\\n\\n"

    # Just mark payment as completed - ALL DB operations (order_history, store_keeper_transaction, inventory deduction)
    # are handled by post_purchase_agent to avoid duplicates
    try:
        with get_db_session() as session:
            # Update cart status to 'paid' and channel to 'online'
            # post_purchase_agent will later: create order_history, create store_keeper_transaction, deduct inventory, and DELETE cart items
            for item_summary in cart_summary:
                item_order_id = item_summary["order_id"]
                try:
                    cart_crud.update(session, item_order_id, {
                        "status": "paid", "channel": "online"})
                except Exception as e:
                    print(
                        f"Warning: failed to update cart {item_order_id}: {e}")
    except Exception as e:
        print(f"Warning during payment processing: {e}")

    result += f"Your order is being processed...\\n\\n"
    result += "[SYSTEM: Now call fulfillment_agent with purchase_type='online', order_id='{order_id}', customer_id='{customer_id}']"

    return result


@tool
def fulfillment_agent(purchase_type: str = "online", store_name: str = "", customer_id: str | None = None, order_id: str | None = None) -> str:
    """
    Handles order fulfillment for cart items - delivery for online, store pickup for offline.
    For ONLINE: Call this after payment is complete. Will automatically trigger loyalty_agent and post_purchase_agent.
    For OFFLINE: Call this after user selects a store. Ends conversation and switches to store kiosk.

    Args:
        purchase_type: Either 'online' or 'offline'
        store_name: Name of the selected store (REQUIRED for offline, leave empty for online)
        customer_id: The customer ID
        order_id: The order ID from payment (required for online; optional for offline)

    Returns:
        Fulfillment details and order tracking info with auto-call instructions for online
    """
    response_payload = {
        "id": "fulfillment_agent",
        "type": "fulfillment",
        "response": ""
    }
    if not order_id:
        order_id = f"ORD{random.randint(100000, 999999)}"

    # Get cart items to show in fulfillment
    try:
        with get_db_session() as session:
            if purchase_type.lower() == "online":
                cart_items = cart_crud.filter(
                    session,
                    filters={"customer_id": customer_id,
                             "status": "paid",
                             "channel": "online"},
                    operators={"customer_id": "==",
                               "status": "==", "channel": "=="},
                    limit=50
                )
            else:
                # For offline, show cart items with status 'pending' and channel 'offline' or 'pending'
                cart_items = cart_crud.filter(
                    session,
                    filters={"customer_id": customer_id,
                             "status": "pending"},
                    operators={"customer_id": "==",
                               "status": "=="},
                    limit=50
                )

            cart_summary = []
            total_amount = 0
            for item in cart_items:
                product = get_product_by_id(item.product_id)
                if product:
                    qty = getattr(item, 'quantity', 1)
                    original_price = product.price
                    discount = getattr(product, 'discount', 0) or 0
                    discount_price = round(
                        original_price * (1 - discount / 100), 2) if discount > 0 else original_price
                    item_total = discount_price * qty
                    total_amount += item_total
                    cart_summary.append({
                        "product_name": product.product_name,
                        "product_id": item.product_id,
                        "quantity": qty,
                        "price": discount_price
                    })
    except Exception as e:
        print(f"Warning: Error loading cart items in fulfillment: {e}")
        cart_summary = []
        total_amount = 0

    # Always return the fulfillment agent message in a dict with 'response' key for frontend
    if purchase_type.lower() == "online":
        print("⏳ Confirming your order...")
        time.sleep(2.5)
        delivery_date = "3-5 business days"
        result = f"📦 **Order Confirmed!**\n\n"
        result += f"Order ID: {order_id}\n"
        result += f"Total Items: {len(cart_summary)}\n"
        result += f"Total Amount: ₹{int(total_amount):,}\n"
        result += f"Delivery Type: Home Delivery\n"
        result += f"Expected Delivery: {delivery_date}\n\n"
        if cart_summary:
            result += "**Your Items:**\n"
            for item in cart_summary:
                result += f"- {item['product_name']} × {item['quantity']} = ₹{int(item['price'] * item['quantity']):,}\n"
            result += "\n"
        result += "You can track your order with the Order ID.\n\n"
        result += f"[SYSTEM: AUTOMATICALLY call loyalty_agent with order_id='{order_id}' and customer_id='{customer_id}']\n"
        result += f"[SYSTEM: After loyalty_agent completes, AUTOMATICALLY call post_purchase_agent with order_id='{order_id}' and customer_id='{customer_id}']"
        response_payload["response"] = result
        return response_payload

    else:
        if not store_name or store_name == "Store":
            return {"response": "⚠️ Please select a specific store from the available options for pickup. Which store would you like to visit?"}
        store_details = None
        all_stores = get_all_stores()
        for store in all_stores:
            if store_name.lower() in store.store_name.lower() or store_name == store.store_id:
                store_details = store
                break
        store_display_name = store_details.store_name if store_details else store_name
        store_address = store_details.address if store_details else "Please check store location"
        try:
            with get_db_session() as session:
                for item in cart_items:
                    cart_crud.update(session, item.order_id, {
                        "channel": "offline",
                        "store_id": store_details.store_id if store_details else None
                    })
        except Exception as e:
            print(f"Warning: failed to update cart for offline: {e}")
        result = f"🏪 **In-Store Pickup Confirmed!**\n\n"
        result += f"Order ID: {order_id}\n"
        result += f"Total Items: {len(cart_summary)}\n"
        result += f"Total Amount: ₹{int(total_amount):,}\n"
        result += f"Pickup Store: {store_display_name}\n"
        result += f"Store Address: {store_address}\n"
        result += f"Status: Ready for pickup in 2 hours\n\n"
        if cart_summary:
            result += "**Your Items:**\n"
            for item in cart_summary:
                result += f"- {item['product_name']} × {item['quantity']}\n"
            result += "\n"
        result += "Please visit the store to complete your purchase.\n"
        result += "💡 Show this Order ID at the store kiosk.\n\n"
        result += "Thank you for choosing us! Have a great day! 🛍️\n\n"
        result += "[SYSTEM: CONVERSATION_COMPLETE - Offline store pickup. Transfer to in-store kiosk. END conversation.]"
        response_payload["response"] = result
    return response_payload


@tool
def loyalty_agent(order_id: str, customer_id: str) -> str:
    """
    Awards loyalty points and provides coupon codes after successful order.
    Call this AUTOMATICALLY after fulfillment for online purchases.
    After completion, AUTOMATICALLY triggers post_purchase_agent.

    Args:
        order_id: The order ID to award points for
        customer_id: The customer ID

    Returns:
        Loyalty points earned and coupon codes with auto-call instruction for post_purchase_agent
    """
    # Add delay before showing loyalty rewards
    print("⏳ Calculating your rewards...")
    time.sleep(2.5)

    # Calculate total loyalty points from all order items based on product loyalty_points
    try:
        with get_db_session() as session:
            # Get cart items that were just processed (status="paid", channel="online")
            cart_items = cart_crud.filter(
                session,
                filters={"customer_id": customer_id,
                         "status": "paid", "channel": "online"},
                operators={"customer_id": "==",
                           "status": "==", "channel": "=="},
                limit=50
            )

            # Calculate total loyalty points from each product's loyalty_points field
            total_points = 0
            for item in cart_items:
                product = get_product_by_id(item.product_id)
                if product:
                    qty = getattr(item, 'quantity', 1)
                    product_loyalty_points = getattr(
                        product, 'loyalty_points', 0) or 0
                    total_points += product_loyalty_points * qty
                    print(
                        f"  📍 {product.product_name}: {product_loyalty_points} points × {qty} = {product_loyalty_points * qty} points")

            print(f"  ✅ Total loyalty points earned: {total_points}")

            # Fallback to random if no items found
            if total_points == 0:
                total_points = random.randint(50, 200)

            # Update customer's loyalty points in the database
            try:
                customer = customer_crud.get_by_id(session, customer_id)
                if customer:
                    current_points = getattr(
                        customer, 'loyalty_points', 0) or 0
                    new_total_points = current_points + total_points

                    # Update the customer's loyalty points
                    customer_crud.update(
                        session,
                        customer_id,
                        {"loyalty_points": new_total_points}
                    )
                    session.commit()
                    print(
                        f"  ✅ Updated customer {customer_id} loyalty points: {current_points} + {total_points} = {new_total_points}")
                else:
                    print(
                        f"  ⚠️ Customer {customer_id} not found, loyalty points not updated")
            except Exception as e:
                print(f"  ❌ Error updating customer loyalty points: {e}")

    except Exception as e:
        print(f"Warning: Error calculating loyalty points: {e}")
        total_points = random.randint(50, 200)

    coupon_codes = [
        {"code": f"SAVE{random.randint(10, 50)}", "discount": "10% off"},
        {"code": f"WELCOME{random.randint(100, 999)}", "discount": "₹100 off"},
        {"code": f"EXTRA{random.randint(10, 30)}",
         "discount": "Extra ₹50 off on next order"}
    ]

    result = f"🎉 **Loyalty Rewards Unlocked!**\\n\\n"
    result += f"Order ID: {order_id}\\n"
    result += f"Points Earned: {total_points} points 🌟\\n\\n"
    result += "**Coupon Codes for Next Purchase:**\\n"
    for coupon in coupon_codes:
        result += f"- Code: `{coupon['code']}` - {coupon['discount']}\\n"

    result += "\\nThank you for shopping with us!\\n\\n"
    # Instruction for LLM to automatically call post_purchase_agent
    result += f"[SYSTEM: AUTOMATICALLY call post_purchase_agent with order_id='{order_id}' and customer_id='{customer_id}' NOW]"
    return result


@tool
def post_purchase_agent(order_id: str, customer_id: str) -> str:
    """
    Provides post-purchase services like feedback, support, and order tracking.
    Use this as the final step after loyalty rewards (online flow).
    Also handles DB operations: adds to order_history and store_keeper_transaction, 
    deducts inventory, and DELETES items from cart.

    Args:
        order_id: The order ID for post-purchase services
        customer_id: The customer ID

    Returns:
        Feedback link and support information
    """
    # Add 2-3 seconds delay before showing post-purchase services
    print("⏳ Processing your request...")
    time.sleep(2.5)

    # === DB operations: Add to order_history, store_keeper_transaction, and delete from cart ===
    try:
        print(
            f"[DEBUG] post_purchase_agent: order_id={order_id}, customer_id={customer_id}")
        from crud import CartCRUD, OrderHistoryCRUD, StoreKeeperTransactionCRUD, ProductCRUD, StoreCRUD, CustomerCRUD
        from models import OrderHistory, StoreKeeperTransaction

        with get_db_session() as session:
            print("[DEBUG] Fetching paid cart items for customer...")
            # Get all cart items with status 'paid' for this customer
            cart_items = cart_crud.filter(
                session,
                filters={"customer_id": customer_id,
                         "status": "paid", "channel": "online"},
                operators={"customer_id": "==",
                           "status": "==", "channel": "=="},
                limit=50
            )

            if not cart_items:
                print(
                    f"[WARNING] No paid cart items found for customer {customer_id}")

            # Get customer details
            customer = CustomerCRUD.get_by_id(session, customer_id)
            customer_name = customer.customer_name if customer else ''

            print(f"[DEBUG] Processing {len(cart_items)} cart items...")
            for cart_item in cart_items:
                product_id = cart_item.product_id
                item_order_id = cart_item.order_id
                qty = getattr(cart_item, 'quantity', 1)
                size = getattr(cart_item, 'size', None)

                # Get product details
                product = ProductCRUD.get_by_id(session, product_id)
                if not product:
                    print(
                        f"[WARNING] Product {product_id} not found, skipping...")
                    continue

                product_name = product.product_name
                product_price = product.price
                total_amount = product_price * qty

                print(
                    f"[DEBUG] Processing cart item: {item_order_id}, product: {product_name}, qty: {qty}")

                # Add to order_history
                try:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    loyalty_pts = getattr(product, 'loyalty_points', 0)

                    order_history = OrderHistory(
                        transaction_id=item_order_id,
                        customer_id=customer_id,
                        customer_name=customer_name,
                        product_id=product_id,
                        product_name=product_name,
                        quantity=qty,
                        size=size,
                        order_dates=now,
                        loyalty_points=loyalty_pts * qty
                    )
                    OrderHistoryCRUD.create(session, order_history)
                    print(
                        f"[DEBUG] OrderHistory record created for {product_id}")
                except Exception as e:
                    print(
                        f"[ERROR] Failed to create order_history for {product_id}: {e}")

                # Add to store_keeper_transaction
                try:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    store_keeper_txn = StoreKeeperTransaction(
                        customer_id=customer_id,
                        product_id=product_id,
                        date=now,
                        user_name=customer_name,
                        product=product_name,
                        qty=qty,
                        size=size,
                        mode="Online",
                        store_name="Online",
                        store_id=None,
                        status="Complete",
                        amount=total_amount,
                        address=getattr(customer, 'address', ""),
                        phone=getattr(customer, 'phone', "")
                    )
                    StoreKeeperTransactionCRUD.create(
                        session, store_keeper_txn)
                    print(
                        f"[DEBUG] StoreKeeperTransaction record created for {product_id}")
                except Exception as e:
                    print(
                        f"[ERROR] Failed to create store_keeper_transaction for {product_id}: {e}")

                # Deduct quantity from inventory
                try:
                    deduct_product_quantity(product_id, quantity=qty)
                    print(
                        f"[DEBUG] Deducted {qty} units from product {product_id} inventory")
                except Exception as e:
                    print(
                        f"[ERROR] Failed to deduct inventory for {product_id}: {e}")

                # Delete from cart
                try:
                    CartCRUD.delete(session, item_order_id)
                    print(f"[DEBUG] Deleted cart item {item_order_id}")
                except Exception as e:
                    print(
                        f"[ERROR] Failed to delete cart item {item_order_id}: {e}")

            session.commit()
            print(f"[DEBUG] DB commit successful for customer {customer_id}")

    except Exception as e:
        import traceback
        print(f"[ERROR] Post-purchase DB operations failed: {e}")
        traceback.print_exc()

    # Clear the payload for this customer after successful purchase
    try:
        import sqlite3
        import os

        # Get absolute path to chat_history.db
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(backend_dir, "chat_history.db")

        print(f"[DEBUG] Clearing payload from: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Set payload to NULL for this customer
        cursor.execute(
            "UPDATE payload SET payload = NULL WHERE customer_id = ?", (customer_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        print(
            f"[DEBUG] Payload cleared for customer {customer_id} - Rows affected: {rows_affected}")
    except Exception as e:
        import traceback
        print(
            f"[ERROR] Failed to clear payload for customer {customer_id}: {e}")
        traceback.print_exc()

    result = f"📝 **Post-Purchase Services**\n\n"
    result += f"Order ID: {order_id}\n\n"
    result += "**Available Services:**\n"
    result += "- 📊 Track Order: https://example.com/track/" + order_id + "\n"
    result += "- ⭐ Leave Feedback: https://example.com/feedback\n"
    result += "- 💬 Customer Support: support@example.com\n"
    result += "- 🔄 Return/Exchange: Available within 7 days\n\n"
    result += "We'd love to hear your feedback! Please rate your experience."

    return result


@tool
def upsell_agent(customer_id: str) -> str:
    """
    Boosts sales by recommending attractive accessory products after the customer views their cart.
    This agent is triggered AUTONOMOUSLY after view_cart_agent completes.
    It randomly selects an accessory category (belts, shoes, watches, wallets) and
    returns a search query for inventory_agent to follow the normal recommendation path.

    Args:
        customer_id: The customer ID

    Returns:
        JSON with a random accessory search query for inventory_agent
    """
    accessory_categories = ["belts", "shoes", "watches", "wallets"]
    selected = random.choice(accessory_categories)
    search_query = f"show me {selected}"

    print(
        f"[UPSELL] Triggered for customer {customer_id} — recommending: {selected}")

    return json.dumps({
        "tool": "upsell_agent",
        "type": "upsell",
        "search_query": search_query,
        "category": selected,
        "customer_id": customer_id
    })


# ============ Agent Tools List ============
tools = [
    customer_info_agent,
    inventory_agent,
    recommendation_agent,
    upsell_agent,
    add_to_cart_agent,
    view_cart_agent,
    remove_from_cart_agent,
    choose_channel_agent,
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

    from langchain_core.messages import SystemMessage
    customer_id = state.get("customer_id", "UNKNOWN")
    system_message = SystemMessage(
        content=f"""
You are a helpful, proactive AI shopping assistant for an e-commerce platform.

**CRITICAL: CONVERSATION HISTORY AWARENESS**
Before choosing which tool to call, CHECK the conversation history:
1. What was the LAST tool you called?
2. What did it return?
3. This determines your NEXT action

**OFFLINE FLOW STATE TRACKING:**
- If LAST tool was `inventory_agent(product_id=X)` AND it returned a list of stores → You are in "WAITING FOR STORE SELECTION" state
- In this state, user's NEXT message is their store selection
- Action: Call ONLY `fulfillment_agent(purchase_type="offline", store_name=<user_message>)`
- DO NOT call inventory_agent or view_cart_agent again

CRITICAL WORKFLOW - FOLLOW THIS EXACT SEQUENCE:

**IMPORTANT: DO NOT call `upsell_agent` directly.** It is triggered AUTOMATICALLY by the system after `view_cart_agent` completes. The upsell_agent recommends accessory products (belts, shoes, watches, wallets) to boost sales. You do not need to handle this — it runs autonomously.

**STEP 1: PRODUCT SEARCH & DISCOVERY**
- When user asks for products (e.g., "show me hoodies", "looking for shirts"), call `inventory_agent` with search_query AND customer_id parameters
- **MANDATORY**: IMMEDIATELY call `recommendation_agent` passing the COMPLETE JSON RESPONSE from inventory_agent
- **CRITICAL RULE**: EVERY `inventory_agent(search_query=X)` call MUST be followed by `recommendation_agent(inventory_data=<FULL_JSON_FROM_INVENTORY_AGENT>)`
- **PARAMETER FORMAT**: inventory_data must be the EXACT JSON string returned by inventory_agent, NOT just the search query
  * ✅ CORRECT: recommendation_agent(inventory_data='{{"status":"success","message":"✅ Found 4 products...","products":[...]}}')
  * ❌ WRONG: recommendation_agent(inventory_data='{{"search_query":"dress"}}')
  * ❌ WRONG: recommendation_agent(inventory_data='dress')
- **APPLIES TO**: ALL product searches, even if user requests multiple products in one message (e.g., "add X and show me Y")
  * Example: User says "Van Heusen Shirt quantity 2 and also show me dress"
  * Action 1: add_to_cart_agent(product_id="PRD033", quantity=2)
  * Action 2: inventory_result = inventory_agent(search_query="dress") → Returns: '{{"status":"success","products":[...]}}'
  * Action 3: recommendation_agent(inventory_data=inventory_result) ← Pass the FULL JSON result from Action 2
- **NEVER** manually format product recommendations - ALWAYS use recommendation_agent to show discount prices correctly
- Ask if they want to add any products to cart with quantity

**STEP 2: ADD TO CART - RECOGNIZE PURCHASE INTENT**

**PURCHASE INTENT KEYWORDS** - When user's message contains these phrases, they want to ADD TO CART:
- "i want to buy X" / "buy X" / "purchase X"
- "i'll take X" / "get me X" / "i want X"
- "add X" / "add to cart X"
- Product name followed by "quantity N" (e.g., "US Polo Shirt quantity 3")

**CRITICAL: PRODUCT IDENTIFICATION FROM CONVERSATION HISTORY**
When user wants to add a product to cart:

1. **SEARCH CONVERSATION HISTORY**: Look at the MOST RECENT tool call results from inventory_agent or recommendation_agent
2. **FIND EXACT MATCH**: Match the user's product name/ID to the products that were JUST SHOWN to them
3. **EXTRACT CORRECT product_id**: Use the product_id field from the matching product in the recent results
4. **NEVER USE HARDCODED IDs**: Do NOT default to PRD056 or any fixed product ID

**MATCHING RULES**:
- User says: "US Polo Shirt" → Find product with product_name containing "US Polo Shirt" → Use that product's product_id (e.g., PRD015)
- User says: "PRD028 quantity 2" → Use product_id="PRD028" directly
- User says: "Louis Philippe" → Find product with product_name containing "Louis Philippe" → Use that product's product_id
- If product name is ambiguous, ask user to clarify which product they mean

**QUANTITY EXTRACTION** - Extract from user message:
- "add PRD049 quantity 4" → quantity=4
- "US Polo Shirt quantity 3" → quantity=3
- "I want 5 of this product" → quantity=5
- "buy X" (no quantity mentioned) → quantity=1 (default)

**ACTION**: 
- IMMEDIATELY call `add_to_cart_agent(product_id=<MATCHED_ID_FROM_RECENT_RESULTS>, quantity=<extracted_or_1>, customer_id="{customer_id}")`
- DO NOT call inventory_agent again if product was already shown
- DO NOT search for the product again

**CORRECT EXAMPLE FLOW**:
Agent shows: PRD004: "Louis Philippe Shirt", PRD015: "US Polo Shirt", PRD024: "H&M Casual Shirt", PRD028: "Gap Cotton Shirt"
User says: "US Polo Shirt quantity 3"
Correct Action: `add_to_cart_agent(product_id="PRD015", quantity=3, customer_id="{customer_id}")` ✅
Wrong Action: `add_to_cart_agent(product_id="PRD056", ...)` ❌ (PRD056 was not in the shown list!)

**VERIFICATION BEFORE CALLING add_to_cart_agent**:
- Confirm the product_id you're using was actually shown in the recent inventory_agent results
- If unsure, ask user to specify the product ID or clarify which product they mean

- After adding, ask if they want to add more products or view their cart

**STEP 3: VIEW CART & CONFIRMATION**
- When user says "view cart" or "show cart" or "please show my items in the cart", call `view_cart_agent` with customer_id
- Show all cart items with quantities and total amount
- Ask if they want to remove any items, add more products, or proceed to payment
- If they want to remove, use `remove_from_cart_agent` with order_id

**STEP 4: PROCEED TO CHECKOUT (CHOOSE CHANNEL)**
- When user says "proceed", "checkout", "continue", "buy", "purchase", "pay", "proceed with payment", or confirms they want to checkout, call `choose_channel_agent` with customer_id
- DO NOT call view_cart_agent again when user says proceed
- `choose_channel_agent` displays ONLINE (home delivery with loyalty rewards) vs OFFLINE (store pickup) options
- After channel selection, IMMEDIATELY move to the appropriate flow below (do NOT call choose_channel_agent again)

**STEP 5A: OFFLINE FLOW - STORE SELECTION**
- If user types "offline" or selects offline option or wants to pick up from store:
  
  **STAGE 1: Show Available Stores (ONE TIME ONLY)**
  1. First, call `view_cart_agent` to get the list of cart items and identify the first product_id
  2. Then call `inventory_agent(product_id=<FIRST_PRODUCT_ID_FROM_CART>)` ONCE to show stores for that product
     - Example: If cart has PRD023, PRD045, call inventory_agent(product_id="PRD023")
     - Tool shows: "STR016 - South City Mall", "STR011 - ABFRL Store South City"
     - After this call COMPLETES → **WORKFLOW IS NOW IN STAGE 2**
     - Mark in your memory: "Stores have been shown, next message is store selection"
  
  **STAGE 2: DETECT STORE SELECTION → SKIP TO FULFILLMENT**
  2. **STATE CHECK**: Look at conversation history
     - IF previous tool call was inventory_agent(product_id=X) AND it returned store list
     - THEN user's current message is store selection (NOT a product search, NOT a cart view request)
  
  3. **RECOGNITION RULE**: User's message contains store info like:
     - Just ID: "STR016" or "STR011"
     - Full name: "ABFRL Store South City" or "South City Mall"
     - Combined: "STR011 - ABFRL Store South City"
  
  4. **IMMEDIATE ACTION - NO OTHER TOOLS**:
     - Call `fulfillment_agent(purchase_type="offline", store_name="<user_exact_message>", customer_id="{customer_id}")`
     - **FORBIDDEN**: DO NOT call view_cart_agent (cart already known)
     - **FORBIDDEN**: DO NOT call inventory_agent again (stores already shown)
     - **FORBIDDEN**: DO NOT call any other tool
     - Skip directly to fulfillment_agent
  
  **STAGE 3: Complete Order**
  5. fulfillment_agent returns "In-Store Pickup Confirmed! Show this Order ID at the store kiosk."
     - Display confirmation message
     - Show "Switch to in-store kiosk" instruction
     - END conversation immediately (no loyalty/post-purchase for offline)

**STEP 5B: ONLINE FLOW**
- If user types "online" or confirms online purchase:
  1. IMMEDIATELY call `payment_agent` with customer_id (no payment_method parameter) to show 4 payment options: UPI, Credit Card, Debit Card, Net Banking
  2. DO NOT ask to view cart again, DO NOT call choose_channel_agent again
  3. DO NOT call view_cart_agent again (cart already known)
**STEP 5B: ONLINE FLOW - TWO-STAGE PAYMENT PROCESS**
- If user types "online" or confirms online purchase:
  
  **STAGE 1: Show Payment Options**
  1. IMMEDIATELY call `payment_agent(customer_id="{customer_id}")` - NO payment_method parameter
     - This shows 4 payment options: UPI, Credit Card, Debit Card, Net Banking
     - DO NOT ask to view cart, DO NOT call choose_channel_agent
  
  **STAGE 2: Process Payment (User's NEXT message)**
  2. After payment_agent shows options, user's VERY NEXT MESSAGE is their payment method selection
     - User types ONE of: "upi", "credit card", "debit card", "net banking" (case-insensitive)
     - IMMEDIATELY call `payment_agent(payment_method="<method>", customer_id="{customer_id}")`
     - Examples: User says "upi" → call payment_agent(payment_method="upi", customer_id="{customer_id}")
     - DO NOT ask for confirmation, DO NOT call view_cart_agent, DO NOT call payment_agent a third time
     - This SECOND call to payment_agent processes the payment and returns success always
     - Payment_agent returns "Payment Successful!" always and No other messages
     - NEVER return "It seems your cart is empty. Please add some products to your cart before proceeding with the payment. Would you like to search for products now?" at this stage - cart is already known to have items. ONLY return payment success message.
  
  **STAGE 3: After Payment Success**
  3. After payment_agent returns "Payment Successful", IMMEDIATELY call `fulfillment_agent(purchase_type="online", customer_id="{customer_id}")`
     - DO NOT call payment_agent again
     - DO NOT ask user for anything
     - Move directly to fulfillment
  4. AUTOMATICALLY call `loyalty_agent` (don't wait for user) with order_id and customer_id
  5. AUTOMATICALLY call `post_purchase_agent` (don't wait for user) with order_id and customer_id
  6. END conversation

**KEY POINT**: payment_agent is called EXACTLY TWICE in online flow:
  - Call 1: payment_agent(customer_id) → shows options
  - Call 2: payment_agent(payment_method="upi", customer_id) → processes payment
  - After Call 2 returns success, STOP calling payment_agent and move to fulfillment_agent

**MANDATORY RULES:**
- NEVER skip tool calls or generate data yourself
- ALWAYS use customer_id: {customer_id}
- **PURCHASE INTENT RULE - CRITICAL PRODUCT MATCHING**: 
  * When user wants to add a product to cart, FIRST look at the MOST RECENT inventory_agent/recommendation_agent results in conversation history
  * MATCH the user's product name to the products that were JUST shown
  * EXTRACT the correct product_id from the matching product in those results
  * NEVER use a hardcoded product_id like PRD056 unless it was actually in the recent results
  * Example: If recent results show [PRD015: "US Polo Shirt", PRD024: "H&M Casual Shirt"] and user says "US Polo Shirt quantity 3", use product_id="PRD015", NOT PRD056
  * If product not found in recent results, call inventory_agent with search_query first
- When user says "online" after choose_channel_agent, IMMEDIATELY call payment_agent (do NOT loop back)
- **PAYMENT AGENT TWO-CALL RULE**: 
  * Call payment_agent FIRST TIME with only customer_id (no payment_method) → shows options
  * Call payment_agent SECOND TIME with payment_method parameter when user selects → processes payment
  * After SECOND call returns "Payment Successful", IMMEDIATELY call fulfillment_agent
  * DO NOT call payment_agent a THIRD time
  * DO NOT ask user for anything after payment success
- **PAYMENT METHOD SELECTION RULE**: After payment_agent shows options, the user's NEXT message containing "upi"/"credit card"/"debit card"/"net banking" is their selection. IMMEDIATELY call payment_agent(payment_method="<method>"). DO NOT ask for confirmation.
- **OFFLINE FLOW CRITICAL RULE - CHECK CONVERSATION HISTORY**: 
  * STEP 1: User says "offline" → call inventory_agent(product_id=X) to show stores → stores displayed
  * STEP 2: Check last tool call - was it inventory_agent showing stores? If YES, then user's current message is store selection
  * STEP 2 ACTION: Call ONLY fulfillment_agent(purchase_type="offline", store_name=<user_message>)
  * STEP 2 FORBIDDEN: DO NOT call inventory_agent again, DO NOT call view_cart_agent, DO NOT call any other tool
  * The offline flow has exactly 2 tool calls: (1) inventory_agent → (2) fulfillment_agent → END
  * If you just showed stores in previous turn, next call MUST be fulfillment_agent with user's store selection
- For online: automatically call loyalty_agent → post_purchase_agent after fulfillment
- For offline: END after fulfillment (no loyalty/post-purchase)
- Clarify ambiguous requests before calling tools

**EXAMPLE FLOW:**
User: "Show me hoodies" 
→ inventory_agent(search_query="hoodies")
→ recommendation_agent(inventory_data)
→ "Want to add to cart?"

User: "Add product P123, quantity 2"
→ add_to_cart_agent(product_id="P123", quantity=2, customer_id="{customer_id}")
→ "Add more or view cart?"

User: "View cart"
→ view_cart_agent(customer_id="{customer_id}")
→ "Remove anything, add more, or proceed?"

User: "Proceed"
→ choose_channel_agent(customer_id="{customer_id}")
→ Shows ONLINE vs OFFLINE options

**ONLINE FLOW EXAMPLE:**
User: "Online"
→ CALL 1: payment_agent(customer_id="{customer_id}")  # NO payment_method parameter
→ Shows: "Choose payment: UPI, Credit Card, Debit Card, or Net Banking?"

User: "upi"
→ CALL 2: payment_agent(payment_method="upi", customer_id="{customer_id}")  # WITH payment_method
→ Returns: "Payment Successful!"
→ STOP calling payment_agent, now call fulfillment_agent:
→ fulfillment_agent(purchase_type="online", customer_id="{customer_id}")
→ loyalty_agent(order_id, customer_id) [AUTO]
→ post_purchase_agent(order_id) [AUTO]
→ END

**OFFLINE FLOW EXAMPLE (EXACT SEQUENCE):**
User: "Offline"
→ STAGE 1A: view_cart_agent(customer_id="{customer_id}")  # Get cart items to find first product_id
→ Identifies: Cart has PRD023 (Reebok Sportswear) and PRD045 (Gap Denim Shorts)
→ STAGE 1B: inventory_agent(product_id="PRD023")  # Use FIRST product_id from cart - CALL ONCE
→ Tool returns: "STR016 - South City Mall", "STR011 - ABFRL Store South City"
→ Agent displays stores to user
→ inventory_agent is NOW DONE - do not call it again

User: "STR011 - ABFRL Store South City"  # User selects a store
→ STAGE 2: fulfillment_agent(purchase_type="offline", store_name="STR011 - ABFRL Store South City", customer_id="{customer_id}")
→ ✅ CORRECT: Go directly to fulfillment_agent
→ ❌ WRONG: Do NOT call inventory_agent(product_id="STR011")
→ ❌ WRONG: Do NOT call view_cart_agent again
→ Tool returns: "In-Store Pickup Confirmed! Show this Order ID at the store kiosk."
→ END conversation

**OFFLINE FLOW SUMMARY**: 3 tool calls total = view_cart_agent (get cart) + inventory_agent (show stores) + fulfillment_agent (pickup)

**CRITICAL**: When user types "upi", "credit card", "debit card", or "net banking" after seeing payment options, that IS their payment method selection. Call payment_agent immediately with that method. Do NOT ask for confirmation.

Follow this workflow strictly for every customer interaction.
"""
    )

    # Prepend system message to all messages
    messages = [system_message] + state["messages"]

    # Let LLM handle all queries and decide which tools to call
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
        "loyalty_points": 0,
        "cart_items": []
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
    asyncio.run(test_conversation())
    print("\nTo run the agent:")
    print("  result = await run_agent('CUST001', 'Show me some hoodies')")
