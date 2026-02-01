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

        # Get conversation history from database
        history = get_conversation_history(customer_id, session_id, limit=20)

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

        # Try to return tool output as JSON if present
        from langchain_core.messages import ToolMessage
        for message in reversed(result["messages"]):
            if isinstance(message, ToolMessage):
                try:
                    return json.loads(message.content)
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
        print(f"AI Response: {ai_response[:100]}...")
        print(f"Agent Calls: {agent_calls}")
        print(f"{'='*60}\n")

        # Save assistant response to database
        if ai_response:
            save_message(customer_id, session_id, "assistant",
                         ai_response, agent_calls)

        # Return as legacy chat response if not a tool JSON
        return {
            "response": ai_response if ai_response else "I apologize, but I couldn't generate a response. Please try again.",
            "agent_calls": agent_calls
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
