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
)
from models import Customer, Product, Store, OrderHistory, StoreKeeperTransaction, AdminDashboardData, Payload
from database import engine, get_db_session
from chat_database import save_message, get_conversation_history, clear_conversation_history
from langchain_core.messages import HumanMessage, AIMessage
from intelligent_agent_graph import run_agent, create_agent_graph
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict
import json
import asyncio
import re
from sqlmodel import Session, select, func
from dotenv import load_dotenv
from whatsapp import send_message
from security import signature_required
from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime

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
            return order_history_crud.filter(session, {'customer_id': customer_id})
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
        "add_to_cart_agent": "Add to Cart Agent",
        "view_cart_agent": "View Cart Agent",
        "remove_from_cart_agent": "Remove from Cart Agent",
        "choose_channel_agent": "Sales Agent",
        "payment_agent": "Payment Agent",
        "fulfillment_agent": "Fulfillment Agent",
        "loyalty_agent": "Loyalty Agent",
        "post_purchase_agent": "Post-Purchase Agent",
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
            order_products.append({
                "transaction_id": order.transaction_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "price": product.price,
                "quantity": order.quantity,
                "purchase_date": order.order_dates,
                "loyalty_points": order.loyalty_points,
                "image_reference": product.image_reference
            })

    return {
        "customer_id": customer_id,
        "order_history": order_products
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
                    "phone": customer.phone or '',
                    "address": customer.address or '',
                    "loyalty_points": customer.loyalty_points,
                    "role_id": customer.role_id,
                    "order_history": order_history,
                    "pending_orders": pending_orders
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


@app.get("/api/admin/dashboard")
def get_admin_dashboard_data(time_range: str = "1month"):
    """
    Get comprehensive admin dashboard analytics including:
    - Total customers count
    - Total products sold
    - Total retail stores
    - Online vs Offline transactions (based on time_range)
    - Offline purchases per store

    Args:
        time_range: Filter by time range - '7days', '1month', or 'all' (default: '1month')
    """
    try:
        with get_db_session() as session:
            from datetime import datetime, timedelta
            from collections import defaultdict

            # Get total customers count
            total_customers = session.exec(
                select(func.count(Customer.customer_id))
            ).one()

            # Get total retail stores count
            total_stores = session.exec(
                select(func.count(Store.store_id))
            ).one()

            # Get admin dashboard data (all transactions)
            all_transactions = admin_dashboard_data_crud.get_all(
                session, skip=0, limit=100000)

            # Calculate total products sold (sum of quantities from all transactions)
            total_products_sold = sum(tx.qty for tx in all_transactions)

            # Determine date threshold based on time_range
            now = datetime.now()
            date_threshold = None
            time_period_label = "All Time"

            if time_range == "7days":
                date_threshold = now - timedelta(days=7)
                time_period_label = "Last 7 Days"
            elif time_range == "1month":
                date_threshold = now - timedelta(days=30)
                time_period_label = "Last 1 Month"
            # else: time_range == "all", no date threshold

            # Analyze transactions based on time range
            online_transactions = []
            offline_transactions = []
            store_purchases = defaultdict(int)
            total_revenue = 0
            online_revenue = 0
            offline_revenue = 0

            for tx in all_transactions:
                # Parse transaction date with multiple format attempts
                tx_date = None
                try:
                    # Try M/D/YYYY format (e.g., "1/15/2026")
                    tx_date = datetime.strptime(tx.date, "%m/%d/%Y")
                except:
                    try:
                        # Try YYYY-MM-DD format
                        tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
                    except:
                        try:
                            # Try DD-MM-YYYY format
                            tx_date = datetime.strptime(tx.date, "%d-%m-%Y")
                        except:
                            try:
                                # Try MM/DD/YYYY format with zero padding
                                tx_date = datetime.strptime(
                                    tx.date.strip(), "%m/%d/%Y")
                            except:
                                # Skip transactions with unparseable dates
                                print(f"Could not parse date: {tx.date}")
                                continue

                # Filter by date threshold (if set) or include all
                if date_threshold is None or tx_date >= date_threshold:
                    if tx.mode.lower() == "online":
                        online_transactions.append(tx)
                        online_revenue += tx.amount
                    else:
                        offline_transactions.append(tx)
                        offline_revenue += tx.amount
                        # Count purchases per store for offline only
                        store_purchases[tx.store_name] += tx.qty

                # Total revenue from all transactions (regardless of time filter)
                if date_threshold is None or tx_date >= date_threshold:
                    total_revenue += tx.amount

            # Calculate total transactions for the selected period
            total_transactions = len(
                online_transactions) + len(offline_transactions)

            # Calculate average transaction value for the selected period
            avg_transaction_value = total_revenue / \
                total_transactions if total_transactions > 0 else 0

            # Format offline purchases per store (sorted by purchase count)
            offline_purchases_per_store = [
                {
                    "store_name": store_name,
                    "purchases_count": count
                }
                for store_name, count in sorted(
                    store_purchases.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

            # Calculate online vs offline percentages
            online_percentage = (len(
                online_transactions) / total_transactions * 100) if total_transactions > 0 else 0
            offline_percentage = (len(
                offline_transactions) / total_transactions * 100) if total_transactions > 0 else 0

            # Calculate monthly transaction trends (respecting time_range filter)
            monthly_online = defaultdict(int)
            monthly_offline = defaultdict(int)

            # Use filtered transactions for monthly trends
            filtered_tx_for_trends = online_transactions + offline_transactions

            for tx in filtered_tx_for_trends:
                # Parse transaction date
                tx_date = None
                try:
                    tx_date = datetime.strptime(tx.date, "%m/%d/%Y")
                except:
                    try:
                        tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
                    except:
                        try:
                            tx_date = datetime.strptime(tx.date, "%d-%m-%Y")
                        except:
                            continue

                # Get month-year key
                month_key = tx_date.strftime("%b")  # e.g., "Jan", "Feb"

                # Count by mode
                if tx.mode.lower() == "online":
                    monthly_online[month_key] += 1
                else:
                    monthly_offline[month_key] += 1

            # Create monthly trends list with proper month ordering
            month_order = ["Jan", "Feb", "Mar", "Apr", "May",
                           "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            monthly_trends = []
            for month in month_order:
                if month in monthly_online or month in monthly_offline:
                    monthly_trends.append({
                        "month": month,
                        "online": monthly_online.get(month, 0),
                        "offline": monthly_offline.get(month, 0),
                        "total": monthly_online.get(month, 0) + monthly_offline.get(month, 0)
                    })

            # Format all transactions for the table view
            all_transactions_list = []
            for tx in all_transactions:
                all_transactions_list.append({
                    "id": tx.id,
                    "date": tx.date,
                    "user_name": tx.user_name,
                    "product": tx.product,
                    "qty": tx.qty,
                    "mode": tx.mode,
                    "store_name": tx.store_name,
                    "status": tx.status,
                    "amount": tx.amount,
                    "address": tx.address,
                    "phone": tx.phone
                })

            # Sort transactions by date (most recent first)
            try:
                all_transactions_list.sort(key=lambda x: datetime.strptime(
                    x["date"], "%m/%d/%Y"), reverse=True)
            except:
                pass  # If date parsing fails, keep original order

            return {
                "summary": {
                    "total_customers": total_customers,
                    "total_products_sold": total_products_sold,
                    "total_retail_stores": total_stores,
                    "total_transactions": total_transactions,
                    "total_revenue": round(total_revenue, 2),
                    "avg_transaction_value": round(avg_transaction_value, 2)
                },
                "transactions_overview": {
                    "time_period": time_period_label,
                    "time_range": time_range,
                    "online": {
                        "count": len(online_transactions),
                        "percentage": round(online_percentage, 1),
                        "revenue": round(online_revenue, 2)
                    },
                    "offline": {
                        "count": len(offline_transactions),
                        "percentage": round(offline_percentage, 1),
                        "revenue": round(offline_revenue, 2)
                    }
                },
                "monthly_trends": monthly_trends,
                "total_online_transactions": sum(monthly_online.values()),
                "total_offline_transactions": sum(monthly_offline.values()),
                "offline_purchases_per_store": offline_purchases_per_store,
                "transactions": all_transactions_list
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
                "avg_transaction_value": 0
            },
            "transactions_overview": {
                "time_period": "Past 1 Month",
                "online": {"count": 0, "percentage": 0, "revenue": 0},
                "offline": {"count": 0, "percentage": 0, "revenue": 0}
            },
            "offline_purchases_per_store": []
        }


@app.get("/api/admin/ai-insights")
def get_admin_ai_insights(time_range: str = "1month"):
    """
    Get AI-powered insights and recommendations for the admin dashboard.
    Uses LLM to analyze transaction data and provide actionable intelligence.

    Args:
        time_range: Filter by time range - '7days', '1month', or 'all' (default: '1month')
    """
    try:
        from langchain_openai import ChatOpenAI
        from datetime import datetime, timedelta
        from collections import defaultdict

        with get_db_session() as session:
            # Get all dashboard data
            all_transactions = admin_dashboard_data_crud.get_all(
                session, skip=0, limit=100000)

            # Determine date threshold
            now = datetime.now()
            date_threshold = None
            time_period_label = "All Time"

            if time_range == "7days":
                date_threshold = now - timedelta(days=7)
                time_period_label = "Last 7 Days"
            elif time_range == "1month":
                date_threshold = now - timedelta(days=30)
                time_period_label = "Last 1 Month"

            # Filter and analyze transactions
            filtered_transactions = []
            online_count = 0
            offline_count = 0
            online_revenue = 0
            offline_revenue = 0
            store_performance = defaultdict(lambda: {"count": 0, "revenue": 0})
            product_performance = defaultdict(
                lambda: {"count": 0, "revenue": 0})
            customer_frequency = defaultdict(int)

            for tx in all_transactions:
                # Parse date
                tx_date = None
                try:
                    tx_date = datetime.strptime(tx.date, "%m/%d/%Y")
                except:
                    try:
                        tx_date = datetime.strptime(tx.date, "%Y-%m-%d")
                    except:
                        try:
                            tx_date = datetime.strptime(tx.date, "%d-%m-%Y")
                        except:
                            continue

                # Filter by date threshold
                if date_threshold is None or tx_date >= date_threshold:
                    filtered_transactions.append(tx)

                    if tx.mode.lower() == "online":
                        online_count += 1
                        online_revenue += tx.amount
                    else:
                        offline_count += 1
                        offline_revenue += tx.amount
                        store_performance[tx.store_name]["count"] += 1
                        store_performance[tx.store_name]["revenue"] += tx.amount

                    product_performance[tx.product]["count"] += tx.qty
                    product_performance[tx.product]["revenue"] += tx.amount
                    customer_frequency[tx.user_name] += 1

            # Calculate insights
            total_transactions = len(filtered_transactions)
            total_revenue = online_revenue + offline_revenue
            avg_transaction = total_revenue / \
                total_transactions if total_transactions > 0 else 0
            online_percentage = (
                online_count / total_transactions * 100) if total_transactions > 0 else 0

            # Get top performing products
            top_products = sorted(product_performance.items(
            ), key=lambda x: x[1]["revenue"], reverse=True)[:3]

            # Get top stores
            top_stores = sorted(store_performance.items(),
                                key=lambda x: x[1]["revenue"], reverse=True)[:3]

            # Get top customers
            top_customers = sorted(
                customer_frequency.items(), key=lambda x: x[1], reverse=True)[:5]

            # Prepare data summary for LLM
            data_summary = f"""
Analyze the following retail dashboard data for {time_period_label}:

OVERALL METRICS:
- Total Transactions: {total_transactions:,}
- Total Revenue: ₹{total_revenue:,.2f}
- Average Transaction Value: ₹{avg_transaction:,.2f}
- Online Sales: {online_count:,} transactions (₹{online_revenue:,.2f})
- Offline Sales: {offline_count:,} transactions (₹{offline_revenue:,.2f})
- Online Percentage: {online_percentage:.1f}%

TOP PERFORMING PRODUCTS:
{chr(10).join([f"- {prod}: {data['count']} units sold, ₹{data['revenue']:,.2f} revenue" for prod, data in top_products[:3]])}

TOP PERFORMING STORES (Offline):
{chr(10).join([f"- {store}: {data['count']} transactions, ₹{data['revenue']:,.2f} revenue" for store, data in top_stores[:3]])}

TOP CUSTOMERS (by frequency):
{chr(10).join([f"- {customer}: {count} purchases" for customer, count in top_customers[:5]])}

Provide insights in the following JSON format:
{{
  "overview": "Brief performance summary in 2-3 sentences",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
  "opportunities": [
    {{"area": "area name", "suggestion": "specific suggestion", "potential_savings": "estimated impact"}}
  ]
}}

Focus on actionable insights about:
1. Revenue trends and transaction patterns
2. Product performance and inventory optimization
3. Store performance differences
4. Customer behavior and retention strategies
5. Channel optimization (online vs offline)
"""

            # Initialize LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )

            # Get AI insights
            response = llm.invoke(data_summary)

            # Parse LLM response
            try:
                # Extract JSON from response
                response_text = response.content

                # Find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

                if json_match:
                    insights_data = json.loads(json_match.group())
                else:
                    # Fallback if JSON not found
                    insights_data = {
                        "overview": response_text[:200],
                        "key_insights": ["Unable to parse structured insights"],
                        "recommendations": ["Please refresh to try again"],
                        "opportunities": []
                    }
            except Exception as parse_error:
                print(f"Error parsing LLM response: {parse_error}")
                insights_data = {
                    "overview": "Analysis completed but unable to format insights properly.",
                    "key_insights": ["Data has been analyzed successfully"],
                    "recommendations": ["Refresh to generate new insights"],
                    "opportunities": []
                }

            return {
                "insights": insights_data,
                "time_period": time_period_label,
                "data_summary": {
                    "total_transactions": total_transactions,
                    "total_revenue": round(total_revenue, 2),
                    "avg_transaction_value": round(avg_transaction, 2),
                    "online_percentage": round(online_percentage, 1)
                }
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error generating AI insights: {str(e)}",
            "insights": {
                "overview": "Unable to generate insights at this time.",
                "key_insights": [],
                "recommendations": [],
                "opportunities": []
            }
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


class UpdateCartQuantityModel(BaseModel):
    order_id: str
    quantity: int


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

        # Save user message to database
        save_message(customer_id, session_id, "user", user_query)

        # Get conversation history from database (limit to recent messages to force fresh tool calls)
        history = get_conversation_history(customer_id, session_id, limit=1)

        print(f"Retrieved {len(history)} messages from history")

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

            if not customer_id or not user_query:
                await websocket.send_json({
                    "type": "error",
                    "request_id": request_id,
                    "message": "Missing customer_id or message",
                })
                continue

            session_id = customer_id

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

        # If a previous kiosk run completed, but the customer still has pending cart items,
        # reset the kiosk session so users can pay for the new items.
        try:
            with get_db_session() as session:
                pending_items = cart_crud.filter(
                    session,
                    filters={"customer_id": customer_id, "status": "pending"},
                    operators={"customer_id": "==", "status": "=="},
                    limit=1,
                )
            if pending_items and state.get("payment_completed"):
                state = _init_kiosk_state(customer_id)
                # Skip welcome step for this request; frontend already shows the cart.
                state["welcome_done"] = True
        except Exception:
            # If cart check fails, keep existing state (do not block kiosk flow).
            pass
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


@app.delete("/api/chat/history/{customer_id}")
async def clear_chat_history(customer_id: str):
    """Clear conversation history for a customer"""
    try:
        clear_conversation_history(customer_id)
        return {"success": True, "message": f"Conversation history cleared for {customer_id}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


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


async def handle_message(body: dict):
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A JSON response with appropriate HTTP status code.
    """
    # logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return JSONResponse(content={"status": "ok"}, status_code=200)

    try:
        # if is_valid_whatsapp_message(body):
        #     process_whatsapp_message(body)
        send_message(body)
        return JSONResponse(content={"status": "ok"}, status_code=200)
        # else:
        #     # if the request is not a WhatsApp API event, return an error
        #     raise HTTPException(
        #         status_code=404,
        #         detail="Not a WhatsApp API event"
        #     )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON provided"
        )


@app.post("/webhook")
@signature_required
async def webhook_post(request: Request):
    """
    Handle incoming webhook POST requests from WhatsApp.
    """
    # Get body from request state (stored by decorator)
    import json
    # import pdb; pdb.set_trace()
    body = json.loads(request.state.body)
    print(body)
    return await handle_message(body)
