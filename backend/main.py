from http.client import HTTPException
import logging
from crud import (
    product_crud, customer_crud, store_crud, order_history_crud,
    store_keeper_transaction_crud, cart_crud, admin_dashboard_data_crud,
    payload_crud, ProductCRUD, CustomerCRUD, CartCRUD
)
from store_kiosk_graph import (
    welcome_node,
    payment_prompt_node,
    payment_method_node,
    fulfillment_node,
    loyalty_node,
    post_purchase_node,
    kiosk_add_to_cart_agent,
)
from models import Customer, Product, Store, OrderHistory, StoreKeeperTransaction, AdminDashboardData, Payload, Feedback, Distance, Wishlist
from database import engine, get_db_session
from chat_database import save_message, get_conversation_history, clear_conversation_history
from langchain_core.messages import HumanMessage, AIMessage
from intelligent_agent_graph import run_agent, create_agent_graph, upsell_agent, inventory_agent, recommendation_agent
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
import tempfile
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict
import json
import asyncio
import re
import time
import random
from sqlmodel import Session, select, func
from dotenv import load_dotenv
from whatsapp import send_text_message, send_image_message, resolve_image_url, is_valid_whatsapp_message
from intelligent_whatsapp_graph import run_whatsapp_agent, send_whatsapp_text
from security import signature_required
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Import intelligent agent graph

# Import chat database

# Import database and CRUD modules

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000",
                   "http://127.0.0.1:5173", "http://127.0.0.1:5174"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve product images so Twilio can fetch them for WhatsApp media messages.
# Images live in  frontend/public/images/  →  mounted at /images/
_IMAGES_DIR = Path(__file__).resolve().parent.parent / \
    "frontend" / "public" / "images"
if _IMAGES_DIR.is_dir():
    app.mount("/images", StaticFiles(directory=str(_IMAGES_DIR)),
              name="product-images")


def load_products_from_db(skip: int = 0, limit: int = 100) -> List[Product]:
    """Load product data from database"""
    try:
        with get_db_session() as session:
            return product_crud.get_all(session, skip=skip, limit=limit)
    except Exception as e:
        print(f"Error loading products from database: {e}")
        return []


def load_customer_from_db(customer_id: str) -> Optional[Customer]:
    """Load customer data from database by ID"""
    try:
        with get_db_session() as session:
            return customer_crud.get_by_id(session, customer_id)
    except Exception as e:
        print(f"Error loading customer from database: {e}")
        return None


def get_product_from_db(product_id: str) -> Optional[Product]:
    """Get a product by ID from database"""
    try:
        with get_db_session() as session:
            return product_crud.get_by_id(session, product_id)
    except Exception as e:
        print(f"Error getting product from database: {e}")
        return None


def get_customer_orders_from_db(customer_id: str) -> List[OrderHistory]:
    """Get order history for a customer from database"""
    try:
        with get_db_session() as session:
            return order_history_crud.filter(
                session,
                {"customer_id": customer_id},
                order_by="order_dates",
                order_desc=True,
                limit=1000,
            )
    except Exception as e:
        print(f"Error getting orders from database: {e}")
        return []


def _tool_to_agent_map() -> Dict[str, str]:
    """Map LangChain tool names to timeline display labels."""
    return {
        # Tool names correspond to @tool functions in intelligent_agent_graph.py
        "customer_info_agent": "Customer Info Agent",
        "inventory_agent": "Inventory Agent",
        "recommendation_agent": "Recommendation Agent",
        "upsell_agent": "Upsell Agent",
        "add_to_cart_agent": "Add to Cart Agent",
        "view_cart_agent": "View Cart Agent",
        "remove_from_cart_agent": "Remove from Cart Agent",
        "choose_channel_agent": "Sales Agent",
        "payment_agent": "Payment Agent",
        "fulfillment_agent": "Fulfillment Agent",
        "loyalty_agent": "Loyalty Agent",
        "post_purchase_agent": "Post-Purchase Agent",
        "locate_us_agent": "Locate Us Agent",
    }


def _format_timeline_messages_from_langchain_messages(messages: List[Any]) -> List[Dict[str, str]]:
    """Extract a deduplicated timeline from LangChain messages containing tool calls."""
    timeline_messages: List[Dict[str, str]] = []
    seen_agents: set[str] = set()
    tool_to_agent_map = _tool_to_agent_map()

    try:
        from langchain_core.messages import AIMessage as LangChainAIMessage
    except Exception:
        LangChainAIMessage = None  # type: ignore

    for message in messages:
        if LangChainAIMessage is not None and isinstance(message, LangChainAIMessage):
            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = (tool_call or {}).get("name", "")
                    agent_name = tool_to_agent_map.get(tool_name, tool_name)
                    if agent_name and agent_name not in seen_agents:
                        seen_agents.add(agent_name)
                        timeline_messages.append({
                            "agent": agent_name,
                            "timestamp": "now",
                        })

    return timeline_messages


@app.get("/")
def greet():
    return {"message": "Hello world"}


@app.get("/productdatabase/")
def get_products_from_database():
    """Get all products from database"""
    products = load_products_from_db()

    if not products:
        return {"error": "Failed to load product data or no products found"}

    # Convert Product objects to dictionaries
    products_list = [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "category": p.category,
            "gender": p.gender,
            "price": p.price,
            "online_available": p.online_available,
            "offline_available": p.offline_available,
            "offline_stores": p.offline_stores,
            "store_ids": p.store_ids,
            "festival": p.festival,
            "season": p.season,
            "image_reference": p.image_reference,
            "loyalty_points": p.loyalty_points,
            "quantity": p.quantity
        }
        for p in products
    ]

    return {
        "total_products": len(products_list),
        "products": products_list
    }


@app.get("/productdatabase/{product_id}")
def get_product_by_id_from_database(product_id: str):
    """Get a specific product by ID from database"""
    product = get_product_from_db(product_id)

    if product is None:
        return {"error": f"Product with ID {product_id} not found"}

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "category": product.category,
        "gender": product.gender,
        "price": product.price,
        "online_available": product.online_available,
        "offline_available": product.offline_available,
        "offline_stores": product.offline_stores,
        "store_ids": product.store_ids,
        "festival": product.festival,
        "season": product.season,
        "image_reference": product.image_reference,
        "loyalty_points": product.loyalty_points,
        "quantity": product.quantity
    }


# @app.get("/productdatabase/category/{category}")
# def get_products_by_category(category: str):
#     """Get products by category using pandas"""
#     df = load_csv_data()

#     if df is None:
#         return {"error": "Failed to load CSV data"}

#     # Filter DataFrame by category (case insensitive)
#     category_products = df[df['category'].str.lower() == category.lower()]

#     if category_products.empty:
#         return {"error": f"No products found in category: {category}"}

#     products = category_products.to_dict('records')

#     return {
#         "category": category,
#         "total_products": len(products),
#         "products": products
#     }


# @app.get("/productdatabase/price-range/")
# def get_products_by_price_range(min_price: float = 0, max_price: float = 10000):
#     """Get products within a price range using pandas"""
#     df = load_csv_data()

#     if df is None:
#         return {"error": "Failed to load CSV data"}

#     # Filter DataFrame by price range
#     price_filtered = df[(df['price'] >= min_price) &
#                         (df['price'] <= max_price)]

#     if price_filtered.empty:
#         return {"error": f"No products found in price range {min_price} - {max_price}"}

#     products = price_filtered.to_dict('records')

#     return {
#         "price_range": f"{min_price} - {max_price}",
#         "total_products": len(products),
#         "products": products
#     }


@app.get("/api/customer/{customer_id}/orders")
def get_customer_orders_endpoint(customer_id: str):
    """Get customer's order history with product details"""
    # First get customer data
    customer = load_customer_from_db(customer_id)

    if customer is None:
        return {"error": f"Customer with ID {customer_id} not found"}

    # Get order history from database
    orders = get_customer_orders_from_db(customer_id)

    order_products = []
    for order in orders:
        # Get full product details
        product = get_product_from_db(order.product_id)
        if product:
            # Use final_price from order if available (includes discount + loyalty),
            # otherwise fall back to product's current price
            display_price = order.final_price if order.final_price is not None else product.price
            order_products.append({
                "transaction_id": order.transaction_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "price": display_price,
                "original_price": product.price,
                "discount_amount": order.discount_amount,
                "loyalty_applied": order.loyalty_applied,
                "final_price": order.final_price,
                "quantity": order.quantity,
                "size": order.size,
                "purchase_date": order.order_dates,
                "loyalty_points": order.loyalty_points,
                "image_reference": product.image_reference,
                "return_status": order.return_status,
                "feedback": order.feedback,
            })

    return {
        "customer_id": customer_id,
        "order_history": order_products
    }


class SubmitFeedbackModel(BaseModel):
    customer_id: str
    product_id: str
    feedback: int  # 1-5 star rating


@app.post("/api/orders/feedback")
def submit_order_feedback(data: SubmitFeedbackModel):
    """Submit star-rating feedback for a purchased product. Once set it cannot be changed."""
    if data.feedback < 1 or data.feedback > 5:
        raise HTTPException(
            status_code=400, detail="Feedback must be between 1 and 5")

    try:
        with Session(engine) as session:
            # Find the order(s) for this customer + product
            orders = session.exec(
                select(OrderHistory).where(
                    OrderHistory.customer_id == data.customer_id,
                    OrderHistory.product_id == data.product_id
                )
            ).all()

            if not orders:
                raise HTTPException(
                    status_code=404, detail="No order found for this customer and product")

            # Check if feedback already exists on any of the matching orders
            already_rated = any(o.feedback is not None for o in orders)
            if already_rated:
                raise HTTPException(
                    status_code=400, detail="Feedback already submitted for this product")

            # Update all matching orders with the feedback
            for order in orders:
                order.feedback = str(data.feedback)
                session.add(order)
            session.commit()

            return {"status": "success", "message": "Feedback submitted successfully", "feedback": data.feedback}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error submitting feedback: {str(e)}")


@app.get("/api/customer/{customer_id}/orders/recent")
def get_customer_recent_orders_endpoint(customer_id: str, days: int = 7):
    """Get customer's order history for the last N days (default 7).

    Data source: order_history table filtered by customer_id and order_dates.
    """
    if days <= 0:
        raise HTTPException(status_code=400, detail="days must be > 0")

    customer = load_customer_from_db(customer_id)
    if customer is None:
        return {"error": f"Customer with ID {customer_id} not found"}

    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    orders = get_customer_orders_from_db(customer_id)

    recent_orders: list[tuple[datetime, OrderHistory]] = []
    for order in orders:
        raw_date = (order.order_dates or "").strip()
        if not raw_date:
            continue
        try:
            parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except Exception:
            # If legacy/non-ISO formats exist, skip them rather than failing the whole request
            continue
        # Eligible for return: purchased between 24 hours ago and N days ago
        # (items purchased in the last 24 hours are NOT eligible)
        if parsed >= cutoff and parsed <= cutoff_24h:
            recent_orders.append((parsed, order))

    recent_orders.sort(key=lambda x: x[0], reverse=True)

    order_products = []
    for parsed, order in recent_orders:
        product = get_product_from_db(order.product_id)
        if product:
            display_price = order.final_price if order.final_price is not None else product.price
            order_products.append({
                "transaction_id": order.transaction_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "price": display_price,
                "original_price": product.price,
                "discount_amount": order.discount_amount,
                "loyalty_applied": order.loyalty_applied,
                "final_price": order.final_price,
                "quantity": order.quantity,
                "size": order.size,
                "purchase_date": order.order_dates,
                "loyalty_points": order.loyalty_points,
                "image_reference": product.image_reference,
                "return_status": order.return_status,
            })

    return {
        "customer_id": customer_id,
        "days": days,
        "order_history": order_products,
    }


@app.get("/api/customer/{customer_id}/{role_id}")
def get_customer_profile(customer_id: str, role_id: str):
    """Get customer or store profile by ID and role ID"""
    try:
        with get_db_session() as session:
            if str(role_id) == "2":  # Store Keeper
                # Fetch from stores table using customer_id as store_id
                store = store_crud.get_by_id(session, customer_id)
                if store is None:
                    return {"error": f"Store with ID {customer_id} not found"}
                return {
                    "store_id": store.store_id,
                    "store_name": store.store_name,
                    "address": store.address,
                    "phone": store.store_phone,
                    "manager": store.manager_name,
                    # "store_type": store.store_type,
                    # "products": store.products,
                    "role_id": 2
                }
            else:
                customer = customer_crud.get_by_id(session, customer_id)
                if customer is None:
                    return {"error": f"Customer with ID {customer_id} not found"}
                # Check role_id matches
                if not hasattr(customer, 'role_id'):
                    return {"error": "Customer record does not have a role_id field"}
                if str(customer.role_id) != str(role_id):
                    return {"error": f"Role ID {role_id} does not match for customer {customer_id}"}

                # Parse order history (comma-separated product IDs)
                order_history = []
                if customer.order_history:
                    product_ids = customer.order_history.split('|')
                    order_history = [pid.strip() for pid in product_ids]

                # Parse pending orders
                pending_orders = []
                if customer.pending_orders:
                    product_ids = customer.pending_orders.split('|')
                    pending_orders = [pid.strip() for pid in product_ids]

                return {
                    "customer_id": customer.customer_id,
                    "customer_name": customer.customer_name,
                    "gender": customer.gender or '',
                    "phone": customer.phone or '',
                    "address": customer.address or '',
                    "loyalty_points": customer.loyalty_points,
                    "role_id": customer.role_id,
                    "order_history": order_history,
                    "pending_orders": pending_orders,
                    "customer_type": customer.customer_type or ''
                }
    except Exception as e:
        return {"error": f"Error fetching customer/store: {str(e)}"}


@app.get("/api/products/multiple/{product_ids}")
def get_multiple_products(product_ids: str):
    """Get multiple products by pipe-separated product IDs"""
    # Split product IDs and clean them
    ids_list = [pid.strip() for pid in product_ids.split('|')]

    products = []
    for pid in ids_list:
        product = get_product_from_db(pid)
        if product:
            products.append({
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "gender": product.gender,
                "price": product.price,
                "online_available": product.online_available,
                "offline_available": product.offline_available,
                "image_reference": product.image_reference,
                "loyalty_points": product.loyalty_points,
                "quantity": product.quantity
            })

    return {
        "products": products,
        "total_count": len(products)
    }


@app.get("/api/feedback/multiple/{product_ids}")
def get_multiple_feedback_reviews(product_ids: str):
    """Get product reviews from feedback table by pipe-separated product IDs"""
    ids_list = [pid.strip() for pid in product_ids.split('|') if pid.strip()]
    if not ids_list:
        return {"reviews": {}, "total_count": 0}

    try:
        with get_db_session() as session:
            feedback_rows = session.exec(
                select(Feedback).where(Feedback.product_id.in_(ids_list))
            ).all()

        reviews = {row.product_id: row.review for row in feedback_rows}
        return {"reviews": reviews, "total_count": len(reviews)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching feedback reviews: {str(e)}")


@app.get("/api/admin/dashboard")
def get_admin_dashboard_data(time_range: str = "1month"):
    """
    Get comprehensive admin dashboard analytics including:
    - Total customers count
    - Total products sold
    - Total retail stores
    - Online vs Offline transactions (based on time_range)
    - Offline purchases per store

    Data sources:
    - Online orders  → order_history table
    - Offline orders → store_keeper_transactions table
    - Store count    → stores table

    Args:
        time_range: Filter by time range - '7days', '1month', or 'all' (default: '1month')
    """
    try:
        with get_db_session() as session:
            from datetime import datetime, timedelta
            from collections import defaultdict

            # ---------- helper: parse date string ----------
            def _parse_date(date_str):
                if not date_str:
                    return None
                s = str(date_str).strip()
                # Truncate microseconds / fractional seconds
                if '.' in s:
                    s = s[:s.index('.')]
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                            "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                    try:
                        return datetime.strptime(s, fmt)
                    except Exception:
                        continue
                return None

            # ---------- counts ----------
            total_customers = session.exec(
                select(func.count(Customer.customer_id))
            ).one()

            total_stores = session.exec(
                select(func.count(Store.store_id))
            ).one()

            # ---------- online orders from order_history ----------
            all_online_orders = session.exec(select(OrderHistory)).all()

            # ---------- offline orders from store_keeper_transactions ----------
            all_offline_orders = session.exec(
                select(StoreKeeperTransaction).where(
                    func.lower(StoreKeeperTransaction.mode) == "offline"
                )
            ).all()

            # ---------- look-ups for address / phone / price ----------
            customer_map = {
                c.customer_id: c
                for c in session.exec(select(Customer)).all()
            }
            product_map = {
                p.product_id: p
                for p in session.exec(select(Product)).all()
            }

            # ---------- build unified transaction dicts ----------
            unified_transactions = []

            for order in all_online_orders:
                amount = order.final_price
                if not amount:
                    prod = product_map.get(order.product_id)
                    amount = (prod.price * order.quantity) if prod else 0
                cust = customer_map.get(order.customer_id)
                status = "Complete"
                if order.return_status and order.return_status.lower() == "returned":
                    status = "Returned"
                elif order.return_status and order.return_status.lower() == "initiated":
                    status = "Return Initiated"
                unified_transactions.append({
                    "id": order.transaction_id,
                    "date": order.order_dates,
                    "user_name": order.customer_name,
                    "product": order.product_name,
                    "qty": order.quantity,
                    "mode": "Online",
                    "store_name": "Online",
                    "status": status,
                    "amount": round(amount, 2) if amount else 0,
                    "address": cust.address if cust else "N/A",
                    "phone": cust.phone if cust else "N/A",
                })

            for tx in all_offline_orders:
                unified_transactions.append({
                    "id": tx.id,
                    "date": tx.date,
                    "user_name": tx.user_name,
                    "product": tx.product,
                    "qty": tx.qty,
                    "mode": "Offline",
                    "store_name": tx.store_name,
                    "status": tx.status,
                    "amount": tx.amount,
                    "address": tx.address,
                    "phone": tx.phone,
                })

            # ---------- total products sold (all time) ----------
            total_products_sold = sum(t["qty"] for t in unified_transactions)

            # ---------- date threshold ----------
            now = datetime.now()
            date_threshold = None
            time_period_label = "All Time"

            if time_range == "7days":
                date_threshold = now - timedelta(days=7)
                time_period_label = "Last 7 Days"
            elif time_range == "1month":
                date_threshold = now - timedelta(days=30)
                time_period_label = "Last 1 Month"

            # ---------- filter & aggregate ----------
            online_transactions = []
            offline_transactions = []
            store_purchases = defaultdict(int)
            total_revenue = 0
            online_revenue = 0
            offline_revenue = 0

            for tx in unified_transactions:
                tx_date = _parse_date(tx["date"])
                if tx_date is None:
                    continue

                if date_threshold is None or tx_date >= date_threshold:
                    if tx["mode"].lower() == "online":
                        online_transactions.append(tx)
                        online_revenue += tx["amount"]
                    else:
                        offline_transactions.append(tx)
                        offline_revenue += tx["amount"]
                        store_purchases[tx["store_name"]] += tx["qty"]
                    total_revenue += tx["amount"]

            total_transactions = len(
                online_transactions) + len(offline_transactions)
            avg_transaction_value = (
                total_revenue / total_transactions if total_transactions > 0 else 0
            )

            # ---------- offline purchases per store ----------
            offline_purchases_per_store = [
                {"store_name": name, "purchases_count": count}
                for name, count in sorted(
                    store_purchases.items(), key=lambda x: x[1], reverse=True
                )
            ]

            # ---------- online / offline percentages ----------
            online_percentage = (
                len(online_transactions) / total_transactions * 100
                if total_transactions > 0 else 0
            )
            offline_percentage = (
                len(offline_transactions) / total_transactions * 100
                if total_transactions > 0 else 0
            )

            # ---------- monthly trends (filtered) ----------
            monthly_online = defaultdict(int)
            monthly_offline = defaultdict(int)

            for tx in online_transactions + offline_transactions:
                tx_date = _parse_date(tx["date"])
                if tx_date is None:
                    continue
                month_key = tx_date.strftime("%b")
                if tx["mode"].lower() == "online":
                    monthly_online[month_key] += 1
                else:
                    monthly_offline[month_key] += 1

            month_order = ["Jan", "Feb", "Mar", "Apr", "May",
                           "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            monthly_trends = []
            for month in month_order:
                if month in monthly_online or month in monthly_offline:
                    monthly_trends.append({
                        "month": month,
                        "online": monthly_online.get(month, 0),
                        "offline": monthly_offline.get(month, 0),
                        "total": monthly_online.get(month, 0) + monthly_offline.get(month, 0),
                    })

            # ---------- all transactions list (for table view) ----------
            all_transactions_list = list(unified_transactions)

            # Sort by date (most recent first)
            try:
                all_transactions_list.sort(
                    key=lambda x: _parse_date(x["date"]) or datetime.min,
                    reverse=True,
                )
            except Exception:
                pass

            return {
                "summary": {
                    "total_customers": total_customers,
                    "total_products_sold": total_products_sold,
                    "total_retail_stores": total_stores,
                    "total_transactions": total_transactions,
                    "total_revenue": round(total_revenue, 2),
                    "avg_transaction_value": round(avg_transaction_value, 2),
                },
                "transactions_overview": {
                    "time_period": time_period_label,
                    "time_range": time_range,
                    "online": {
                        "count": len(online_transactions),
                        "percentage": round(online_percentage, 1),
                        "revenue": round(online_revenue, 2),
                    },
                    "offline": {
                        "count": len(offline_transactions),
                        "percentage": round(offline_percentage, 1),
                        "revenue": round(offline_revenue, 2),
                    },
                },
                "monthly_trends": monthly_trends,
                "total_online_transactions": sum(monthly_online.values()),
                "total_offline_transactions": sum(monthly_offline.values()),
                "offline_purchases_per_store": offline_purchases_per_store,
                "transactions": all_transactions_list,
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error fetching admin dashboard data: {str(e)}",
            "summary": {
                "total_customers": 0,
                "total_products_sold": 0,
                "total_retail_stores": 0,
                "total_transactions_past_month": 0,
                "total_revenue": 0,
                "avg_transaction_value": 0,
            },
            "transactions_overview": {
                "time_period": "Past 1 Month",
                "online": {"count": 0, "percentage": 0, "revenue": 0},
                "offline": {"count": 0, "percentage": 0, "revenue": 0},
            },
            "offline_purchases_per_store": [],
        }


@app.get("/api/admin/ai-insights")
def get_admin_ai_insights(time_range: str = "1month"):
    """
    Get AI-powered insights and recommendations for the admin dashboard.
    Computes per-store performance metrics from order_history + store_keeper_transactions,
    then uses LLM to generate business insights and recommendations.

    Args:
        time_range: Filter by time range - '7days', '1month', or 'all' (default: '1month')
    """
    try:
        from langchain_openai import ChatOpenAI
        from datetime import datetime, timedelta
        from collections import defaultdict

        # ---------- helper: parse date string ----------
        def _parse_date(date_str):
            if not date_str:
                return None
            s = str(date_str).strip()
            if '.' in s:
                s = s[:s.index('.')]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                        "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(s, fmt)
                except Exception:
                    continue
            return None

        with get_db_session() as session:
            # ---------- load data ----------
            all_online_orders = session.exec(select(OrderHistory)).all()
            all_offline_orders = session.exec(
                select(StoreKeeperTransaction).where(
                    func.lower(StoreKeeperTransaction.mode) == "offline"
                )
            ).all()
            all_stores = session.exec(select(Store)).all()
            store_info_map = {s.store_name: s for s in all_stores}
            # Also index by store_id for fallback matching
            store_id_map = {s.store_id: s for s in all_stores}

            product_map = {
                p.product_id: p
                for p in session.exec(select(Product)).all()
            }

            # ---------- build unified transaction dicts ----------
            unified_transactions = []

            for order in all_online_orders:
                amount = order.final_price
                if not amount:
                    prod = product_map.get(order.product_id)
                    amount = (prod.price * order.quantity) if prod else 0
                unified_transactions.append({
                    "date": order.order_dates,
                    "user_name": order.customer_name,
                    "product": order.product_name,
                    "qty": order.quantity,
                    "mode": "Online",
                    "store_name": "Online",
                    "amount": round(amount, 2) if amount else 0,
                    "status": "Complete" if not order.return_status else order.return_status,
                })

            for tx in all_offline_orders:
                unified_transactions.append({
                    "date": tx.date,
                    "user_name": tx.user_name,
                    "product": tx.product,
                    "qty": tx.qty,
                    "mode": "Offline",
                    "store_name": tx.store_name,
                    "amount": tx.amount,
                    "status": tx.status,
                })

            # ---------- date threshold ----------
            now = datetime.now()
            date_threshold = None
            time_period_label = "All Time"

            if time_range == "7days":
                date_threshold = now - timedelta(days=7)
                time_period_label = "Last 7 Days"
            elif time_range == "1month":
                date_threshold = now - timedelta(days=30)
                time_period_label = "Last 1 Month"

            # ---------- filter & aggregate ----------
            filtered_transactions = []
            online_count = 0
            offline_count = 0
            online_revenue = 0
            offline_revenue = 0
            # Per-store detailed metrics
            store_metrics = defaultdict(lambda: {
                "revenue": 0, "orders": 0, "customers": set(),
                "complete_count": 0, "total_count": 0
            })
            product_performance = defaultdict(
                lambda: {"count": 0, "revenue": 0})
            customer_frequency = defaultdict(int)

            for tx in unified_transactions:
                tx_date = _parse_date(tx["date"])
                if tx_date is None:
                    continue

                if date_threshold is None or tx_date >= date_threshold:
                    filtered_transactions.append(tx)

                    if tx["mode"].lower() == "online":
                        online_count += 1
                        online_revenue += tx["amount"]
                    else:
                        offline_count += 1
                        offline_revenue += tx["amount"]
                        sname = tx["store_name"]
                        store_metrics[sname]["revenue"] += tx["amount"]
                        store_metrics[sname]["orders"] += tx["qty"]
                        store_metrics[sname]["customers"].add(tx["user_name"])
                        store_metrics[sname]["total_count"] += 1
                        status_lower = (tx.get("status") or "").lower()
                        if status_lower in ("complete", "completed"):
                            store_metrics[sname]["complete_count"] += 1

                    product_performance[tx["product"]]["count"] += tx["qty"]
                    product_performance[tx["product"]
                                        ]["revenue"] += tx["amount"]
                    customer_frequency[tx["user_name"]] += 1

            total_transactions = len(filtered_transactions)
            total_revenue = online_revenue + offline_revenue
            avg_transaction = total_revenue / \
                total_transactions if total_transactions > 0 else 0
            online_percentage = (
                online_count / total_transactions * 100) if total_transactions > 0 else 0

            # ---------- build store performance list ----------
            store_performance_list = []
            for sname, m in store_metrics.items():
                cust_count = len(m["customers"])
                aov = round(m["revenue"] / m["orders"],
                            0) if m["orders"] > 0 else 0
                success_rate = round(
                    m["complete_count"] / m["total_count"] * 100, 1
                ) if m["total_count"] > 0 else 0

                # Determine rating based on revenue & orders
                if m["revenue"] >= 200000 and m["orders"] >= 100:
                    rating = "EXCELLENT"
                elif m["revenue"] >= 150000 and m["orders"] >= 70:
                    rating = "GOOD"
                elif m["revenue"] >= 80000 and m["orders"] >= 30:
                    rating = "AVERAGE"
                else:
                    rating = "POOR"

                # Lookup manager from stores table
                store_obj = store_info_map.get(sname)
                manager = store_obj.manager_name if store_obj else "N/A"

                store_performance_list.append({
                    "store_name": sname,
                    "manager": manager,
                    "revenue": round(m["revenue"], 2),
                    "orders": m["orders"],
                    "customers": cust_count,
                    "aov": int(aov),
                    "success_rate": success_rate,
                    "rating": rating,
                })

            # Sort by revenue descending
            store_performance_list.sort(
                key=lambda x: x["revenue"], reverse=True)
            # Filter out stores with empty/blank names
            store_performance_list = [
                s for s in store_performance_list if s["store_name"].strip()]

            # Identify top performer & needs-attention store
            top_performer = store_performance_list[0] if store_performance_list else None
            needs_attention = store_performance_list[-1] if len(
                store_performance_list) > 1 else None

            # Poor performing stores
            poor_stores = [
                s for s in store_performance_list if s["rating"] == "POOR"]

            # ---------- top products, stores, customers for LLM ----------
            top_products = sorted(product_performance.items(),
                                  key=lambda x: x[1]["revenue"], reverse=True)[:5]
            top_stores_sorted = sorted(store_metrics.items(),
                                       key=lambda x: x[1]["revenue"], reverse=True)[:5]
            bottom_stores_sorted = sorted(store_metrics.items(),
                                          key=lambda x: x[1]["revenue"])[:5]
            top_customers = sorted(customer_frequency.items(),
                                   key=lambda x: x[1], reverse=True)[:5]

            # ---------- LLM prompt ----------
            total_offline_revenue = offline_revenue
            avg_store_perf_gap = 0
            if store_performance_list:
                avg_rev = sum(
                    s["revenue"] for s in store_performance_list) / len(store_performance_list)
                avg_store_perf_gap = round(avg_rev / 1000)

            best_aov = max((s["aov"]
                           for s in store_performance_list), default=0)
            avg_aov = round(sum(s["aov"] for s in store_performance_list) /
                            len(store_performance_list)) if store_performance_list else 0
            aov_improvement_potential = round(
                (best_aov - avg_aov) / avg_aov * 100) if avg_aov > 0 else 0

            data_summary = f"""
Analyze the following retail dashboard data for {time_period_label}:

OVERALL METRICS:
- Total Transactions: {total_transactions:,}
- Total Revenue: ₹{total_revenue:,.2f}
- Average Transaction Value: ₹{avg_transaction:,.2f}
- Online Sales: {online_count:,} transactions (₹{online_revenue:,.2f})
- Offline Sales: {offline_count:,} transactions (₹{offline_revenue:,.2f})
- Online Percentage: {online_percentage:.1f}%

TOP PERFORMING STORES (Offline):
{chr(10).join([f"- {store}: {data['revenue']:.0f} revenue, {data['orders']} orders, {len(data['customers'])} customers" for store, data in top_stores_sorted])}

BOTTOM PERFORMING STORES (Offline):
{chr(10).join([f"- {store}: {data['revenue']:.0f} revenue, {data['orders']} orders, {len(data['customers'])} customers" for store, data in bottom_stores_sorted])}

TOP PERFORMING PRODUCTS:
{chr(10).join([f"- {prod}: {data['count']} units sold, ₹{data['revenue']:,.2f} revenue" for prod, data in top_products])}

TOP CUSTOMERS (by frequency):
{chr(10).join([f"- {customer}: {count} purchases" for customer, count in top_customers])}

Provide business insights in the following strict JSON format ONLY (no extra text):
{{
  "overview": "Brief performance summary in 2-3 sentences covering growth trends",
  "market_opportunities": [
    "Total offline revenue: ₹{total_offline_revenue:,.0f}",
    "Average store performance gap: {avg_store_perf_gap}K",
    "Potential for {aov_improvement_potential}% AOV improvement across stores"
  ],
  "strategic_focus_areas": [
    "specific strategic recommendation 1",
    "specific strategic recommendation 2",
    "specific strategic recommendation 3",
    "specific strategic recommendation 4"
  ],
  "trend_analysis": {{
    "direction": "growth or decline",
    "summary": "2-3 sentences about revenue/order trends over time",
    "key_factors": ["factor 1", "factor 2", "factor 3"]
  }},
  "poor_store_actions": [
    "Urgent: Review operational efficiency and costs",
    "Implement digital marketing and customer engagement",
    "Consider staff retraining or management changes",
    "Improve order fulfillment processes",
    "Focus on upselling and cross-selling strategies"
  ],
  "top_performer_success_factors": [
    "factor that makes the top store successful 1",
    "factor 2",
    "factor 3"
  ],
  "needs_attention_improvement_areas": [
    "area to improve for the weakest store 1",
    "area 2",
    "area 3"
  ]
}}
"""

            # Initialize LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )

            response = llm.invoke(data_summary)

            # Parse LLM response
            try:
                response_text = response.content
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    insights_data = json.loads(json_match.group())
                else:
                    insights_data = {
                        "overview": response_text[:200],
                        "market_opportunities": [],
                        "strategic_focus_areas": [],
                        "trend_analysis": {"direction": "unknown", "summary": "Unable to determine", "key_factors": []},
                        "poor_store_actions": [],
                        "top_performer_success_factors": [],
                        "needs_attention_improvement_areas": [],
                    }
            except Exception as parse_error:
                print(f"Error parsing LLM response: {parse_error}")
                insights_data = {
                    "overview": "Analysis completed but unable to format insights properly.",
                    "market_opportunities": [],
                    "strategic_focus_areas": [],
                    "trend_analysis": {"direction": "unknown", "summary": "Unable to determine trends.", "key_factors": []},
                    "poor_store_actions": [],
                    "top_performer_success_factors": [],
                    "needs_attention_improvement_areas": [],
                }

            return {
                "insights": insights_data,
                "store_performance": store_performance_list,
                "top_performer": top_performer,
                "needs_attention": needs_attention,
                "poor_stores": poor_stores,
                "time_period": time_period_label,
                "data_summary": {
                    "total_transactions": total_transactions,
                    "total_revenue": round(total_revenue, 2),
                    "total_offline_revenue": round(offline_revenue, 2),
                    "avg_transaction_value": round(avg_transaction, 2),
                    "online_percentage": round(online_percentage, 1),
                },
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error generating AI insights: {str(e)}",
            "insights": {
                "overview": "Unable to generate insights at this time.",
                "market_opportunities": [],
                "strategic_focus_areas": [],
                "trend_analysis": {"direction": "unknown", "summary": "", "key_factors": []},
                "poor_store_actions": [],
                "top_performer_success_factors": [],
                "needs_attention_improvement_areas": [],
            },
            "store_performance": [],
            "top_performer": None,
            "needs_attention": None,
            "poor_stores": [],
        }


@app.get("/api/store/{store_id}/transactions")
def get_store_transactions(store_id: str, time_range: str = "all"):
    """
    Get transaction history for a specific store with product analytics (offline mode only)

    Args:
        store_id: Store ID
        time_range: Filter by time range - 'daily', 'weekly', 'monthly', or 'all' (default)
    """
    try:
        from datetime import datetime, timedelta

        with get_db_session() as session:
            # Fetch store details
            store = store_crud.get_by_id(session, store_id)

            if store is None:
                return {
                    "error": f"Store with ID {store_id} not found",
                    "store_name": "Unknown Store",
                    "transactions": [],
                    "products_sold": []
                }

            # Fetch all transactions for this store
            transactions = store_keeper_transaction_crud.filter(
                session,
                {'store_id': store_id},
                operators={'store_id': '=='}
            )

            # Calculate date threshold based on time_range
            now = datetime.utcnow()
            date_threshold = None

            if time_range == "daily":
                date_threshold = now - timedelta(days=1)
            elif time_range == "weekly":
                date_threshold = now - timedelta(weeks=1)
            elif time_range == "monthly":
                date_threshold = now - timedelta(days=30)

            # Filter for OFFLINE mode only and apply date range
            filtered_transactions = []
            for tx in transactions:
                # Only include offline mode transactions
                if tx.mode and tx.mode.lower() != "online":
                    # Apply date filter if specified
                    if date_threshold:
                        try:
                            # Parse transaction date - handle multiple formats
                            tx_date = None
                            # Try M/D/YYYY format first (e.g., "12/5/2025")
                            try:
                                tx_date = datetime.strptime(
                                    tx.date, "%m/%d/%Y")
                            except:
                                # Try ISO format
                                try:
                                    tx_date = datetime.fromisoformat(
                                        tx.date.replace('Z', '+00:00'))
                                except:
                                    pass

                            if tx_date and tx_date >= date_threshold:
                                filtered_transactions.append(tx)
                        except Exception as e:
                            print(f"Date parsing error for {tx.date}: {e}")
                            # Skip transactions with unparseable dates when filter is active
                            pass
                    else:
                        # No date filter, include all offline transactions
                        filtered_transactions.append(tx)

            # Format transaction data and calculate product analytics
            transaction_list = []
            product_sales = {}  # Dictionary to aggregate product quantities

            for tx in filtered_transactions:
                transaction_list.append({
                    "id": tx.id,
                    "date": tx.date,
                    "user_name": tx.user_name,
                    "product": tx.product,
                    "product_id": tx.product_id,
                    "qty": tx.qty,
                    "mode": tx.mode,
                    "status": tx.status,
                    "amount": tx.amount,
                    "address": tx.address,
                    "phone": tx.phone,
                    "customer_id": tx.customer_id
                })

                # Aggregate product quantities
                product_name = tx.product
                if product_name in product_sales:
                    product_sales[product_name] += tx.qty
                else:
                    product_sales[product_name] = tx.qty

            # Convert product sales to list format for frontend
            products_sold = [
                {
                    "product_name": product,
                    "total_quantity": quantity
                }
                for product, quantity in product_sales.items()
            ]

            # Sort by quantity descending
            products_sold.sort(key=lambda x: x['total_quantity'], reverse=True)

            return {
                "store_id": store.store_id,
                "store_name": store.store_name,
                "store_address": store.address,
                "manager_name": store.manager_name,
                "time_range": time_range,
                "total_transactions": len(transaction_list),
                "transactions": transaction_list,
                "products_sold": products_sold
            }

    except Exception as e:
        return {
            "error": f"Error fetching store transactions: {str(e)}",
            "store_name": "Unknown Store",
            "transactions": [],
            "products_sold": []
        }


@app.get("/api/store/{store_id}/daily-orders")
def get_store_daily_orders(store_id: str, time_range: str = "weekly"):
    """
    Get daily order counts for a specific store

    Args:
        store_id: Store ID
        time_range: 'daily' (24h), 'weekly' (7d), or 'monthly' (30d)
    """
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict

        with get_db_session() as session:
            store = store_crud.get_by_id(session, store_id)
            if not store:
                return {"error": f"Store {store_id} not found"}

            # Calculate date range
            now = datetime.utcnow()
            if time_range == "daily":
                date_threshold = now - timedelta(days=1)
                days_count = 1
                title = "Last 24 Hours"
            elif time_range == "monthly":
                date_threshold = now - timedelta(days=30)
                days_count = 30
                title = "Past Month"
            else:  # weekly
                date_threshold = now - timedelta(days=7)
                days_count = 7
                title = "Last 7 Days"

            # Fetch transactions
            transactions = store_keeper_transaction_crud.filter(
                session,
                {'store_id': store_id},
                operators={'store_id': '=='}
            )

            # Count orders by day
            daily_counts = defaultdict(int)
            total_orders = 0

            for tx in transactions:
                if tx.mode and tx.mode.lower() != "online":
                    try:
                        tx_date = None
                        try:
                            tx_date = datetime.strptime(tx.date, "%m/%d/%Y")
                        except:
                            try:
                                tx_date = datetime.fromisoformat(
                                    tx.date.replace('Z', '+00:00'))
                            except:
                                pass

                        if tx_date and tx_date >= date_threshold:
                            day_key = tx_date.strftime("%Y-%m-%d")
                            daily_counts[day_key] += 1
                            total_orders += 1
                    except:
                        pass

            # Format daily orders with percentages
            daily_orders = []
            for date_str, count in sorted(daily_counts.items()):
                percentage = (count / total_orders *
                              100) if total_orders > 0 else 0
                daily_orders.append({
                    "date": date_str,
                    "count": count,
                    "percentage": round(percentage, 1)
                })

            # Calculate peak day and average
            peak_day = max(daily_counts.items(),
                           key=lambda x: x[1]) if daily_counts else (None, 0)
            avg_daily = total_orders / len(daily_counts) if daily_counts else 0

            return {
                "store_id": store.store_id,
                "store_name": store.store_name,
                "total_orders": total_orders,
                "time_range": time_range,
                "title": title,
                "daily_orders": daily_orders,
                "peak_day": {"date": peak_day[0], "count": peak_day[1]} if peak_day[0] else None,
                "avg_daily": round(avg_daily, 1),
                "growth": None
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/store/{store_id}/pending-orders")
def get_store_pending_orders(store_id: str):
    """
    Get pending cart orders for a specific store.
    Queries the cart table where store_id matches and status is 'pending'.
    """
    try:
        with get_db_session() as session:
            # Query cart items with matching store_id and pending status
            pending_items = cart_crud.filter(
                session,
                filters={"store_id": store_id, "status": "pending"},
                operators={"store_id": "==", "status": "=="},
                limit=200,
            )

            if not pending_items:
                return {"pending_orders": [], "total_pending": 0}

            details = []
            for item in pending_items:
                product = product_crud.get_by_id(
                    session, item.product_id) if item.product_id else None
                customer = customer_crud.get_by_id(
                    session, item.customer_id) if item.customer_id else None
                details.append({
                    "order_id": item.order_id,
                    "customer_id": item.customer_id or "N/A",
                    "customer_name": customer.customer_name if customer else "N/A",
                    "product_id": item.product_id or "N/A",
                    "product_name": product.product_name if product else "N/A",
                    "quantity": getattr(item, "quantity", 1),
                    "size": item.size or "N/A",
                    "channel": item.channel or "N/A",
                    "status": item.status,
                    "created_at": item.created_at or "N/A",
                })

            return {
                "pending_orders": details,
                "total_pending": len(details),
            }
    except Exception as e:
        return {"pending_orders": [], "total_pending": 0, "error": str(e)}


@app.get("/api/store/{store_id}/ai-insights")
async def get_store_ai_insights(store_id: str, time_range: str = "monthly"):
    """
    Generate AI-powered insights for a store using LLM

    Args:
        store_id: Store ID
        time_range: Filter by time range - 'daily', 'weekly', 'monthly', or 'all' (default: monthly)
    """
    try:
        from langchain_openai import ChatOpenAI
        from datetime import datetime, timedelta
        import json

        with get_db_session() as session:
            # Fetch store details
            store = store_crud.get_by_id(session, store_id)

            if store is None:
                return {"error": f"Store with ID {store_id} not found"}

            # Get store transactions using the existing endpoint logic
            transactions = store_keeper_transaction_crud.filter(
                session,
                {'store_id': store_id},
                operators={'store_id': '=='}
            )

            # Calculate date threshold based on time_range
            now = datetime.utcnow()
            date_threshold = None

            if time_range == "daily":
                date_threshold = now - timedelta(days=1)
            elif time_range == "weekly":
                date_threshold = now - timedelta(weeks=1)
            elif time_range == "monthly":
                date_threshold = now - timedelta(days=30)

            # Filter for OFFLINE mode only and apply date range
            filtered_transactions = []
            for tx in transactions:
                if tx.mode and tx.mode.lower() != "online":
                    if date_threshold:
                        try:
                            tx_date = None
                            try:
                                tx_date = datetime.strptime(
                                    tx.date, "%m/%d/%Y")
                            except:
                                try:
                                    tx_date = datetime.fromisoformat(
                                        tx.date.replace('Z', '+00:00'))
                                except:
                                    pass

                            if tx_date and tx_date >= date_threshold:
                                filtered_transactions.append(tx)
                        except:
                            pass
                    else:
                        filtered_transactions.append(tx)

            # Calculate analytics
            product_sales = {}
            successful_transactions = 0
            failed_transactions = 0
            total_revenue = 0

            for tx in filtered_transactions:
                product_name = tx.product
                if product_name in product_sales:
                    product_sales[product_name] += tx.qty
                else:
                    product_sales[product_name] = tx.qty

                if tx.status == "Success":
                    successful_transactions += 1
                    total_revenue += tx.amount
                elif tx.status == "Failed":
                    failed_transactions += 1

            # Sort products by sales
            sorted_products = sorted(
                product_sales.items(), key=lambda x: x[1], reverse=True)
            top_products = sorted_products[:5] if len(
                sorted_products) >= 5 else sorted_products
            bottom_products = sorted_products[-5:] if len(
                sorted_products) >= 5 else []

            # Prepare data for LLM
            store_data = {
                "store_id": store.store_id,
                "store_name": store.store_name,
                "manager": store.manager_name,
                "address": store.address,
                "time_range": time_range,
                "total_transactions": len(filtered_transactions),
                "successful_transactions": successful_transactions,
                "failed_transactions": failed_transactions,
                "total_revenue": total_revenue,
                "top_selling_products": [{"product": p[0], "quantity": p[1]} for p in top_products],
                "lowest_selling_products": [{"product": p[0], "quantity": p[1]} for p in bottom_products]
            }

            # Create LLM prompt
            prompt = f"""You are an AI retail analytics advisor. Analyze the following store performance data and provide detailed insights.

Store Data:
{json.dumps(store_data, indent=2)}

Generate a comprehensive analysis with the following sections. Return ONLY a valid JSON object with these exact keys:

{{
  "performance_overview": "A brief 2-3 sentence overview of the store's overall performance",
  "key_metrics": [
    {{"metric": "Success Rate", "value": "XX%", "insight": "brief insight"}},
    {{"metric": "Revenue", "value": "$X,XXX", "insight": "brief insight"}},
    {{"metric": "Transaction Volume", "value": "XXX", "insight": "brief insight"}}
  ],
  "top_products": [
    {{"product": "product name", "quantity": X, "recommendation": "why it's performing well"}}
  ],
  "underperforming_products": [
    {{"product": "product name", "quantity": X, "recommendation": "actionable improvement suggestion"}}
  ],
  "strategic_recommendations": [
    {{"title": "Recommendation Title", "description": "Detailed actionable recommendation", "priority": "High/Medium/Low"}},
    {{"title": "Another Recommendation", "description": "Another detailed recommendation", "priority": "High/Medium/Low"}}
  ],
  "customer_attraction_strategies": [
    {{"strategy": "Strategy name", "description": "How to implement this strategy", "expected_impact": "Expected outcome"}}
  ],
  "loss_minimization": [
    {{"area": "Area of concern", "suggestion": "Specific action to reduce losses", "potential_savings": "Estimated impact"}}
  ]
}}

Important: Return ONLY the JSON object, no additional text or markdown formatting."""

            # Initialize LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=2000
            )

            # Get LLM response
            response = await llm.ainvoke(prompt)

            # Parse the JSON response
            try:
                insights = json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from markdown code blocks
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                insights = json.loads(content.strip())

            return {
                "store_id": store.store_id,
                "store_name": store.store_name,
                "time_range": time_range,
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat()
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error generating AI insights: {str(e)}",
            "insights": None
        }


# ============ Chatbot Endpoints ============

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")  # Allow extra fields

    customer_id: str
    message: str
    conversation_history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    response: str
    agent_calls: List[str] = []


kiosk_sessions: Dict[str, Dict[str, Any]] = {}


def _init_kiosk_state(customer_id: str) -> Dict[str, Any]:
    return {
        "messages": [],
        "customer_id": customer_id,
        "order_id": None,
        "product_id": None,
        "store_id": None,
        "payment_completed": False,
        "fulfillment_done": False,
        "loyalty_done": False,
        "post_purchase_done": False,
        "welcome_done": False,
        "payment_prompt_done": False,
    }


def _merge_kiosk_result(state: Dict[str, Any], result: Dict[str, Any]) -> List[str]:
    messages = result.get("messages", [])
    if messages:
        state["messages"].extend(messages)

    for key, value in result.items():
        if key == "messages":
            continue
        state[key] = value

    ai_texts = []
    for message in messages:
        if isinstance(message, AIMessage) and message.content:
            ai_texts.append(message.content)
    return ai_texts


# ============ Speech-to-Text (Whisper) Endpoint ============

# Supported voice languages: English, Hindi, Bengali
_SUPPORTED_VOICE_LANGS = {"en", "hi", "bn"}


def _translate_to_english(client, text: str, source_lang: str) -> str:
    """Translate Hindi/Bengali text to English using GPT for the agent pipeline."""
    lang_name = {"hi": "Hindi", "bn": "Bengali"}.get(source_lang, source_lang)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": f"You are a translator. Translate the following {lang_name} text to English. Return ONLY the English translation, nothing else."},
                {"role": "user", "content": text},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Translation to English failed: {e}")
        return text  # fallback to original


def _translate_from_english(client, text: str, target_lang: str) -> str:
    """Translate English text to Hindi/Bengali using GPT for TTS output."""
    lang_name = {"hi": "Hindi", "bn": "Bengali"}.get(target_lang, target_lang)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": f"You are a translator. Translate the following English text to {lang_name}. Return ONLY the {lang_name} translation, nothing else. Keep product names, brand names, and prices in English/numerals."},
                {"role": "user", "content": text},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Translation to {lang_name} failed: {e}")
        return text  # fallback to English


@app.post("/api/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """Transcribe audio to text using OpenAI Whisper model with Hindi/Bengali support."""
    try:
        # Read the uploaded audio bytes
        audio_bytes = await audio.read()
        if not audio_bytes:
            return JSONResponse(status_code=400, content={"error": "Empty audio file"})

        # Determine a safe suffix from the uploaded filename
        suffix = ".webm"
        if audio.filename:
            ext = os.path.splitext(audio.filename)[1]
            if ext:
                suffix = ext

        # Write to a temp file so the openai client can read it
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            client = openai.OpenAI()  # uses OPENAI_API_KEY env var

            # Step 1: Transcribe WITHOUT forcing language so Whisper auto-detects
            with open(tmp_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                )

            text = transcription.text.strip() if transcription.text else ""
            detected_lang = getattr(transcription, "language", "en") or "en"
            # Normalise language code (Whisper may return full name)
            lang_map = {"english": "en", "hindi": "hi",
                        "bengali": "bn", "bangla": "bn"}
            detected_lang = lang_map.get(
                detected_lang.lower(), detected_lang.lower()[:2])

            # If language is not in our supported set, treat as English
            if detected_lang not in _SUPPORTED_VOICE_LANGS:
                detected_lang = "en"

            # Step 2: If Hindi or Bengali, translate to English for the agent
            translated_text = text
            if detected_lang in ("hi", "bn") and text:
                translated_text = _translate_to_english(
                    client, text, detected_lang)

            return {
                "text": translated_text,           # English text for the agent
                "original_text": text,              # Original transcription
                "detected_language": detected_lang,  # "en", "hi", or "bn"
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except openai.APIError as e:
        logging.error(f"OpenAI Whisper API error: {e}")
        return JSONResponse(status_code=502, content={"error": "Speech-to-text service error"})
    except Exception as e:
        logging.error(f"Speech-to-text error: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to transcribe audio"})


# ============ Text-to-Speech (OpenAI TTS) Endpoint ============

class TTSRequest(BaseModel):
    text: str
    customer_id: str = ""
    language: str = "en"  # "en", "hi", or "bn"


@app.post("/api/text-to-speech")
async def text_to_speech(data: TTSRequest):
    """Convert text to speech using OpenAI TTS. Voice is chosen based on customer gender.
    If language is Hindi or Bengali, the English text is translated before TTS."""
    try:
        if not data.text or not data.text.strip():
            return JSONResponse(status_code=400, content={"error": "Empty text"})

        # Determine customer gender to pick opposite voice
        voice = "nova"  # default female voice
        if data.customer_id:
            try:
                with get_db_session() as session:
                    customer = customer_crud.get_by_id(
                        session, data.customer_id)
                    if customer and customer.gender:
                        g = customer.gender.strip().lower()
                        if g in ("male", "men", "m"):
                            # Male customer -> female voice
                            voice = "nova"
                        elif g in ("female", "women", "f"):
                            # Female customer -> male voice
                            voice = "echo"
            except Exception:
                pass  # fallback to default voice

        # Truncate long text to avoid excessive TTS cost (max ~500 chars)
        speak_text = data.text.strip()
        if len(speak_text) > 500:
            speak_text = speak_text[:497] + "..."

        # Translate English text to target language if Hindi or Bengali
        target_lang = (data.language or "en").strip().lower()
        if target_lang in ("hi", "bn") and speak_text:
            client_translate = openai.OpenAI()
            speak_text = _translate_from_english(
                client_translate, speak_text, target_lang)

        client = openai.OpenAI()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=speak_text,
        )

        # Return audio as MP3 bytes
        audio_bytes = response.content
        if not audio_bytes:
            return JSONResponse(status_code=500, content={"error": "No audio generated"})
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"},
        )

    except openai.APIError as e:
        logging.error(f"OpenAI TTS API error: {e}")
        return JSONResponse(status_code=502, content={"error": "Text-to-speech service error"})
    except Exception as e:
        logging.error(f"Text-to-speech error: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to generate speech"})


# ============ Virtual Try-On (Google Vertex AI) Endpoint ============

@app.post("/api/virtual-tryon")
async def virtual_tryon(
    person_image: UploadFile = File(...),
    product_image_url: Optional[str] = Form(None),
    product_image: Optional[UploadFile] = File(None),
):
    """
    Virtual Try-On using Google Vertex AI.
    Accepts a person image upload and a product image (either as URL or upload).
    Returns the generated try-on image as base64.
    """
    try:
        from google import genai
        from google.genai.types import RecontextImageSource, ProductImage, Image

        logging.info(
            f"[VTO] person_image={person_image.filename}, product_image_url={product_image_url}, product_image={getattr(product_image, 'filename', None)}")

        api_key = os.getenv("GOOGLE_VERTEX_API_KEY", "")
        project_id = os.getenv("GOOGLE_VERTEX_PROJECT_ID", "")
        location = os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

        # google-genai SDK: api_key and vertexai/project/location are MUTUALLY EXCLUSIVE.
        # virtual-try-on-001 is a Vertex AI model → needs vertexai=True + project + location.
        # We load the service account JSON to provide credentials.
        if project_id:
            # Resolve credentials path relative to this file if not absolute
            if credentials_path and not os.path.isabs(credentials_path):
                credentials_path = os.path.join(
                    os.path.dirname(os.path.abspath(
                        __file__)), credentials_path
                )

            # Load service account credentials from JSON key file
            if credentials_path and os.path.isfile(credentials_path):
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                logging.info(
                    f"[VTO] Using Vertex AI mode with service account: project={project_id}, location={location}, creds={credentials_path}")
                vertex_client = genai.Client(
                    vertexai=True,
                    project=project_id,
                    location=location,
                    credentials=credentials,
                )
            else:
                # Fallback: rely on Application Default Credentials (gcloud auth)
                logging.info(
                    f"[VTO] Using Vertex AI mode with ADC: project={project_id}, location={location}")
                vertex_client = genai.Client(
                    vertexai=True,
                    project=project_id,
                    location=location,
                )
        elif api_key:
            # API-key-only mode (Google AI / Gemini API)
            logging.info("[VTO] Using API key mode (no project_id set)")
            vertex_client = genai.Client(api_key=api_key)
        else:
            return JSONResponse(status_code=500, content={
                "error": "Virtual try-on not configured. Set GOOGLE_VERTEX_PROJECT_ID + GOOGLE_APPLICATION_CREDENTIALS in .env"
            })

        # Read person image bytes
        person_bytes = await person_image.read()
        if not person_bytes:
            return JSONResponse(status_code=400, content={"error": "Empty person image"})

        # --- Image optimization: resize large images for faster Vertex AI processing ---
        def _optimize_image_bytes(img_bytes, max_dim=1024, quality=85):
            """Resize and compress image bytes using Pillow for faster API calls."""
            try:
                from PIL import Image as PILImage
                import io
                img = PILImage.open(io.BytesIO(img_bytes))
                # Convert RGBA/palette to RGB
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                w, h = img.size
                if w > max_dim or h > max_dim:
                    scale = min(max_dim / w, max_dim / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    img = img.resize((new_w, new_h), PILImage.LANCZOS)
                    logging.info(
                        f"[VTO] Resized image from {w}x{h} to {new_w}x{new_h}")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                return buf.getvalue()
            except ImportError:
                logging.warning(
                    "[VTO] Pillow not installed, skipping image optimization")
                return img_bytes
            except Exception as e:
                logging.warning(
                    f"[VTO] Image optimization failed: {e}, using original")
                return img_bytes

        person_bytes = _optimize_image_bytes(person_bytes)

        # Save person image to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_person:
            tmp_person.write(person_bytes)
            tmp_person_path = tmp_person.name

        # Get product image - either from URL or file upload
        tmp_product_path = None
        try:
            if product_image and product_image.filename:
                # Product image uploaded directly
                product_bytes = await product_image.read()
                product_bytes = _optimize_image_bytes(product_bytes)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_product:
                    tmp_product.write(product_bytes)
                    tmp_product_path = tmp_product.name
            elif product_image_url:
                # Download product image from URL
                import httpx
                # Handle relative URLs by looking at local filesystem first
                if product_image_url.startswith("/images/"):
                    local_path = _IMAGES_DIR / \
                        product_image_url.replace("/images/", "")
                    if local_path.exists():
                        # Optimize local product image too
                        with open(local_path, "rb") as f:
                            local_bytes = _optimize_image_bytes(f.read())
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_product:
                            tmp_product.write(local_bytes)
                            tmp_product_path = tmp_product.name
                    else:
                        return JSONResponse(status_code=400, content={"error": "Product image not found locally"})
                else:
                    async with httpx.AsyncClient() as http_client:
                        resp = await http_client.get(product_image_url, timeout=15.0)
                        resp.raise_for_status()
                        optimized = _optimize_image_bytes(resp.content)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_product:
                            tmp_product.write(optimized)
                            tmp_product_path = tmp_product.name
            else:
                return JSONResponse(status_code=400, content={"error": "No product image provided"})

            # Call Vertex AI Virtual Try-On
            response = vertex_client.models.recontext_image(
                model="virtual-try-on-001",
                source=RecontextImageSource(
                    person_image=Image.from_file(location=tmp_person_path),
                    product_images=[
                        ProductImage(product_image=Image.from_file(
                            location=tmp_product_path))
                    ],
                ),
            )

            if response.generated_images and len(response.generated_images) > 0:
                # Save result to temp file and read as base64
                import base64
                result_suffix = ".png"
                with tempfile.NamedTemporaryFile(delete=False, suffix=result_suffix) as tmp_result:
                    response.generated_images[0].image.save(tmp_result.name)
                    tmp_result_path = tmp_result.name

                with open(tmp_result_path, "rb") as f:
                    result_bytes = f.read()

                # Cleanup result temp file
                try:
                    os.unlink(tmp_result_path)
                except OSError:
                    pass

                result_base64 = base64.b64encode(result_bytes).decode("utf-8")
                return {"success": True, "image": f"data:image/png;base64,{result_base64}"}
            else:
                return JSONResponse(status_code=422, content={
                    "error": "Virtual try-on could not generate a result. Please try with a clearer full-body photo."
                })

        finally:
            # Cleanup temp files
            try:
                os.unlink(tmp_person_path)
            except OSError:
                pass
            if tmp_product_path and not tmp_product_path.startswith(str(_IMAGES_DIR)):
                try:
                    os.unlink(tmp_product_path)
                except OSError:
                    pass

    except ImportError:
        logging.error(
            "google-genai package not installed. Run: pip install google-genai")
        return JSONResponse(status_code=500, content={"error": "Virtual try-on service not available. Missing google-genai package."})
    except Exception as e:
        logging.error(f"Virtual try-on error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Virtual try-on failed: {str(e)}"})


# code to  be pasted
@app.post("/api/chat/test")
async def test_chat_endpoint(data: dict):
    """Test endpoint to see what data is being received"""
    print("Test endpoint received:", data)
    return {"received": data}


# ----- New API models & endpoints for creating products and transactions -----
class ProductCreateModel(BaseModel):
    product_id: str
    product_name: str
    category: str
    gender: str
    price: float
    quantity: Optional[int] = 0
    online_available: str
    offline_available: str
    offline_stores: Optional[str] = None
    store_ids: Optional[str] = None
    festival: Optional[str] = None
    season: str
    image_reference: str
    loyalty_points: Optional[int] = 0


@app.post("/api/products")
def create_product_endpoint(product: ProductCreateModel):
    try:
        with get_db_session() as session:
            if product_crud.exists(session, product.product_id):
                return {"success": False, "error": "Product with this ID already exists"}

            p = Product(**product.dict())
            created = product_crud.create(session, p)
            return {"success": True, "product_id": created.product_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


class OrderCreateModel(BaseModel):
    transaction_id: str
    customer_id: str
    customer_name: str
    product_id: str
    product_name: str
    quantity: int
    order_dates: str
    loyalty_points: int


@app.post("/api/orders")
def create_order_endpoint(order: OrderCreateModel):
    try:
        with get_db_session() as session:
            if order_history_crud.exists(session, order.transaction_id):
                return {"success": False, "error": "Transaction already exists"}

            o = OrderHistory(**order.dict())
            created = order_history_crud.create(session, o)
            return {"success": True, "transaction_id": created.transaction_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


class InitiateReturnModel(BaseModel):
    transaction_id: str
    return_reason: str


@app.post("/api/orders/initiate-return")
def initiate_return_endpoint(data: InitiateReturnModel):
    """Initiate a return/refund for an order.

    Updates return_status, return_reason, and return_initiated_time
    in the order_history table for the given transaction_id.
    """
    if not data.return_reason or not data.return_reason.strip():
        raise HTTPException(
            status_code=400, detail="Return reason is required.")

    # Validate that the return reason is product-related (not generic)
    reason_lower = data.return_reason.strip().lower()
    valid_reason_keywords = [
        "size", "fit", "fitting", "too small", "too big", "too large", "too tight", "too loose",
        "defect", "defective", "damaged", "broken", "torn", "ripped", "scratched", "dent",
        "quality", "poor quality", "bad quality", "low quality", "fabric", "material", "stitching",
        "color", "colour", "shade", "faded", "discolored", "wrong color", "wrong colour",
        "wrong", "wrong product", "wrong item", "incorrect", "mismatch", "not matching",
        "mistake", "by mistake", "accidentally", "accidental", "ordered wrong", "didn't mean",
        "not as described", "not as shown", "different from", "doesn't match", "does not match",
        "expired", "stale", "spoiled", "smell", "odor", "stain", "dirty",
        "missing", "missing part", "incomplete", "not working", "malfunction", "faulty",
        "allergic", "allergy", "reaction", "irritation", "rash",
        "duplicate", "ordered twice", "double order",
        "not needed", "no longer need", "don't need", "changed mind", "change of mind",
        "better price", "found cheaper", "price drop",
        "late delivery", "delayed", "took too long",
        "packaging", "box damaged", "seal broken",
    ]
    reason_is_valid = any(
        keyword in reason_lower for keyword in valid_reason_keywords)

    if not reason_is_valid:
        return {
            "success": False,
            "error": "Please provide a valid product-related reason for return. Examples: size issue, defective product, wrong item received, quality issue, bought by mistake, etc.",
            "invalid_reason": True,
        }

    try:
        with get_db_session() as session:
            order = order_history_crud.get_by_id(session, data.transaction_id)
            if order is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Order with transaction_id {data.transaction_id} not found.",
                )

            if order.return_status and order.return_status.lower() in ("initiated", "completed"):
                return {
                    "success": False,
                    "error": "Return has already been initiated for this order.",
                }

            # Reject returns for items purchased less than 24 hours ago
            raw_date = (order.order_dates or "").strip()
            if raw_date:
                try:
                    parsed_date = datetime.fromisoformat(
                        raw_date.replace("Z", "+00:00"))
                    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
                    if parsed_date > cutoff_24h:
                        return {
                            "success": False,
                            "error": "Items purchased within the last 24 hours are not eligible for return. Please try again after 24 hours from purchase.",
                        }
                except Exception:
                    pass

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            order_history_crud.update(
                session,
                data.transaction_id,
                {
                    "return_status": "Initiated",
                    "return_reason": data.return_reason.strip(),
                    "return_initiated_time": now,
                },
            )
            session.commit()

            return {
                "success": True,
                "transaction_id": data.transaction_id,
                "return_status": "Initiated",
                "return_reason": data.return_reason.strip(),
                "return_initiated_time": now,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/orders/return-monitoring")
def return_monitoring_endpoint():
    """Silent return-monitoring agent (batch operation).

    Scans the entire order_history table for orders where return_status is
    'Initiated' and return_initiated_time is older than 10 minutes.
    Updates those orders' return_status to 'Returned' for all customers.
    """
    updated_count = 0
    try:
        with get_db_session() as session:
            orders = order_history_crud.get_all(session, skip=0, limit=100000)
            now = datetime.now()

            for order in orders:
                if not order.return_status or order.return_status.lower() != "initiated":
                    continue
                raw_time = (order.return_initiated_time or "").strip()
                if not raw_time:
                    continue
                try:
                    # Handle both "YYYY-MM-DD HH:MM:SS" and ISO formats
                    normalized = raw_time.replace("T", " ").replace("Z", "")
                    initiated_time = datetime.strptime(
                        normalized.split(".")[0], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue

                diff_minutes = (now - initiated_time).total_seconds() / 60.0
                if diff_minutes >= 10:
                    # 1. Get the quantity being returned
                    return_qty = order.quantity if order.quantity else 0

                    # 2. Add quantity back to the product's stock
                    if return_qty > 0 and order.product_id:
                        product = product_crud.get_by_id(
                            session, order.product_id)
                        if product:
                            current_stock = product.quantity if product.quantity else 0
                            product_crud.update(
                                session,
                                order.product_id,
                                {"quantity": current_stock + return_qty},
                            )

                    # 3. Update return_status to "Returned" and set order quantity to 0
                    order_history_crud.update(
                        session,
                        order.transaction_id,
                        {"return_status": "Returned", "quantity": 0},
                    )
                    updated_count += 1

            if updated_count > 0:
                session.commit()

        return {"success": True, "updated_count": updated_count}
    except Exception as e:
        return {"success": False, "error": str(e), "updated_count": 0}


@app.get("/api/stores/locate/{customer_id}")
def get_store_locations(customer_id: str):
    """Locate Us agent: fetch nearby stores with distance and map URL for a customer."""
    try:
        with get_db_session() as session:
            from sqlmodel import select as sql_select
            statement = sql_select(Distance).where(
                Distance.customer_id == customer_id)
            results = session.exec(statement).all()

            if not results:
                return {"success": True, "stores": [], "message": "No store distance data found for this customer."}

            stores = []
            for row in results:
                stores.append({
                    "store_name": row.store_name,
                    "distance": round(row.distance, 2),
                    "map_url": row.map_url or "",
                })

            # Sort by distance ascending
            stores.sort(key=lambda s: s["distance"])

            return {"success": True, "stores": stores, "count": len(stores)}
    except Exception as e:
        return {"success": False, "stores": [], "error": str(e)}


class StoreTransactionCreateModel(BaseModel):
    id: int
    customer_id: str
    product_id: str
    date: str
    user_name: str
    product: str
    qty: int
    mode: str
    store_name: str
    store_id: Optional[str] = None
    status: str
    amount: float
    address: str
    phone: str


@app.post("/api/store-transactions")
def create_store_transaction_endpoint(tx: StoreTransactionCreateModel):
    try:
        with get_db_session() as session:
            if store_keeper_transaction_crud.exists(session, tx.id):
                return {"success": False, "error": "Transaction with this id already exists"}

            t = StoreKeeperTransaction(**tx.dict())
            created = store_keeper_transaction_crud.create(session, t)
            return {"success": True, "id": created.id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cart/pending/{customer_id}")
def get_pending_cart_items(customer_id: str):
    """Return a lightweight summary of pending cart items for a customer."""
    try:
        with get_db_session() as session:
            cart_items = cart_crud.filter(
                session,
                filters={"customer_id": customer_id, "status": "pending"},
                operators={"customer_id": "==", "status": "=="},
                limit=50,
            )
            if not cart_items:
                return {"cart_items": [], "total_items": 0, "total_amount": 0, "total_savings": 0, "available_loyalty_points": 0}

            details = []
            total_amount = 0
            total_savings = 0
            for item in cart_items:
                product = product_crud.get_by_id(session, item.product_id)
                if product:
                    qty = getattr(item, "quantity", 1)
                    size = getattr(item, "size", None)
                    discount = getattr(product, "discount", 0) or 0
                    price = round(product.price * (1 - discount / 100),
                                  2) if discount > 0 else product.price
                    item_total = price * qty
                    item_original_total = product.price * qty
                    item_savings = item_original_total - item_total
                    total_amount += item_total
                    total_savings += item_savings
                    details.append({
                        "order_id": item.order_id,
                        "product_id": item.product_id,
                        "product_name": product.product_name,
                        "quantity": qty,
                        "size": size,
                        "price": price,
                        "original_price": product.price,
                        "discount": discount,
                        "total": item_total,
                        "image_reference": product.image_reference,
                        "savings": item_savings,
                    })

            # Fetch customer loyalty points
            available_loyalty_points = 0
            try:
                customer = customer_crud.get_by_id(session, customer_id)
                if customer:
                    available_loyalty_points = customer.loyalty_points or 0
            except Exception:
                pass

            return {
                "cart_items": details,
                "total_items": len(details),
                "total_amount": total_amount,
                "total_savings": total_savings,
                "available_loyalty_points": available_loyalty_points,
            }
    except Exception as e:
        return {"cart_items": [], "total_items": 0, "total_amount": 0, "total_savings": 0, "available_loyalty_points": 0, "error": str(e)}


@app.get("/api/cart/upsell/{customer_id}")
def get_cart_upsell(customer_id: str):
    """Run the autonomous upsell chain: upsell_agent → inventory_agent → recommendation_agent.
    Loops through multiple candidate categories until 4 unique products are collected.
    Returns upsell product recommendations based on the customer's pending cart."""
    try:
        # 1. Upsell agent – determines candidate categories to recommend
        upsell_raw = upsell_agent.invoke({"customer_id": customer_id})
        upsell_data = json.loads(upsell_raw) if isinstance(
            upsell_raw, str) else upsell_raw
        categories = upsell_data.get("categories", [])
        if not categories:
            categories = [upsell_data.get("category", "Accessories")]
        upsell_category = categories[0]

        # 2. Loop through categories, collecting unique products until we have 4
        collected_products = []
        seen_product_ids = set()
        TARGET_COUNT = 4

        for cat in categories:
            if len(collected_products) >= TARGET_COUNT:
                break
            try:
                inv_raw = inventory_agent.invoke(
                    {"search_query": f"show me {cat}", "customer_id": customer_id})
                inv_data = json.loads(inv_raw) if isinstance(
                    inv_raw, str) else inv_raw
                for p in inv_data.get("products", []):
                    pid = p.get("product_id")
                    if pid and pid not in seen_product_ids:
                        seen_product_ids.add(pid)
                        collected_products.append(p)
                        if len(collected_products) >= TARGET_COUNT:
                            break
            except Exception:
                continue

        if not collected_products:
            return {"upsell": None}

        # 3. Build merged inventory result and pass to recommendation agent
        merged_inv = json.dumps({
            "status": "success",
            "message": f"Found {len(collected_products)} upsell products",
            "products": collected_products
        })
        rec_raw = recommendation_agent.invoke({"inventory_data": merged_inv})
        rec_parsed = json.loads(rec_raw) if isinstance(
            rec_raw, str) else rec_raw

        recs = (rec_parsed.get("responses") or {}).get("recommendation", [])
        if recs:
            rec_parsed["upsell_category"] = upsell_category
            return {"upsell": rec_parsed}

        return {"upsell": None}
    except Exception as e:
        print(f"[UPSELL REST] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"upsell": None}


class CartAddModel(BaseModel):
    product_id: str
    quantity: int
    customer_id: str
    size: Optional[str] = None


@app.post("/api/cart/add")
def add_to_cart_direct(item: CartAddModel):
    """Directly add a product to the cart table, bypassing the LLM pipeline.
    Used by the bulk 'Add All to Cart' flow for deterministic, reliable inserts."""
    if item.quantity <= 0:
        return {"success": False, "error": "Quantity must be greater than 0"}

    product = get_product_from_db(item.product_id)
    if not product:
        return {"success": False, "error": f"Product {item.product_id} not found"}

    if product.quantity < item.quantity:
        return {
            "success": False,
            "error": f"Only {product.quantity} units of {product.product_name} are available in stock.",
        }

    try:
        with get_db_session() as session:
            order_id = f"CART{int(time.time() * 1000) % 1000000}{random.randint(100, 999)}"

            cart_data = {
                "order_id": order_id,
                "customer_id": item.customer_id,
                "product_id": item.product_id,
                "store_id": None,
                "channel": "pending",
                "status": "pending",
                "quantity": item.quantity,
                "size": item.size,
                "created_at": datetime.utcnow().isoformat(),
            }

            cart_crud.create(session, cart_data)

            discount = getattr(product, "discount", 0) or 0
            discount_price = (
                round(product.price * (1 - discount / 100), 2)
                if discount > 0
                else product.price
            )

            return {
                "success": True,
                "order_id": order_id,
                "product_name": product.product_name,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": product.price,
                "discount_price": discount_price,
                "discount": discount,
            }
    except Exception as e:
        print(f"Error adding to cart directly: {e}")
        return {"success": False, "error": "Failed to add product to cart. Please try again."}


class UpdateCartQuantityModel(BaseModel):
    order_id: str
    quantity: int


class UpdateCartSizeModel(BaseModel):
    order_id: str
    size: Optional[str] = None


@app.put("/api/cart/update-quantity")
def update_cart_quantity(update_data: UpdateCartQuantityModel):
    """Update the quantity of an item in the cart"""
    try:
        with get_db_session() as session:
            # Get the cart item
            cart_item = cart_crud.get_by_id(session, update_data.order_id)
            if not cart_item:
                return {"success": False, "error": "Cart item not found"}

            # Ensure quantity is at least 1
            if update_data.quantity < 1:
                return {"success": False, "error": "Quantity must be at least 1"}

            # Get the product to calculate total
            product = product_crud.get_by_id(session, cart_item.product_id)
            if not product:
                return {"success": False, "error": "Product not found"}

            # Update the quantity
            updated_item = cart_crud.update(
                session,
                update_data.order_id,
                {"quantity": update_data.quantity}
            )

            if updated_item:
                total_amount = product.price * update_data.quantity
                return {
                    "success": True,
                    "message": f"Updated quantity to {update_data.quantity}",
                    "cart_item": {
                        "order_id": updated_item.order_id,
                        "product_name": product.product_name,
                        "quantity": updated_item.quantity,
                        "price": product.price,
                        "total_amount": total_amount
                    }
                }
            else:
                return {"success": False, "error": "Failed to update quantity"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.put("/api/cart/update-size")
def update_cart_size(update_data: UpdateCartSizeModel):
    """Update the size of an item in the cart"""
    try:
        with get_db_session() as session:
            cart_item = cart_crud.get_by_id(session, update_data.order_id)
            if not cart_item:
                return {"success": False, "error": "Cart item not found"}

            size_value = update_data.size
            if isinstance(size_value, str):
                size_value = size_value.strip() or None

            updated_item = cart_crud.update(
                session,
                update_data.order_id,
                {"size": size_value},
            )
            if updated_item:
                return {
                    "success": True,
                    "message": "Updated size",
                    "cart_item": {
                        "order_id": updated_item.order_id,
                        "size": getattr(updated_item, "size", None),
                    },
                }
            return {"success": False, "error": "Failed to update size"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class ApplyLoyaltyModel(BaseModel):
    customer_id: str
    apply: bool  # True = apply loyalty points, False = remove/unapply
    cart_total: float  # current cart total before loyalty


@app.post("/api/cart/apply-loyalty")
def apply_loyalty_to_cart(data: ApplyLoyaltyModel):
    """Apply or remove loyalty points discount on the cart total and update customer loyalty_points."""
    try:
        with get_db_session() as session:
            customer = customer_crud.get_by_id(session, data.customer_id)
            if not customer:
                return {"success": False, "error": "Customer not found"}

            available_points = customer.loyalty_points or 0

            if data.apply:
                # Points to use: min of available points and cart total (1 point = ₹1)
                points_to_use = min(available_points, int(data.cart_total))
                new_total = max(data.cart_total - points_to_use, 0)
                remaining_points = available_points - points_to_use

                # Update customer loyalty_points in DB
                customer_crud.update(session, data.customer_id, {
                                     "loyalty_points": remaining_points})

                return {
                    "success": True,
                    "applied": True,
                    "points_used": points_to_use,
                    "remaining_points": remaining_points,
                    "new_total": new_total,
                    "original_total": data.cart_total,
                }
            else:
                # Unapply: we need the frontend to tell us how many points were previously used
                # Just return current state without deducting
                return {
                    "success": True,
                    "applied": False,
                    "points_used": 0,
                    "remaining_points": available_points,
                    "new_total": data.cart_total,
                    "original_total": data.cart_total,
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/cart/unapply-loyalty")
def unapply_loyalty_from_cart(data: ApplyLoyaltyModel):
    """Restore loyalty points back to customer when unchecking loyalty checkbox."""
    try:
        with get_db_session() as session:
            customer = customer_crud.get_by_id(session, data.customer_id)
            if not customer:
                return {"success": False, "error": "Customer not found"}

            # cart_total here is the points_used that need to be restored
            points_to_restore = int(data.cart_total)
            current_points = customer.loyalty_points or 0
            new_points = current_points + points_to_restore

            customer_crud.update(session, data.customer_id, {
                                 "loyalty_points": new_points})

            return {
                "success": True,
                "restored_points": points_to_restore,
                "remaining_points": new_points,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/chat")
async def chat_with_agent(chat_message: ChatMessage):
    """
    Chat endpoint for the intelligent agent system
    Processes user queries and returns AI responses with conversation history
    """
    try:
        print(f"\n{'='*60}")
        print(f"Raw request data received:")
        print(f"Customer ID: {chat_message.customer_id}")
        print(f"Message: {chat_message.message}")
        print(f"{'='*60}\n")

        customer_id = chat_message.customer_id
        user_query = chat_message.message
        session_id = customer_id  # Use customer_id as session_id

        def _looks_like_price_band_query(text: str) -> bool:
            if not text or not isinstance(text, str):
                return False
            t = text.lower()
            # Avoid intercepting cart/checkout intents; let the LLM workflow handle those.
            if re.search(r"\b(add|buy|purchase|checkout|proceed|payment|remove|cart|quantity|qty|online|offline)\b", t):
                return False
            # Must mention a price band keyword AND a number, or a numeric range like 1500-2000.
            if re.search(r"\b(between|above|over|more\s+than|greater\s+than|below|under|less\s+than|>=|<=)\b", t) and re.search(r"\d", t):
                return True
            if re.search(r"\b\d[\d,]*\s*-\s*\d[\d,]*\b", t):
                return True
            return False

        # Save user message to database
        save_message(customer_id, session_id, "user", user_query)

        # Get conversation history from database (limit to recent messages to force fresh tool calls)
        history = get_conversation_history(customer_id, session_id, limit=1)

        print(f"Retrieved {len(history)} messages from history")

        # ---- Price-band browse fast-path ----
        # When a user asks for products with an explicit price constraint (above/between/below),
        # do not rely on the LLM to preserve the numeric band in tool args.
        # Instead, pass the RAW user query to inventory_agent so it can filter on products.price.
        if _looks_like_price_band_query(user_query):
            from intelligent_agent_graph import inventory_agent as _inventory_tool, recommendation_agent as _recommendation_tool

            inv_raw = _inventory_tool.invoke({
                "search_query": user_query,
                "customer_id": customer_id,
            })

            rec_raw = _recommendation_tool.invoke({
                "inventory_data": inv_raw,
            })

            # Save the assistant's default message for history continuity.
            try:
                rec_obj = json.loads(rec_raw) if isinstance(
                    rec_raw, str) else rec_raw
            except Exception:
                rec_obj = None

            if isinstance(rec_obj, dict):
                default_text = (rec_obj.get("responses") or {}).get("default")
                if isinstance(default_text, str) and default_text.strip():
                    save_message(customer_id, session_id, "assistant", default_text, [
                                 "inventory_agent", "recommendation_agent"])
                return rec_obj

            # Fallback: return a legacy payload
            save_message(customer_id, session_id, "assistant", str(
                rec_raw), ["inventory_agent", "recommendation_agent"])
            return {
                "response": str(rec_raw),
                "agent_calls": ["inventory_agent", "recommendation_agent"],
            }

        # Create agent graph
        graph = create_agent_graph()

        # Build messages list with history
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Create initial state with conversation history
        initial_state = {
            "messages": messages,
            "customer_id": customer_id,
            "selected_product": None,
            "inventory_status": None,
            "purchase_channel": None,
            "order_id": None,
            "payment_completed": False,
            "loyalty_points": 0
        }

        print(f"Running agent with {len(messages)} messages in context...")

        # Run the graph with conversation history
        result = await graph.ainvoke(initial_state)

        # Extract timeline messages from all agent tool calls
        from langchain_core.messages import ToolMessage
        timeline_messages = _format_timeline_messages_from_langchain_messages(
            result.get("messages", []))

        # Try to return tool output as JSON if present (with timeline)
        for message in reversed(result["messages"]):
            if isinstance(message, ToolMessage):
                try:
                    response_data = json.loads(message.content)
                    # Add timeline to response if it's a dict
                    if isinstance(response_data, dict):
                        # Add timeline for agents that support it (check for id or cart_items)
                        if response_data.get("id") in ["recommendation_agent", "view_cart_agent"] or "cart_items" in response_data:
                            response_data["timeline"] = timeline_messages
                        # Always return the parsed JSON if successful
                        return response_data
                except Exception:
                    pass

        # Fallback: Extract the AI response from messages
        ai_response = ""
        agent_calls = []

        # Get the latest AI response (last AIMessage without tool calls)
        for message in reversed(result["messages"]):
            if message.__class__.__name__ == 'AIMessage':
                if hasattr(message, 'content') and message.content:
                    if not (hasattr(message, 'tool_calls') and message.tool_calls):
                        ai_response = message.content
                        break

        # Track all tool calls
        for message in result["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call["name"] not in agent_calls:
                        agent_calls.append(tool_call["name"])

        print(f"\n{'='*60}")
        print(f"Chat Response:")
        print(f"Timeline Messages: {len(timeline_messages)}")
        print(f"AI Response: {ai_response[:100] if ai_response else 'N/A'}...")
        print(f"Agent Calls: {agent_calls}")
        print(f"{'='*60}\n")

        # Save assistant response to database
        if ai_response:
            save_message(customer_id, session_id, "assistant",
                         ai_response, agent_calls)

        # Return as legacy chat response if not a tool JSON
        return {
            "response": ai_response if ai_response else "I apologize, but I couldn't generate a response. Please try again.",
            "agent_calls": agent_calls,
            "timeline": timeline_messages
        }

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR in chat endpoint:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")

        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "agent_calls": []
        }


async def _ws_stream_text(websocket: WebSocket, request_id: str, text: str, chunk_size: int = 24):
    """Send assistant text in small deltas for a streaming effect."""
    if not text:
        return
    await websocket.send_json({"type": "assistant_stream_start", "request_id": request_id})
    for i in range(0, len(text), chunk_size):
        await websocket.send_json({
            "type": "assistant_stream_delta",
            "request_id": request_id,
            "delta": text[i:i + chunk_size],
        })
        await asyncio.sleep(0)
    await websocket.send_json({"type": "assistant_stream_end", "request_id": request_id})


def _ws_ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _single_line(text: str) -> str:
    if text is None:
        return ""
    s = str(text)
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


def _ws_line(text: str, max_len: int = 160) -> str:
    s = _single_line(text)
    if not s:
        return ""
    if len(s) > max_len:
        s = s[:max_len] + "…"
    return f"{_ws_ts()} {s}"


def _try_parse_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return json.loads(s)
            except Exception:
                return value
        return value
    return value


def _summarize_tool_start(tool_name: str, tool_args: Any) -> str:
    args = tool_args if isinstance(tool_args, dict) else {}

    if tool_name == "inventory_agent":
        q = args.get("search_query") or args.get("query") or args.get("text")
        parts: List[str] = []
        if q:
            parts.append(f"find {q!r}")
        min_p = args.get("min_price") or args.get("price_min")
        max_p = args.get("max_price") or args.get("price_max")
        if min_p is not None or max_p is not None:
            if min_p is not None and max_p is not None:
                parts.append(f"price={min_p}-{max_p}")
            elif max_p is not None:
                parts.append(f"price<={max_p}")
            else:
                parts.append(f"price>={min_p}")
        color = args.get("color")
        if color:
            parts.append(f"color:{color}")
        size = args.get("size")
        if size:
            parts.append(f"size:{size}")
        if args.get("sort_by_rating"):
            parts.append("sorted by ⭐ rating")
        return " ".join(parts) if parts else "Searching product catalog"

    if tool_name == "recommendation_agent":
        return "Preparing recommendations"

    if tool_name == "customer_info_agent":
        cid = args.get("customer_id")
        return f"Fetching customer profile ({cid})" if cid else "Fetching customer profile"

    if tool_name == "add_to_cart_agent":
        pid = args.get("product_id") or args.get("id")
        qty = args.get("quantity") or args.get("qty")
        if pid and qty:
            return f"Add {qty} × {pid} to cart"
        if pid:
            return f"Add {pid} to cart"
        return "Adding item to cart"

    if tool_name == "remove_from_cart_agent":
        oid = args.get("order_id") or args.get("orderId") or args.get("id")
        return f"Remove item {oid} from cart" if oid else "Removing item from cart"

    if tool_name == "view_cart_agent":
        return "Loading cart items"

    if tool_name == "upsell_agent":
        return "Finding attractive accessories for you"

    if tool_name == "choose_channel_agent":
        channel = args.get("channel")
        return f"Choosing purchase channel: {channel}" if channel else "Choosing purchase channel"

    if tool_name == "payment_agent":
        return "Processing payment"

    if tool_name == "fulfillment_agent":
        return "Preparing fulfillment"

    if tool_name == "loyalty_agent":
        return "Applying loyalty benefits"

    if tool_name == "post_purchase_agent":
        return "Preparing post-purchase support"

    if tool_name == "locate_us_agent":
        return "Locating nearby stores on map"

    return "Working…"


def _summarize_tool_result(tool_name: str, tool_result: Any) -> str:
    parsed = _try_parse_json(tool_result)

    if isinstance(parsed, dict):
        msg = parsed.get("message")
        if isinstance(msg, str) and msg.strip():
            return msg.strip()

        # Common payloads
        products = parsed.get("products")
        if isinstance(products, list):
            preview_items: List[str] = []
            for p in products[:6]:
                if isinstance(p, dict):
                    pid = p.get("product_id") or p.get("id")
                    name = p.get("product_name") or p.get("name")
                    if pid and name:
                        preview_items.append(f"{pid}:{name}")
                    elif pid:
                        preview_items.append(str(pid))
                else:
                    preview_items.append(str(p))
            tail = f" [{', '.join(preview_items)}]" if preview_items else ""
            return f"{len(products)} SKUs found{tail}"

        cart_items = parsed.get("cart_items")
        if isinstance(cart_items, list):
            return f"Cart has {len(cart_items)} item(s)"

        stores = parsed.get("stores")
        if isinstance(stores, list):
            return f"Found {len(stores)} store option(s)"

        status = parsed.get("status")
        if isinstance(status, str) and status.lower() in {"success", "ok"}:
            return "Done"
        if isinstance(status, str) and status.lower() in {"error", "failed"}:
            err = parsed.get("error") or parsed.get("detail") or "Error"
            return str(err)

        resp = parsed.get("response")
        if isinstance(resp, str) and resp.strip():
            return resp.strip()

        return _single_line(json.dumps(parsed, ensure_ascii=False))

    if isinstance(parsed, list):
        return f"Returned {len(parsed)} item(s)"

    s = _single_line(parsed)
    return s


def _extract_selected_store_name(user_query: Any) -> str:
    """Extract a concrete store name from a user's pickup-confirmation message.

    This is intentionally conservative to avoid hijacking the earlier
    "nearest offline store" selection step.
    """
    if not isinstance(user_query, str):
        return ""

    text = user_query.strip()
    if not text:
        return ""

    lower = text.lower()
    # Do NOT treat the generic nearest-store request as a concrete store choice.
    if "nearest offline store" in lower or "nearest store" in lower:
        return ""

    patterns = [
        # Frontend store card selection currently sends this
        r"\bpick\s*up\s+(?:my\s+)?order\s+from\s+(.+)$",
        r"\bi\s+want\s+to\s+pick\s*up\s+(?:my\s+)?order\s+from\s+(.+)$",
        # Defensive: if the UI ever sends the visible message instead
        r"\bi\s+selected\s+(.+)$",
    ]

    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if not m:
            continue
        store = (m.group(1) or "").strip()
        store = store.strip(" \t\r\n\"'`.,;:!?)[]{}")
        store_lower = store.lower()
        # Filter out generic non-store selections.
        if not store or store_lower in {"a store", "any store", "store"}:
            return ""
        if "nearest" in store_lower:
            return ""
        return store

    return ""


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """WebSocket endpoint for live agent timeline updates + streamed assistant output."""
    await websocket.accept()

    try:
        while True:
            payload = await websocket.receive_json()
            request_id = payload.get("request_id") or ""
            customer_id = payload.get("customer_id")
            user_query = payload.get("message")
            payload_size = payload.get("size")

            # Store loyalty points used if sent by frontend during payment
            loyalty_points_used = payload.get("loyalty_points_used")
            if loyalty_points_used is not None and customer_id:
                from intelligent_agent_graph import set_loyalty_points_used
                set_loyalty_points_used(customer_id, int(loyalty_points_used))

            if not customer_id or not user_query:
                await websocket.send_json({
                    "type": "error",
                    "request_id": request_id,
                    "message": "Missing customer_id or message",
                })
                continue

            session_id = customer_id

            def _looks_like_price_band_query(text: str) -> bool:
                if not text or not isinstance(text, str):
                    return False
                t = text.lower()
                # Avoid intercepting cart/checkout intents; let the LLM workflow handle those.
                if re.search(r"\b(add|buy|purchase|checkout|proceed|payment|remove|cart|quantity|qty|online|offline)\b", t):
                    return False
                if re.search(r"\b(between|above|over|more\s+than|greater\s+than|below|under|less\s+than|>=|<=)\b", t) and re.search(r"\d", t):
                    return True
                if re.search(r"\b\d[\d,]*\s*-\s*\d[\d,]*\b", t):
                    return True
                return False

            await websocket.send_json({
                "type": "run_start",
                "request_id": request_id,
                "customer_id": customer_id,
            })

            # Save user message early (keeps parity with /api/chat)
            save_message(customer_id, session_id, "user", user_query)

            history = get_conversation_history(
                customer_id, session_id, limit=1)
            messages: List[Any] = []
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(
                        content=msg.get("content", "")))
                else:
                    messages.append(AIMessage(content=msg.get("content", "")))

            state: Dict[str, Any] = {
                "messages": messages,
                "customer_id": customer_id,
                "selected_product": None,
                "inventory_status": None,
                "purchase_channel": None,
                "order_id": None,
                "payment_completed": False,
                "loyalty_points": 0,
                "cart_items": [],
            }

            tool_to_agent = _tool_to_agent_map()
            agent_calls: List[str] = []
            timeline_started: set[str] = set()

            # ---- Store selection fast-path (OFFLINE pickup) ----
            # When the user confirms a specific store, immediately run fulfillment.
            # This avoids the LLM looping back into inventory/view-cart.
            selected_store = _extract_selected_store_name(user_query)
            if selected_store:
                tool_name = "fulfillment_agent"
                agent_label = tool_to_agent.get(tool_name, "Fulfillment Agent")
                tool_args = {
                    "purchase_type": "offline",
                    "store_name": selected_store,
                    "customer_id": customer_id,
                }
                agent_calls.append(tool_name)

                await websocket.send_json({
                    "type": "timeline_start",
                    "request_id": request_id,
                    "agent": agent_label,
                    "tool": tool_name,
                    "timestamp": "now",
                    "status": "in_progress",
                })

                await websocket.send_json({
                    "type": "timeline_log",
                    "request_id": request_id,
                    "tool": tool_name,
                    "agent": agent_label,
                    "timestamp": "now",
                    "text": _ws_line(f"Master Orchestrator → {agent_label}"),
                })

                start_summary = _summarize_tool_start(tool_name, tool_args)
                if start_summary:
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": tool_name,
                        "agent": agent_label,
                        "timestamp": "now",
                        "text": _ws_line(start_summary),
                    })

                tool_ok = True
                try:
                    from intelligent_agent_graph import fulfillment_agent as _fulfillment_tool
                    tool_result = await asyncio.to_thread(_fulfillment_tool.invoke, tool_args)
                except Exception as e:
                    tool_ok = False
                    tool_result = {"status": "error",
                                   "message": f"Tool execution error: {str(e)}"}

                parsed_result = _try_parse_json(tool_result)
                response_data: Dict[str, Any] = parsed_result if isinstance(
                    parsed_result, dict) else {}
                if not response_data:
                    response_data = {
                        "response": str(parsed_result) if parsed_result is not None else "",
                        "agent_calls": agent_calls,
                    }
                else:
                    response_data.setdefault("agent_calls", agent_calls)
                    if "response" not in response_data and isinstance(response_data.get("message"), str):
                        response_data["response"] = response_data.get(
                            "message")

                result_summary = _summarize_tool_result(tool_name, tool_result)
                if result_summary:
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": tool_name,
                        "agent": agent_label,
                        "timestamp": "now",
                        "text": _ws_line(result_summary),
                    })

                await websocket.send_json({
                    "type": "timeline_log",
                    "request_id": request_id,
                    "tool": tool_name,
                    "agent": agent_label,
                    "timestamp": "now",
                    "text": _ws_line(f"{agent_label} → Master Orchestrator"),
                })

                await websocket.send_json({
                    "type": "timeline_end",
                    "request_id": request_id,
                    "agent": agent_label,
                    "tool": tool_name,
                    "timestamp": "now",
                    "status": "completed" if tool_ok else "error",
                })

                if isinstance(response_data.get("response"), str):
                    await _ws_stream_text(websocket, request_id, response_data.get("response", ""))

                # Save assistant response best-effort
                try:
                    assistant_text = response_data.get("response")
                    if isinstance(assistant_text, str) and assistant_text.strip():
                        save_message(customer_id, session_id,
                                     "assistant", assistant_text, agent_calls)
                except Exception:
                    pass

                await websocket.send_json({
                    "type": "final_response",
                    "request_id": request_id,
                    "data": response_data,
                })
                await websocket.send_json({"type": "run_end", "request_id": request_id})
                continue

            # ---- Price-band browse fast-path ----
            if _looks_like_price_band_query(user_query):
                from intelligent_agent_graph import inventory_agent as _inventory_tool, recommendation_agent as _recommendation_tool

                inv_tool_name = "inventory_agent"
                rec_tool_name = "recommendation_agent"
                inv_label = tool_to_agent.get(inv_tool_name, "Inventory Agent")
                rec_label = tool_to_agent.get(
                    rec_tool_name, "Recommendation Agent")

                agent_calls.extend([inv_tool_name, rec_tool_name])

                # Inventory timeline
                await websocket.send_json({
                    "type": "timeline_start",
                    "request_id": request_id,
                    "agent": inv_label,
                    "tool": inv_tool_name,
                    "timestamp": "now",
                    "status": "in_progress",
                })
                await websocket.send_json({
                    "type": "timeline_log",
                    "request_id": request_id,
                    "tool": inv_tool_name,
                    "agent": inv_label,
                    "timestamp": "now",
                    "text": _ws_line(f"Master Orchestrator → {inv_label}"),
                })
                inv_start = _summarize_tool_start(
                    inv_tool_name, {"search_query": user_query, "customer_id": customer_id})
                if inv_start:
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": inv_tool_name,
                        "agent": inv_label,
                        "timestamp": "now",
                        "text": _ws_line(inv_start),
                    })

                inv_ok = True
                try:
                    inv_raw = await asyncio.to_thread(_inventory_tool.invoke, {"search_query": user_query, "customer_id": customer_id})
                except Exception as e:
                    inv_ok = False
                    inv_raw = json.dumps(
                        {"status": "error", "message": f"Inventory tool error: {str(e)}", "products": []})

                inv_summary = _summarize_tool_result(inv_tool_name, inv_raw)
                if inv_summary:
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": inv_tool_name,
                        "agent": inv_label,
                        "timestamp": "now",
                        "text": _ws_line(inv_summary),
                    })

                await websocket.send_json({
                    "type": "timeline_log",
                    "request_id": request_id,
                    "tool": inv_tool_name,
                    "agent": inv_label,
                    "timestamp": "now",
                    "text": _ws_line(f"{inv_label} → Master Orchestrator"),
                })
                await websocket.send_json({
                    "type": "timeline_end",
                    "request_id": request_id,
                    "agent": inv_label,
                    "tool": inv_tool_name,
                    "timestamp": "now",
                    "status": "completed" if inv_ok else "error",
                })

                # Recommendation timeline
                await websocket.send_json({
                    "type": "timeline_start",
                    "request_id": request_id,
                    "agent": rec_label,
                    "tool": rec_tool_name,
                    "timestamp": "now",
                    "status": "in_progress",
                })
                await websocket.send_json({
                    "type": "timeline_log",
                    "request_id": request_id,
                    "tool": rec_tool_name,
                    "agent": rec_label,
                    "timestamp": "now",
                    "text": _ws_line(f"Master Orchestrator → {rec_label}"),
                })

                rec_ok = True
                try:
                    rec_raw = await asyncio.to_thread(_recommendation_tool.invoke, {"inventory_data": inv_raw})
                except Exception as e:
                    rec_ok = False
                    rec_raw = json.dumps({
                        "name": "Recommendation Agent",
                        "id": "recommendation_agent",
                        "responses": {"default": f"❌ Error preparing recommendations: {str(e)}", "recommendation": []},
                    })

                rec_summary = _summarize_tool_result(rec_tool_name, rec_raw)
                if rec_summary:
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": rec_tool_name,
                        "agent": rec_label,
                        "timestamp": "now",
                        "text": _ws_line(rec_summary),
                    })

                await websocket.send_json({
                    "type": "timeline_log",
                    "request_id": request_id,
                    "tool": rec_tool_name,
                    "agent": rec_label,
                    "timestamp": "now",
                    "text": _ws_line(f"{rec_label} → Master Orchestrator"),
                })
                await websocket.send_json({
                    "type": "timeline_end",
                    "request_id": request_id,
                    "agent": rec_label,
                    "tool": rec_tool_name,
                    "timestamp": "now",
                    "status": "completed" if rec_ok else "error",
                })

                parsed_rec = _try_parse_json(rec_raw)
                response_data: Dict[str, Any] = parsed_rec if isinstance(parsed_rec, dict) else {
                    "response": str(parsed_rec) if parsed_rec is not None else "",
                }
                response_data.setdefault("agent_calls", agent_calls)

                default_text = (response_data.get(
                    "responses") or {}).get("default")
                if isinstance(default_text, str) and default_text.strip():
                    try:
                        save_message(customer_id, session_id,
                                     "assistant", default_text, agent_calls)
                    except Exception:
                        pass

                await websocket.send_json({
                    "type": "final_response",
                    "request_id": request_id,
                    "data": response_data,
                })
                await websocket.send_json({"type": "run_end", "request_id": request_id})
                continue

            # Step-by-step run (agent decides tool calls, we execute tools, loop)
            from intelligent_agent_graph import agent_node as _agent_node, _execute_tool as _execute_tool
            from langchain_core.messages import ToolMessage

            final_ai_text = ""

            while True:
                agent_out = await asyncio.to_thread(_agent_node, state)
                ai_msg = agent_out.get("messages", [None])[0]
                if ai_msg is None:
                    break

                state["messages"].append(ai_msg)

                tool_calls = getattr(ai_msg, "tool_calls", None)
                if not tool_calls:
                    # Conversation ended (no more tool calls)
                    final_ai_text = getattr(ai_msg, "content", "") or ""
                    break

                # Emit timeline + logs as tools are called
                for tool_call in tool_calls:
                    tool_name = (tool_call or {}).get("name", "")
                    tool_args = (tool_call or {}).get("args", {})

                    # If the frontend provided size in the websocket payload for an add-to-cart action,
                    # pass it through as a tool arg so it can be persisted in the cart table.
                    if tool_name == "add_to_cart_agent" and payload_size:
                        if not isinstance(tool_args, dict):
                            tool_args = {}
                        tool_args.setdefault("size", payload_size)
                        try:
                            tool_call["args"] = tool_args
                        except Exception:
                            pass
                    agent_label = tool_to_agent.get(tool_name, tool_name)

                    if tool_name and tool_name not in agent_calls:
                        agent_calls.append(tool_name)

                    if tool_name and tool_name not in timeline_started:
                        timeline_started.add(tool_name)
                        await websocket.send_json({
                            "type": "timeline_start",
                            "request_id": request_id,
                            "agent": agent_label,
                            "tool": tool_name,
                            "timestamp": "now",
                            "status": "in_progress",
                        })

                    # Human-readable orchestration + progress (avoid raw args/JSON dumps)
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": tool_name,
                        "agent": agent_label,
                        "timestamp": "now",
                        "text": _ws_line(f"Master Orchestrator → {agent_label}"),
                    })

                    start_summary = _summarize_tool_start(tool_name, tool_args)
                    if start_summary:
                        await websocket.send_json({
                            "type": "timeline_log",
                            "request_id": request_id,
                            "tool": tool_name,
                            "agent": agent_label,
                            "timestamp": "now",
                            "text": _ws_line(start_summary),
                        })

                    # Execute tool
                    tool_ok = True
                    try:
                        tool_result = await asyncio.to_thread(_execute_tool, tool_call)
                    except Exception as e:
                        tool_ok = False
                        tool_result = {
                            "status": "error", "message": f"Tool execution error: {str(e)}"}

                    result_summary = _summarize_tool_result(
                        tool_name, tool_result)
                    if result_summary:
                        await websocket.send_json({
                            "type": "timeline_log",
                            "request_id": request_id,
                            "tool": tool_name,
                            "agent": agent_label,
                            "timestamp": "now",
                            "text": _ws_line(result_summary),
                        })

                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": tool_name,
                        "agent": agent_label,
                        "timestamp": "now",
                        "text": _ws_line(f"{agent_label} → Master Orchestrator"),
                    })

                    # Append tool result into conversation
                    state["messages"].append(
                        ToolMessage(content=str(tool_result),
                                    tool_call_id=(tool_call or {}).get("id"))
                    )

                    await websocket.send_json({
                        "type": "timeline_end",
                        "request_id": request_id,
                        "agent": agent_label,
                        "tool": tool_name,
                        "timestamp": "now",
                        "status": "completed" if tool_ok else "error",
                    })

            # Build response data similar to /api/chat behavior
            response_data: Dict[str, Any]

            # Try last tool JSON as response
            response_data = {}
            for msg in reversed(state["messages"]):
                if isinstance(msg, ToolMessage):
                    try:
                        parsed = json.loads(msg.content)
                        if isinstance(parsed, dict):
                            response_data = parsed
                            break
                    except Exception:
                        pass

            if not response_data:
                response_data = {
                    "response": final_ai_text if final_ai_text else "I apologize, but I couldn't generate a response. Please try again.",
                    "agent_calls": agent_calls,
                }
            else:
                # Keep frontend compatibility
                response_data.setdefault("agent_calls", agent_calls)
                if "response" not in response_data and isinstance(final_ai_text, str) and final_ai_text.strip():
                    response_data["response"] = final_ai_text
                if "response" not in response_data and isinstance(response_data.get("responses"), dict):
                    default_text = response_data.get(
                        "responses", {}).get("default")
                    if isinstance(default_text, str) and default_text.strip():
                        response_data["response"] = default_text

            # Stream assistant text if present
            if isinstance(response_data.get("response"), str):
                await _ws_stream_text(websocket, request_id, response_data.get("response", ""))

            # Save assistant response best-effort
            try:
                assistant_text = response_data.get("response")
                if isinstance(assistant_text, str) and assistant_text.strip():
                    save_message(customer_id, session_id,
                                 "assistant", assistant_text, agent_calls)
            except Exception:
                pass

            # ---- Autonomous Upsell after View Cart ----
            # If view_cart_agent was called, trigger upsell_agent → inventory_agent → recommendation_agent
            if "view_cart_agent" in agent_calls and response_data.get("cart_items"):
                try:
                    from intelligent_agent_graph import (
                        upsell_agent as _upsell_tool,
                        inventory_agent as _inventory_tool,
                        recommendation_agent as _recommendation_tool,
                    )

                    # --- Upsell Agent timeline ---
                    upsell_tool_name = "upsell_agent"
                    upsell_label = tool_to_agent.get(
                        upsell_tool_name, "Upsell Agent")
                    agent_calls.append(upsell_tool_name)

                    await websocket.send_json({
                        "type": "timeline_start",
                        "request_id": request_id,
                        "agent": upsell_label,
                        "tool": upsell_tool_name,
                        "timestamp": "now",
                        "status": "in_progress",
                    })
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": upsell_tool_name,
                        "agent": upsell_label,
                        "timestamp": "now",
                        "text": _ws_line(f"Master Orchestrator → {upsell_label}"),
                    })
                    upsell_start = _summarize_tool_start(
                        upsell_tool_name, {"customer_id": customer_id})
                    if upsell_start:
                        await websocket.send_json({
                            "type": "timeline_log",
                            "request_id": request_id,
                            "tool": upsell_tool_name,
                            "agent": upsell_label,
                            "timestamp": "now",
                            "text": _ws_line(upsell_start),
                        })

                    upsell_raw = await asyncio.to_thread(
                        _upsell_tool.invoke, {"customer_id": customer_id}
                    )
                    upsell_data = json.loads(upsell_raw) if isinstance(
                        upsell_raw, str) else upsell_raw
                    upsell_categories = upsell_data.get("categories", [])
                    if not upsell_categories:
                        upsell_categories = [
                            upsell_data.get("category", "Accessories")]

                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": upsell_tool_name,
                        "agent": upsell_label,
                        "timestamp": "now",
                        "text": _ws_line(f"Upsell categories: {', '.join(upsell_categories[:4])}"),
                    })
                    await websocket.send_json({
                        "type": "timeline_end",
                        "request_id": request_id,
                        "agent": upsell_label,
                        "tool": upsell_tool_name,
                        "timestamp": "now",
                        "status": "completed",
                    })

                    # --- Inventory Agent timeline (upsell search across categories) ---
                    inv_tool_name = "inventory_agent"
                    inv_label = tool_to_agent.get(
                        inv_tool_name, "Inventory Agent")
                    agent_calls.append(inv_tool_name)

                    await websocket.send_json({
                        "type": "timeline_start",
                        "request_id": request_id,
                        "agent": inv_label,
                        "tool": inv_tool_name,
                        "timestamp": "now",
                        "status": "in_progress",
                    })
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": inv_tool_name,
                        "agent": inv_label,
                        "timestamp": "now",
                        "text": _ws_line(f"{upsell_label} → {inv_label}"),
                    })

                    # Loop through candidate categories until we collect 4 unique products
                    _upsell_collected = []
                    _upsell_seen_pids = set()
                    _UPSELL_TARGET = 4
                    for _ucat in upsell_categories:
                        if len(_upsell_collected) >= _UPSELL_TARGET:
                            break
                        try:
                            _upsell_inv_query = f"show me {_ucat}"
                            _cat_inv_raw = await asyncio.to_thread(
                                _inventory_tool.invoke,
                                {"search_query": _upsell_inv_query,
                                    "customer_id": customer_id},
                            )
                            _cat_inv_data = json.loads(_cat_inv_raw) if isinstance(
                                _cat_inv_raw, str) else _cat_inv_raw
                            for _up in _cat_inv_data.get("products", []):
                                _upid = _up.get("product_id")
                                if _upid and _upid not in _upsell_seen_pids:
                                    _upsell_seen_pids.add(_upid)
                                    _upsell_collected.append(_up)
                                    if len(_upsell_collected) >= _UPSELL_TARGET:
                                        break
                        except Exception:
                            continue

                    # Build merged inventory result
                    inv_raw = json.dumps({
                        "status": "success",
                        "message": f"Found {len(_upsell_collected)} upsell products",
                        "products": _upsell_collected
                    })

                    inv_summary = _summarize_tool_result(
                        inv_tool_name, inv_raw)
                    if inv_summary:
                        await websocket.send_json({
                            "type": "timeline_log",
                            "request_id": request_id,
                            "tool": inv_tool_name,
                            "agent": inv_label,
                            "timestamp": "now",
                            "text": _ws_line(inv_summary),
                        })
                    await websocket.send_json({
                        "type": "timeline_end",
                        "request_id": request_id,
                        "agent": inv_label,
                        "tool": inv_tool_name,
                        "timestamp": "now",
                        "status": "completed",
                    })

                    # --- Recommendation Agent timeline (upsell display) ---
                    rec_tool_name = "recommendation_agent"
                    rec_label = tool_to_agent.get(
                        rec_tool_name, "Recommendation Agent")
                    agent_calls.append(rec_tool_name)

                    await websocket.send_json({
                        "type": "timeline_start",
                        "request_id": request_id,
                        "agent": rec_label,
                        "tool": rec_tool_name,
                        "timestamp": "now",
                        "status": "in_progress",
                    })
                    await websocket.send_json({
                        "type": "timeline_log",
                        "request_id": request_id,
                        "tool": rec_tool_name,
                        "agent": rec_label,
                        "timestamp": "now",
                        "text": _ws_line(f"{inv_label} → {rec_label}"),
                    })

                    rec_raw = await asyncio.to_thread(
                        _recommendation_tool.invoke, {
                            "inventory_data": inv_raw}
                    )

                    rec_summary = _summarize_tool_result(
                        rec_tool_name, rec_raw)
                    if rec_summary:
                        await websocket.send_json({
                            "type": "timeline_log",
                            "request_id": request_id,
                            "tool": rec_tool_name,
                            "agent": rec_label,
                            "timestamp": "now",
                            "text": _ws_line(rec_summary),
                        })
                    await websocket.send_json({
                        "type": "timeline_end",
                        "request_id": request_id,
                        "agent": rec_label,
                        "tool": rec_tool_name,
                        "timestamp": "now",
                        "status": "completed",
                    })

                    # Parse recommendation result and attach to response_data
                    rec_parsed = _try_parse_json(rec_raw)
                    if isinstance(rec_parsed, dict):
                        recs = (rec_parsed.get("responses") or {}).get(
                            "recommendation", [])
                        if recs:
                            response_data["upsell"] = rec_parsed
                            response_data["upsell"]["upsell_category"] = upsell_data.get(
                                "category", "accessories")

                except Exception as upsell_err:
                    print(
                        f"[UPSELL] Error during autonomous upsell: {upsell_err}")
                    import traceback
                    traceback.print_exc()

            await websocket.send_json({
                "type": "final_response",
                "request_id": request_id,
                "data": response_data,
            })
            await websocket.send_json({"type": "run_end", "request_id": request_id})

    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        return


@app.post("/api/kiosk/chat")
async def chat_with_kiosk(chat_message: ChatMessage):
    """Chat endpoint for the store kiosk flow."""
    try:
        customer_id = chat_message.customer_id
        user_query = (chat_message.message or "").strip()

        state = kiosk_sessions.get(
            customer_id) or _init_kiosk_state(customer_id)

        # Persist the store_id from the request into the kiosk state so that
        # welcome_node and payment_method_node can filter cart by this store.
        request_store_id = getattr(chat_message, "store_id", None) or None
        if request_store_id:
            state["kiosk_store_id"] = request_store_id

        kiosk_store_id = state.get("kiosk_store_id") or None

        # If a previous kiosk run completed, but the customer still has pending
        # offline cart items for this store, reset the kiosk session.
        try:
            with get_db_session() as session:
                filters = {"customer_id": customer_id,
                           "status": "pending", "channel": "offline"}
                operators = {"customer_id": "==",
                             "status": "==", "channel": "=="}
                if kiosk_store_id:
                    filters["store_id"] = kiosk_store_id
                    operators["store_id"] = "=="
                pending_items = cart_crud.filter(
                    session,
                    filters=filters,
                    operators=operators,
                    limit=1,
                )
            if pending_items and state.get("payment_completed"):
                state = _init_kiosk_state(customer_id)
                if request_store_id:
                    state["kiosk_store_id"] = request_store_id
                # Skip welcome step for this request; frontend already shows the cart.
                state["welcome_done"] = True
        except Exception:
            # If cart check fails, keep existing state (do not block kiosk flow).
            pass
        # Intercept kiosk barcode-style add-to-cart commands.
        # Frontend sends: "add to cart product id PRD033 quantity 2"
        q_lower = user_query.lower()
        if "add to cart" in q_lower:
            product_match = re.search(
                r"\b(PRD\d+)\b", user_query, flags=re.IGNORECASE)
            qty_match = re.search(
                r"\b(?:qty|quantity)\s*(\d+)\b", user_query, flags=re.IGNORECASE)
            size_match = re.search(
                r"\bsize\s*[:=]?\s*([A-Za-z]{1,3}|\d{1,2})\b",
                user_query,
                flags=re.IGNORECASE,
            )
            if product_match:
                product_id = product_match.group(1).upper()
                qty = int(qty_match.group(1)) if qty_match else 1
                size = size_match.group(1).strip() if size_match else None
                # Use store_id from the request if provided (passed from store keeper session)
                request_store_id = getattr(
                    chat_message, "store_id", None) or None
                tool_result = kiosk_add_to_cart_agent.invoke(
                    {
                        "product_id": product_id,
                        "quantity": qty,
                        "customer_id": customer_id,
                        "size": size,
                        "store_id": request_store_id,
                    }
                )
                kiosk_sessions[customer_id] = state
                return {"response": tool_result or ""}

        responses: List[str] = []

        if user_query == "__kiosk_start__" or not state.get("welcome_done"):
            result = welcome_node(state)
            responses.extend(_merge_kiosk_result(state, result))
            state["welcome_done"] = True
            kiosk_sessions[customer_id] = state
            return {"response": "\n\n".join(responses) if responses else ""}

        state["messages"].append(HumanMessage(content=user_query))

        if not state.get("payment_prompt_done"):
            result = payment_prompt_node(state)
            responses.extend(_merge_kiosk_result(state, result))
            state["payment_prompt_done"] = True
        elif not state.get("payment_completed"):
            result = payment_method_node(state)
            responses.extend(_merge_kiosk_result(state, result))

            if state.get("payment_completed"):
                for node in (fulfillment_node, loyalty_node, post_purchase_node):
                    node_result = node(state)
                    responses.extend(_merge_kiosk_result(state, node_result))
                state["fulfillment_done"] = True
                state["loyalty_done"] = True
                state["post_purchase_done"] = True
        else:
            responses.append("✅ This kiosk session is already completed.")

        kiosk_sessions[customer_id] = state
        return {"response": "\n\n".join(responses) if responses else ""}
    except Exception as e:
        print(f"Error in kiosk chat endpoint: {e}")
        return {"response": f"Sorry, I encountered an error: {str(e)}"}


@app.post("/api/cart/switch-to-online")
async def switch_cart_to_online(request: dict):
    """Switch customer's offline cart items to online channel for later payment"""
    try:
        customer_id = request.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID is required"}

        store_id = request.get("store_id") or None

        # Use the tool from store_kiosk_graph
        from store_kiosk_graph import switch_channel_instore_to_online
        invoke_args = {"customer_id": customer_id}
        if store_id:
            invoke_args["store_id"] = store_id
        result = switch_channel_instore_to_online.invoke(invoke_args)

        # Check if operation was successful
        if "✅" in result:
            return {"success": True, "message": result}
        else:
            return {"success": False, "error": result}
    except Exception as e:
        print(f"Error in switch_cart_to_online endpoint: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/chat/history/{customer_id}")
async def clear_chat_history(customer_id: str):
    """Clear conversation history for a customer"""
    try:
        clear_conversation_history(customer_id)
        return {"success": True, "message": f"Conversation history cleared for {customer_id}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ============ Wishlist Endpoints ============

class WishlistToggleModel(BaseModel):
    customer_id: str
    product_id: str


@app.post("/api/wishlist/toggle")
def toggle_wishlist(item: WishlistToggleModel):
    """Toggle a product in the customer's wishlist. Returns wishlisted=true/false."""
    with Session(engine) as session:
        existing = session.exec(
            select(Wishlist).where(
                Wishlist.customer_id == item.customer_id,
                Wishlist.product_id == item.product_id,
            )
        ).first()
        if existing:
            session.delete(existing)
            session.commit()
            return {"wishlisted": False, "product_id": item.product_id}
        else:
            new_entry = Wishlist(customer_id=item.customer_id,
                                 product_id=item.product_id)
            session.add(new_entry)
            session.commit()
            return {"wishlisted": True, "product_id": item.product_id}


@app.get("/api/wishlist/{customer_id}")
def get_wishlist(customer_id: str):
    """Get all wishlisted product_ids for a customer."""
    with Session(engine) as session:
        rows = session.exec(
            select(Wishlist).where(Wishlist.customer_id == customer_id)
        ).all()
        return {"product_ids": [r.product_id for r in rows]}


@app.get("/api/wishlist/{customer_id}/products")
def get_wishlist_products(customer_id: str):
    """Get full product details for all wishlisted products of a customer."""
    with Session(engine) as session:
        wishlist_rows = session.exec(
            select(Wishlist).where(Wishlist.customer_id == customer_id)
        ).all()
        product_ids = [r.product_id for r in wishlist_rows]

        if not product_ids:
            return {"products": [], "total_count": 0}

        products = []
        for pid in product_ids:
            product = get_product_from_db(pid)
            if product:
                original_price = product.price
                discount = product.discount if product.discount else 0
                discount_price = round(
                    original_price * (1 - discount / 100), 2
                ) if discount > 0 else original_price
                products.append({
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "price": original_price,
                    "discount": discount,
                    "discount_price": discount_price,
                    "category": product.category,
                    "quantity": product.quantity,
                    "image_reference": product.image_reference,
                })

        return {"products": products, "total_count": len(products)}


@app.post("/api/payload/save")
async def save_payload(payload_data: dict):
    """Save conversation log payload to chat_history database"""
    try:
        customer_id = payload_data.get("customer_id")
        payload_content = payload_data.get("payload")

        if not customer_id or not payload_content:
            return {"success": False, "error": "Missing customer_id or payload"}

        # Use chat_history.db instead of retail_agent.db
        import sqlite3
        import json
        import os

        db_path = os.path.join(os.path.dirname(__file__), "chat_history.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if customer_id already has a payload entry
        cursor.execute(
            "SELECT customer_id FROM payload WHERE customer_id = ?", (customer_id,))
        existing = cursor.fetchone()

        if existing:
            # Update existing payload for this customer
            cursor.execute(
                "UPDATE payload SET payload = ? WHERE customer_id = ?",
                (json.dumps(payload_content), customer_id)
            )
            message = f"Payload updated for customer {customer_id}"
        else:
            # Insert new payload for this customer
            cursor.execute(
                "INSERT INTO payload (customer_id, payload) VALUES (?, ?)",
                (customer_id, json.dumps(payload_content))
            )
            message = f"Payload created for customer {customer_id}"

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": message,
            "customer_id": customer_id
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/api/payload/{customer_id}")
async def get_payload(customer_id: str):
    """Retrieve conversation log payload from chat_history database by customer ID"""
    try:
        import sqlite3
        import json
        import os

        db_path = os.path.join(os.path.dirname(__file__), "chat_history.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve payload for the customer
        cursor.execute(
            "SELECT payload FROM payload WHERE customer_id = ?", (customer_id,))
        result = cursor.fetchone()

        conn.close()

        if result and result[0]:
            # Parse the JSON payload
            payload_data = json.loads(result[0])
            return {
                "success": True,
                "customer_id": customer_id,
                "payload": payload_data
            }
        else:
            return {
                "success": True,
                "customer_id": customer_id,
                "payload": None,
                "message": "No payload found for this customer"
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "payload": None}


# handle_message removed — WhatsApp messages are now processed
# by the intelligent agent graph in the /webhook POST endpoint below.


@app.post("/webhook")
async def webhook_post(request: Request):
    """
    Handle incoming Twilio WhatsApp webhook POST requests.
    Twilio sends form-encoded data with fields: Body, From, To, etc.
    Uses the intelligent agent graph (GPT-4o-mini) to process messages
    and sends rich WhatsApp responses (text + product images) via Twilio.
    """
    contact_number = None
    try:
        # Twilio sends application/x-www-form-urlencoded data
        form_data = await request.form()
        message_body = (form_data.get("Body") or "").strip()
        # e.g. "whatsapp:+919339712883"
        from_number = form_data.get("From", "")
        to_number = form_data.get("To", "")

        # Strip the "whatsapp:" prefix to get the raw phone number
        contact_number = from_number.replace("whatsapp:", "").strip()

        print(
            f"[Webhook] Twilio POST  From={from_number}  To={to_number}  Body={message_body!r}")

        if not message_body:
            send_whatsapp_text(
                contact_number, "Please send a text message so I can help you!")
            # Return empty TwiML so Twilio doesn't send a duplicate reply
            return PlainTextResponse(
                content="<Response></Response>",
                media_type="application/xml",
                status_code=200,
            )

        # Run the intelligent WhatsApp agent graph.
        # This processes the message through the full agentic journey
        # (GPT-4o-mini, inventory, recommendations, cart, payment, etc.)
        # and sends rich responses (text + product images) back via Twilio.
        await run_whatsapp_agent(
            wa_id=contact_number,
            message_body=message_body,
            phone_number=contact_number,
        )

        # Return empty TwiML — responses are sent via Twilio REST API,
        # not through TwiML reply, to support multiple messages + images.
        return PlainTextResponse(
            content="<Response></Response>",
            media_type="application/xml",
            status_code=200,
        )

    except Exception as e:
        import traceback
        logging.error(f"[Webhook] Error processing WhatsApp message: {e}")
        traceback.print_exc()
        # Try to send an error fallback to the user
        try:
            if contact_number:
                send_whatsapp_text(
                    contact_number, "Sorry, something went wrong. Please try again.")
        except Exception:
            pass
        return PlainTextResponse(
            content="<Response></Response>",
            media_type="application/xml",
            status_code=200,
        )
