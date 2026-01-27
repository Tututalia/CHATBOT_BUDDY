from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import asyncio
from sqlmodel import Session

# Import LangGraph orchestrator
from langgraph_orchestrator import RetailAgentOrchestrator

# Import intelligent agent graph
from intelligent_agent_graph import run_agent, create_agent_graph
from langchain_core.messages import HumanMessage, AIMessage

# Import chat database
from chat_database import save_message, get_conversation_history, clear_conversation_history

# Import database and CRUD modules
from database import engine
from models import Customer, Product, Store, OrderHistory
from crud import (
    product_crud, customer_crud, store_crud, order_history_crud,
    ProductCRUD, CustomerCRUD
)

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


# Database session helper
def get_db_session():
    """Get a database session"""
    return Session(engine)


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
            "loyalty_points": p.loyalty_points
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
        "loyalty_points": product.loyalty_points
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


@app.get("/api/customer/{customer_id}")
def get_customer_profile(customer_id: str):
    """Get customer profile by customer ID"""
    customer = load_customer_from_db(customer_id)

    if customer is None:
        return {"error": f"Customer with ID {customer_id} not found"}

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
        "order_history": order_history,
        "pending_orders": pending_orders
    }


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
                "loyalty_points": product.loyalty_points
            })

    return {
        "products": products,
        "total_count": len(products)
    }


# ============ LangGraph Agent Orchestration Endpoints ============

# Request/Response Models
class ChatRequest(BaseModel):
    customer_id: str
    query: str
    customer_name: str = None


class ChatResponse(BaseModel):
    success: bool
    customer_id: str
    query: str
    timeline: List[Dict[str, Any]]
    recommended_products: List[Dict[str, Any]] = []
    selected_product: Dict[str, Any] = None
    inventory_info: Dict[str, Any] = None
    channel: str = None
    payment_status: str = None
    order_id: str = None
    loyalty_points_earned: int = 0
    messages: List[str] = []
    error: str = None


# Initialize orchestrator (lazy loading)
_orchestrator = None


def get_orchestrator() -> RetailAgentOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        # Get API key from environment
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        _orchestrator = RetailAgentOrchestrator(google_api_key=google_api_key)
    return _orchestrator


@app.post("/api/chat/orchestrator", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process chat request through LangGraph agent orchestration (OLD ENDPOINT)

    This endpoint runs the complete multi-agent workflow:
    1. Recommendation Agent
    2. Inventory Agent
    3. Sales Agent
    4. Payment Agent (if online)
    5. Fulfillment Agent
    6. Loyalty Agent
    7. Post Purchase Agent
    """
    try:
        orchestrator = get_orchestrator()

        # Run the workflow
        result = await orchestrator.arun(
            customer_id=request.customer_id,
            query=request.query,
            customer_name=request.customer_name
        )

        # Extract messages from state
        messages = [
            msg.content for msg in result.get("messages", [])
            if hasattr(msg, 'content')
        ]

        # Get selected product details
        selected_product = None
        if result.get("selected_product_id") and result.get("recommended_products"):
            for p in result["recommended_products"]:
                if p["product_id"] == result["selected_product_id"]:
                    selected_product = p
                    break

        return ChatResponse(
            success=True,
            customer_id=request.customer_id,
            query=request.query,
            timeline=result.get("timeline", []),
            recommended_products=result.get("recommended_products", []),
            selected_product=selected_product,
            inventory_info=result.get("inventory_info"),
            channel=result.get("channel"),
            payment_status=result.get("payment_status"),
            order_id=result.get("order_id"),
            loyalty_points_earned=result.get("loyalty_points_earned", 0),
            messages=messages
        )

    except Exception as e:
        return ChatResponse(
            success=False,
            customer_id=request.customer_id,
            query=request.query,
            timeline=[],
            error=str(e)
        )


@app.websocket("/ws/chat/{customer_id}")
async def websocket_chat(websocket: WebSocket, customer_id: str):
    """
    WebSocket endpoint for real-time chat with agent timeline updates
    """
    await websocket.accept()

    try:
        orchestrator = get_orchestrator()

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            query = message_data.get("query", "")

            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "message": "Processing your request..."
            })

            # Run workflow
            result = await orchestrator.arun(
                customer_id=customer_id,
                query=query,
                customer_name=message_data.get("customer_name")
            )

            # Stream timeline events
            for event in result.get("timeline", []):
                await websocket.send_json({
                    "type": "timeline",
                    "data": event
                })
                await asyncio.sleep(0.5)  # Small delay for better UX

            # Extract messages
            messages = [
                msg.content for msg in result.get("messages", [])
                if hasattr(msg, 'content')
            ]

            # Send final response
            await websocket.send_json({
                "type": "response",
                "data": {
                    "recommended_products": result.get("recommended_products", []),
                    "selected_product_id": result.get("selected_product_id"),
                    "inventory_info": result.get("inventory_info"),
                    "channel": result.get("channel"),
                    "order_id": result.get("order_id"),
                    "loyalty_points_earned": result.get("loyalty_points_earned", 0),
                    "messages": messages
                }
            })

    except WebSocketDisconnect:
        print(f"Client {customer_id} disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


@app.get("/api/agent-flow/status")
def get_agent_flow_status():
    """Get status of the agent orchestration system"""
    try:
        orchestrator = get_orchestrator()
        return {
            "status": "active",
            "llm_model": "gemini-2.0-flash-exp",
            "agents": [
                "recommendation_agent",
                "inventory_agent",
                "sales_agent",
                "payment_agent",
                "fulfillment_agent",
                "loyalty_agent",
                "post_purchase_agent"
            ],
            "workflow_type": "langgraph"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
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


@app.post("/api/chat", response_model=ChatResponse)
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

        # Add current query (already in history, but need for state)
        # The last message should be the user query

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

        # Extract the AI response from messages
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

        return ChatResponse(
            response=ai_response if ai_response else "I apologize, but I couldn't generate a response. Please try again.",
            agent_calls=agent_calls
        )

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR in chat endpoint:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")

        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            agent_calls=[]
        )


@app.delete("/api/chat/history/{customer_id}")
async def clear_chat_history(customer_id: str):
    """Clear conversation history for a customer"""
    try:
        clear_conversation_history(customer_id)
        return {"success": True, "message": f"Conversation history cleared for {customer_id}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
