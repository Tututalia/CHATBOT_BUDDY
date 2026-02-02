from crud import (
    product_crud, customer_crud, store_crud, order_history_crud,
    store_keeper_transaction_crud,
    ProductCRUD, CustomerCRUD
)
from models import Customer, Product, Store, OrderHistory, StoreKeeperTransaction
from database import engine, get_db_session
from chat_database import save_message, get_conversation_history, clear_conversation_history
from langchain_core.messages import HumanMessage, AIMessage
from intelligent_agent_graph import run_agent, create_agent_graph
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import asyncio
from sqlmodel import Session
from dotenv import load_dotenv

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
                                tx_date = datetime.fromisoformat(tx.date.replace('Z', '+00:00'))
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
                percentage = (count / total_orders * 100) if total_orders > 0 else 0
                daily_orders.append({
                    "date": date_str,
                    "count": count,
                    "percentage": round(percentage, 1)
                })

            # Calculate peak day and average
            peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else (None, 0)
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
    customer_id: str
    message: str
    conversation_history: List[Dict[str, str]] = []

    class Config:
        extra = "allow"  # Allow extra fields


class ChatResponse(BaseModel):
    response: str
    agent_calls: List[str] = []


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
        history = get_conversation_history(customer_id, session_id, limit=6)

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
        timeline_messages = []
        from langchain_core.messages import ToolMessage, AIMessage as LangChainAIMessage
        
        # Map tool names to agent names for timeline display
        tool_to_agent_map = {
            "search_products": "Inventory Agent",
            "recommend_products": "Recommendation Agent",
            "add_to_cart": "Add to Cart Agent",
            "view_cart": "View Cart Agent",
            "remove_from_cart": "Remove from Cart Agent",
            "process_payment": "Payment Agent",
            "schedule_delivery": "Fulfillment Agent",
            "apply_loyalty_rewards": "Loyalty Agent",
            "get_customer_info": "Customer Info Agent",
            "post_purchase_support": "Post-Purchase Agent"
        }
        
        # Track which agents have been called
        seen_agents = set()
        
        for message in result["messages"]:
            # Check for tool calls in AIMessage
            if isinstance(message, LangChainAIMessage) and hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get("name", "")
                    agent_name = tool_to_agent_map.get(tool_name, tool_name)
                    
                    # Only add each agent once to timeline
                    if agent_name not in seen_agents:
                        seen_agents.add(agent_name)
                        timeline_messages.append({
                            "agent": agent_name,
                            "timestamp": "now"
                        })

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


@app.delete("/api/chat/history/{customer_id}")
async def clear_chat_history(customer_id: str):
    """Clear conversation history for a customer"""
    try:
        clear_conversation_history(customer_id)
        return {"success": True, "message": f"Conversation history cleared for {customer_id}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
