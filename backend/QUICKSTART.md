# 🚀 Quick Start Guide - LangGraph Retail Agent

## Installation Steps

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the example env file
copy .env.example .env   # Windows
# or
cp .env.example .env     # macOS/Linux

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_actual_api_key_here
```

### 5. Get Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in your `.env` file

## Running the Application

### Option 1: Run FastAPI Server
```bash
uvicorn main:app --reload --port 8000
```

The server will start at: `http://localhost:8000`

### Option 2: Test the Agent Flow Directly
```bash
python test_langgraph_flow.py
```

This will run a complete test of the agent workflow and show you:
- Agent timeline
- Messages from each agent
- Product recommendations
- Order details
- Loyalty points

## Testing the API

### Test with cURL
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\": \"CUST001\", \"query\": \"I want shirts for Christmas under 3000\", \"customer_name\": \"Raymond\"}"
```

### Test with Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "customer_id": "CUST001",
        "query": "Show me trending shirts",
        "customer_name": "Raymond"
    }
)

print(response.json())
```

### Check Agent Status
```bash
curl http://localhost:8000/api/agent-flow/status
```

## WebSocket Testing

### Using Python
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/CUST001"
    
    async with websockets.connect(uri) as websocket:
        # Send query
        await websocket.send(json.dumps({
            "query": "I want to buy jeans",
            "customer_name": "Raymond"
        }))
        
        # Receive responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Type: {data['type']}")
            print(f"Data: {data}")
            
            if data['type'] == 'response':
                break

asyncio.run(test_websocket())
```

## Workflow Visualization

```
User Query: "I want shirts for Christmas under 3000"
    ↓
📝 Recommendation Agent
   - Extracts intent: category=shirt, max_price=3000, occasion=Christmas
   - Searches products from CSV
   - Returns 6 matching products
   - Narrates: "I found 6 great shirts for Christmas..."
    ↓
📦 Inventory Agent
   - Checks availability for selected product
   - Finds: Online available + 3 offline stores
   - Narrates: "The Raymond Shirt is available online and at 3 stores..."
    ↓
🛒 Sales Agent
   - Confirms product selection
   - Sets amount: ₹1789
   - Narrates: "Proceeding with Raymond Shirt at ₹1789..."
    ↓
💳 Payment Agent (if online)
   - Processes payment
   - Status: Success
   - Payment ID: PAY789ABC12
   - Narrates: "Payment of ₹1789 received successfully..."
    ↓
📮 Fulfillment Agent
   - Creates order
   - Order ID: ORD789ABC
   - Status: Confirmed - preparing for dispatch
   - Narrates: "Order confirmed, will be shipped soon..."
    ↓
⭐ Loyalty Agent
   - Calculates points: 178 points (₹10 = 1 point)
   - Updates total: 178 points
   - Checks tier: Bronze
   - Available coupons: FIRST10
   - Narrates: "Congratulations! You earned 178 loyalty points..."
    ↓
🎁 Post Purchase Agent
   - Enables order tracking
   - Sets up support channels
   - Generates offers: FREESHIP, REFER500
   - Schedules feedback: 7 days
   - Narrates: "Thank you! You can track your order and we have special offers..."
    ↓
✅ Complete!
```

## Agent Timeline Output Example

```json
[
  {
    "agent": "recommendation_agent",
    "timestamp": "2026-01-25T11:53:19",
    "action": "Products recommended",
    "details": "Found 6 products"
  },
  {
    "agent": "inventory_agent",
    "timestamp": "2026-01-25T11:53:20",
    "action": "Inventory checked",
    "details": "Available via online channel"
  },
  {
    "agent": "sales_agent",
    "timestamp": "2026-01-25T11:53:25",
    "action": "Product selected",
    "details": "User selected product SKU205"
  },
  {
    "agent": "payment_agent",
    "timestamp": "2026-01-25T11:53:59",
    "action": "Payment processed",
    "details": "Payment success - Amount: ₹1879"
  },
  {
    "agent": "fulfillment_agent",
    "timestamp": "2026-01-25T11:54:00",
    "action": "Order confirmed",
    "details": "Order ORD789ABC - confirmed"
  },
  {
    "agent": "loyalty_agent",
    "timestamp": "2026-01-25T11:54:03",
    "action": "Loyalty rewards processed",
    "details": "Earned 120 points"
  },
  {
    "agent": "post_purchase_agent",
    "timestamp": "2026-01-25T11:54:05",
    "action": "Post-purchase services setup",
    "details": "Setup complete for order tracking and support"
  }
]
```

## Troubleshooting

### Issue: "GOOGLE_API_KEY not found"
**Solution**: Make sure you created `.env` file and added your API key:
```bash
GOOGLE_API_KEY=your_actual_key_here
```

### Issue: "Module not found"
**Solution**: Make sure you're in the virtual environment and installed dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution**: Use a different port:
```bash
uvicorn main:app --reload --port 8001
```

### Issue: "CSV file not found"
**Solution**: Make sure you're running from the `backend` directory where `data/` folder exists.

## Next Steps

1. ✅ Complete installation
2. ✅ Test with `test_langgraph_flow.py`
3. ✅ Run FastAPI server
4. ✅ Test API endpoints
5. 🚀 Integrate with frontend
6. 🎨 Customize agents for your use case

## Documentation

- [Full Documentation](./LANGGRAPH_README.md)
- [FastAPI Docs](http://localhost:8000/docs) (when server is running)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review the full documentation
3. Check environment variables in `.env`
4. Verify API key is valid
5. Ensure all dependencies are installed

Happy building! 🎉
