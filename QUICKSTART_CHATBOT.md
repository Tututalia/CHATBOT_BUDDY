# 🚀 Quick Start Guide - AI Chatbot Integration

## Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API Key

## Step 1: Set OpenAI API Key

### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your-openai-api-key-here"
```

### Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=your-openai-api-key-here
```

### Linux/Mac:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## Step 2: Start Backend Server

```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Step 3: Test Backend (Optional)

In a new terminal:
```powershell
cd backend
python test_chatbot_integration.py
```

This will test the AI agent with sample queries.

## Step 4: Start Frontend

In a new terminal:
```powershell
cd frontend
npm install  # First time only
npm run dev
```

**Expected Output:**
```
VITE v4.x.x  ready in xxx ms
Local: http://localhost:5173/
```

## Step 5: Test the Chatbot

1. Open browser: `http://localhost:5173`
2. Look for the **chatbot icon** (🤖) in the **bottom-right corner**
3. Click the icon to open the chatbot
4. Try these queries:
   - "Show me some hoodies"
   - "I want to buy product P001"
   - "What products do you have?"

## Expected Behavior

### Chatbot Opens ✅
- Dark themed window appears
- Left panel shows "Agent Timeline"
- Right panel shows chat interface
- Welcome message from AI

### Send Message ✅
1. Type query in input box
2. Click "Search" button
3. User message appears on right
4. AI response appears on left
5. Agent timeline updates showing which agents were called

## Troubleshooting

### Issue: "Module not found" error in backend
**Solution:**
```powershell
cd backend
pip install -r requirements.txt
```

### Issue: Chatbot icon not visible
**Solution:**
- Check browser console (F12) for errors
- Verify frontend is running on port 5173
- Clear browser cache (Ctrl+Shift+R)

### Issue: No AI responses
**Solution:**
- Check OpenAI API key is set correctly
- Verify backend is running on port 8000
- Check backend terminal for error messages

### Issue: CORS error in browser console
**Solution:**
- Make sure backend is running on port 8000
- Frontend should be on port 5173
- If using different ports, update `allow_origins` in `backend/main.py`

## API Endpoints

Once backend is running, you can test the API:

### Health Check
```bash
curl http://localhost:8000/
```

### Chat API (POST)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "message": "Show me some hoodies",
    "conversation_history": []
  }'
```

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐
│                 │         │                  │
│  Frontend       │◄────────┤  Backend         │
│  (React)        │         │  (FastAPI)       │
│                 │         │                  │
│  - ChatBot.jsx  │         │  - main.py       │
│  - ChatBot.css  │         │  - /api/chat     │
│                 │         │                  │
└─────────────────┘         └────────┬─────────┘
                                     │
                            ┌────────▼─────────┐
                            │                  │
                            │  LangGraph +     │
                            │  OpenAI          │
                            │                  │
                            │  intelligent_    │
                            │  agent_graph.py  │
                            │                  │
                            └──────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
            │              │ │             │ │             │
            │ Recommend    │ │ Inventory   │ │ Payment     │
            │ Agent        │ │ Agent       │ │ Agent       │
            │              │ │             │ │             │
            └──────────────┘ └─────────────┘ └─────────────┘
```

## Next Steps

1. **Customize Styling**: Edit `frontend/src/components/ChatBot.css`
2. **Add More Agents**: Modify `backend/intelligent_agent_graph.py`
3. **Enhance UI**: Update `frontend/src/components/ChatBot.jsx`
4. **Deploy**: Follow deployment guide in main README

## Sample Conversation

```
👤 User: Show me some hoodies

🤖 AI: 🛍️ **Product Recommendations:**

1. Classic Cotton Hoodie - ₹1,299
   - Size: S, M, L, XL
   - Colors: Black, Navy, Grey

2. Premium Fleece Hoodie - ₹1,899
   - Size: S, M, L, XL
   - Colors: Charcoal, Olive

Would you like to select any product?

👤 User: I want product P001

🤖 AI: ✅ **Product P001 is IN STOCK!**

**Classic Cotton Hoodie** - ₹1,299

📦 **Purchase Options:**

🌐 **Online Purchase:**
   - Home delivery available
   - Free shipping on orders above ₹999

How would you like to proceed?
- Type 'online' to buy online with home delivery
```

## Support

For issues or questions:
1. Check `CHATBOT_INTEGRATION.md` for detailed documentation
2. Review backend logs in terminal
3. Check browser console (F12) for frontend errors
4. Verify OpenAI API key and credits

---

**Ready to go! 🎉** Open `http://localhost:5173` and start chatting with the AI!
