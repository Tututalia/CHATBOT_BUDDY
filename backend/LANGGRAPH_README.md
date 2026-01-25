# LangGraph Multi-Agent Retail Chatbot

This backend implements a sophisticated multi-agent orchestration system using LangGraph for a retail deep care chatbot.

## Architecture Overview

The system uses **LangGraph** to orchestrate multiple specialized agents that work together to provide end-to-end retail assistance:

```
User Query
    ↓
Recommendation Agent → Suggests products based on user preferences
    ↓
Inventory Agent → Checks availability (online/offline)
    ↓
Sales Agent → Handles product selection
    ↓
[Conditional Routing]
    ├─ Online → Payment Agent → Fulfillment Agent
    └─ Offline → Fulfillment Agent
    ↓
Loyalty Agent → Processes rewards and points
    ↓
Post Purchase Agent → Sets up post-purchase services
```

## Agent Details

### 1. **Recommendation Agent**
- **Purpose**: Suggests products based on user query and preferences
- **Tools**: ProductTools (CSV-based product search)
- **LLM Role**: Intent extraction and narrative generation
- **Output**: List of recommended products with natural language introduction

### 2. **Inventory Agent**
- **Purpose**: Checks product availability across channels
- **Tools**: InventoryTools (online/offline stock checking)
- **LLM Role**: Explains availability in friendly manner
- **Output**: Channel selection (online/offline) and store information

### 3. **Sales Agent**
- **Purpose**: Manages product selection and confirms purchase intent
- **Tools**: None (uses state from previous agents)
- **LLM Role**: Generates confirmation messages
- **Output**: Sales confirmation and amount

### 4. **Payment Agent** (Online only)
- **Purpose**: Processes online payments
- **Tools**: PaymentTools (mock payment processing)
- **LLM Role**: Generates payment confirmation/failure messages
- **Output**: Payment status and payment ID

### 5. **Fulfillment Agent**
- **Purpose**: Creates and manages orders
- **Tools**: FulfillmentTools (order creation and tracking)
- **LLM Role**: Generates fulfillment confirmation
- **Output**: Order ID and fulfillment status

### 6. **Loyalty Agent**
- **Purpose**: Processes loyalty points and rewards
- **Tools**: LoyaltyTools (points calculation and coupon generation)
- **LLM Role**: Generates reward notifications
- **Output**: Points earned, total points, available coupons

### 7. **Post Purchase Agent**
- **Purpose**: Sets up post-purchase services
- **Tools**: PostPurchaseTools (tracking, support, offers)
- **LLM Role**: Generates thank you and service information
- **Output**: Tracking info, personalized offers, support details

## Key Design Principles

### 1. **Separation of Concerns**
- **LLMs**: Only for reasoning, intent extraction, and natural language generation
- **Tools**: Deterministic data access and business logic
- **UI**: Renders structured data from backend

### 2. **State Management**
LangGraph manages a shared state (`AgentState`) that flows through all agents:
```python
class AgentState:
    - messages: Conversation history
    - customer_id: Logged-in customer
    - recommended_products: From recommendation agent
    - inventory_info: From inventory agent
    - payment_status: From payment agent
    - order_id: From fulfillment agent
    - loyalty_points_earned: From loyalty agent
    - timeline: Live agent execution log
```

### 3. **Conditional Routing**
The workflow uses conditional edges to route based on channel:
- **Online purchases** → Payment Agent → Fulfillment
- **Offline purchases** → Direct to Fulfillment (no payment needed)

### 4. **Observable Execution**
Each agent adds timeline events for transparency:
```python
{
    "agent": "recommendation_agent",
    "timestamp": "2026-01-25T10:30:00",
    "action": "Products recommended",
    "details": "Found 6 products"
}
```

## API Endpoints

### POST `/api/chat`
Process a complete chat request through the agent workflow.

**Request:**
```json
{
    "customer_id": "CUST001",
    "query": "I want shirts for Christmas under 3000",
    "customer_name": "Raymond"
}
```

**Response:**
```json
{
    "success": true,
    "customer_id": "CUST001",
    "query": "...",
    "timeline": [...],
    "recommended_products": [...],
    "selected_product": {...},
    "order_id": "ORD123ABC",
    "loyalty_points_earned": 189,
    "messages": [
        "I found 6 great shirts for Christmas...",
        "The Raymond Shirt is available online...",
        ...
    ]
}
```

### WebSocket `/ws/chat/{customer_id}`
Real-time chat with streaming timeline updates.

**Client sends:**
```json
{
    "query": "Show me trending shirts",
    "customer_name": "Raymond"
}
```

**Server streams:**
```json
{"type": "timeline", "data": {...}}
{"type": "timeline", "data": {...}}
{"type": "response", "data": {...}}
```

### GET `/api/agent-flow/status`
Check orchestration system status.

## Installation

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

3. **Run the server:**
```bash
uvicorn main:app --reload --port 8000
```

## Project Structure

```
backend/
├── langgraph_orchestrator.py   # Main LangGraph workflow
├── agents/                      # Individual agent modules
│   ├── recommendation_agent.py
│   ├── inventory_agent.py
│   ├── sales_agent.py
│   ├── payment_agent.py
│   ├── fulfillment_agent.py
│   ├── loyalty_agent.py
│   └── post_purchase_agent.py
├── tools/                       # Deterministic tools
│   ├── product_tools.py
│   ├── inventory_tools.py
│   ├── payment_tools.py
│   ├── fulfillment_tools.py
│   ├── loyalty_tools.py
│   └── post_purchase_tools.py
├── data/                        # CSV data files
│   ├── product_data.csv
│   ├── customer_data.csv
│   └── ...
└── main.py                      # FastAPI application
```

## Testing

Test the agent flow:

```bash
# Test recommendation
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "query": "Show me shirts under 3000"
  }'

# Check status
curl http://localhost:8000/api/agent-flow/status
```

## Extending the System

### Adding a New Agent

1. Create agent file in `agents/`:
```python
class MyAgent:
    def __init__(self, llm):
        self.llm = llm
    
    def execute(self, state):
        # Agent logic
        return state
```

2. Add to orchestrator in `langgraph_orchestrator.py`:
```python
workflow.add_node("my_agent", self.my_agent)
workflow.add_edge("previous_agent", "my_agent")
```

3. Update state definition to include new fields if needed.

### Adding New Tools

1. Create tool file in `tools/`:
```python
class MyTools:
    def do_something(self, param):
        # Deterministic logic
        return result
```

2. Import and use in relevant agent.

## LangGraph Benefits

- ✅ **Visual workflow**: Easy to understand agent flow
- ✅ **State management**: Automatic state passing between agents
- ✅ **Conditional routing**: Smart decision-based routing
- ✅ **Async support**: Efficient concurrent execution
- ✅ **Extensible**: Easy to add/modify agents
- ✅ **Debuggable**: Clear execution path and state inspection

## Environment Variables

See `.env.example` for required configuration:
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)
- `LLM_MODEL`: Model to use (default: gemini-2.0-flash-exp)
- `LLM_TEMPERATURE`: Temperature setting (default: 0.3)

## Dependencies

Key packages:
- `langgraph`: Agent orchestration framework
- `langchain-google-genai`: Google Gemini LLM integration
- `fastapi`: Web framework
- `pandas`: Data processing
- `websockets`: Real-time communication

See `requirements.txt` for complete list.
