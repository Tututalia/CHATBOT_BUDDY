# AI Chatbot Integration Guide

## Overview
This document describes the integration of the intelligent AI chatbot powered by LangGraph and OpenAI into the ABFRL Agentic Dashboard.

## Architecture

### Backend (FastAPI)
- **File**: `backend/main.py`
- **Endpoint**: `POST /api/chat`
- **AI Engine**: `intelligent_agent_graph.py` (LangGraph + OpenAI GPT-4 mini)

The chatbot uses an intelligent multi-agent system where:
1. User sends a query
2. OpenAI LLM analyzes the query and conversation history
3. LLM intelligently decides which agent tools to call:
   - `recommendation_agent` - Shows product recommendations
   - `inventory_agent` - Checks product availability
   - `payment_agent` - Processes online payments
   - `fulfillment_agent` - Handles order delivery/pickup
   - `loyalty_agent` - Awards loyalty points
   - `post_purchase_agent` - Sends feedback and support info
4. Tools execute and return results
5. LLM processes results and responds naturally to user

### Frontend (React)
- **Component**: `frontend/src/components/ChatBot.jsx`
- **Styling**: `frontend/src/components/ChatBot.css`
- **Integration**: Added to `frontend/pages.jsx`

## Features

### Chatbot UI
- **Floating Icon**: Bottom-right corner of all pages with pulse animation
- **Dark Theme**: Matches the dashboard's aesthetic
- **Two-Panel Layout**:
  - **Left Panel (Agent Timeline)**: Shows live log of agent activities
  - **Right Panel (Chat Interface)**: Conversational interface with message history

### Chat Interface Features
- Real-time AI responses using OpenAI
- Message history with timestamps
- Typing indicators during AI processing
- Status badge showing "Active" or "In Progress"
- Clear chat functionality
- Expandable/collapsible chatbot window
- Responsive design for mobile devices

### Agent Timeline
- Live tracking of agent tool calls
- Displays which agents are being invoked
- Shows execution timestamps
- Visual timeline with connecting dots

## Setup Instructions

### 1. Backend Setup

Ensure you have the required dependencies:
```bash
cd backend
pip install -r requirements.txt
```

Make sure you have set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Start the backend server:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

Install dependencies:
```bash
cd frontend
npm install
```

Start the development server:
```bash
npm run dev
```

### 3. Test the Chatbot

1. Open the application in your browser (usually `http://localhost:5173`)
2. Click the chatbot icon in the bottom-right corner
3. Try sample queries:
   - "Show me some hoodies"
   - "I want to buy product P001"
   - "Buy online"
   - "What's the status of my order?"

## API Reference

### POST /api/chat

**Request Body:**
```json
{
  "customer_id": "CUST001",
  "message": "Show me some hoodies",
  "conversation_history": [
    {
      "role": "user",
      "content": "previous message"
    },
    {
      "role": "assistant",
      "content": "previous response"
    }
  ]
}
```

**Response:**
```json
{
  "response": "🛍️ **Product Recommendations:**\n\n1. Hoodie X - ₹1,299...",
  "agent_calls": ["recommendation_agent", "inventory_agent"]
}
```

## How It Works

### User Flow
1. User clicks chatbot icon → Chatbot window opens
2. User types a query → Message sent to backend
3. Backend processes with LangGraph → LLM decides which agents to call
4. Agents execute (recommendation, inventory, payment, etc.)
5. AI response displayed → Agent timeline updated

### Example Conversation Flow

**User**: "Show me some hoodies"
- **Agent Called**: `recommendation_agent`
- **Response**: Product recommendations with prices

**User**: "I want product P001"
- **Agent Called**: `inventory_agent`
- **Response**: Availability status, online/offline options

**User**: "Buy online"
- **Agents Called**: `payment_agent` → `fulfillment_agent` → `loyalty_agent` → `post_purchase_agent`
- **Response**: Payment processed, delivery scheduled, loyalty points awarded

## Customization

### Change Customer ID
The chatbot uses the logged-in customer ID automatically. For guest users, it uses "GUEST".

```jsx
<ChatBot customerId={isLoggedIn || "GUEST"} />
```

### Modify Styling
Edit `ChatBot.css` to change colors, sizes, or layout:
- Window size: `.chatbot-window { width: 900px; height: 600px; }`
- Colors: Change gradient colors in `.chatbot-icon` and `.send-btn`
- Theme: Modify background colors for light/dark themes

### Add More Agents
To add new agent tools:
1. Define the tool in `intelligent_agent_graph.py`
2. Add to `tools` list
3. LLM will automatically use it when appropriate

## Troubleshooting

### Chatbot not appearing
- Check that `ChatBot` component is imported and rendered in `pages.jsx`
- Verify CSS file is imported correctly

### No AI responses
- Check backend is running on port 8000
- Verify OpenAI API key is set
- Check browser console for CORS errors

### CORS errors
- Backend already configured for localhost:5173
- If using different port, update `allow_origins` in `main.py`

## Technologies Used
- **Backend**: FastAPI, LangGraph, LangChain, OpenAI GPT-4 mini
- **Frontend**: React, CSS3 (animations and gradients)
- **AI**: Multi-agent orchestration with intelligent tool calling

## Future Enhancements
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Product image display in chat
- [ ] Chat history persistence
- [ ] User feedback on responses
- [ ] Analytics dashboard for chat interactions
