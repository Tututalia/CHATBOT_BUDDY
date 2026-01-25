"""
Frontend Integration Example for LangGraph Agent System
This shows how to integrate the React frontend with the LangGraph backend
"""

# Example React Component Structure for Integration

"""
// App.jsx or ChatInterface.jsx

import React, { useState, useEffect, useRef } from 'react';

const ChatWithAgents = () => {
  const [messages, setMessages] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef(null);

  // Option 1: REST API Integration
  const sendQueryREST = async (query) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: 'CUST001', // Get from auth context
          query: query,
          customer_name: 'Raymond' // Get from auth context
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update UI with response
        setMessages(data.messages);
        setTimeline(data.timeline);
        
        // Display results
        console.log('Recommended Products:', data.recommended_products);
        console.log('Order ID:', data.order_id);
        console.log('Loyalty Points:', data.loyalty_points_earned);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Option 2: WebSocket Integration (Real-time)
  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/chat/CUST001');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'ack':
          console.log('Processing:', data.message);
          break;
          
        case 'timeline':
          // Update timeline in real-time
          setTimeline(prev => [...prev, data.data]);
          break;
          
        case 'response':
          // Final response received
          setMessages(data.data.messages);
          console.log('Complete response:', data.data);
          break;
          
        case 'error':
          console.error('Error:', data.message);
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    wsRef.current = ws;
  };

  const sendQueryWebSocket = (query) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        query: query,
        customer_name: 'Raymond'
      }));
    }
  };

  useEffect(() => {
    // Connect WebSocket on mount
    connectWebSocket();
    
    // Cleanup on unmount
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return (
    <div className="chat-container">
      {/* Agent Timeline Panel (Left Side) */}
      <div className="timeline-panel">
        <h3>🤖 Agent Timeline</h3>
        <div className="timeline-events">
          {timeline.map((event, idx) => (
            <div key={idx} className="timeline-event">
              <div className="agent-badge">{event.agent}</div>
              <div className="event-time">{event.timestamp}</div>
              <div className="event-action">{event.action}</div>
              <div className="event-details">{event.details}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Panel (Main) */}
      <div className="chat-panel">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className="message">
              {msg}
            </div>
          ))}
        </div>
        
        <div className="input-area">
          <input
            type="text"
            value={currentQuery}
            onChange={(e) => setCurrentQuery(e.target.value)}
            placeholder="Type your message..."
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                sendQueryWebSocket(currentQuery);
                setCurrentQuery('');
              }
            }}
          />
          <button 
            onClick={() => {
              sendQueryWebSocket(currentQuery);
              setCurrentQuery('');
            }}
            disabled={isLoading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWithAgents;
"""

# CSS Styling Example for Timeline
"""
/* styles.css */

.chat-container {
  display: flex;
  height: 100vh;
}

.timeline-panel {
  width: 30%;
  background: #f5f5f5;
  padding: 20px;
  overflow-y: auto;
  border-right: 1px solid #ddd;
}

.timeline-event {
  background: white;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 8px;
  border-left: 4px solid #ff6b35;
}

.agent-badge {
  display: inline-block;
  background: #ff6b35;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 8px;
}

.event-time {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}

.event-action {
  font-weight: bold;
  margin-bottom: 4px;
}

.event-details {
  font-size: 14px;
  color: #666;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.message {
  background: #e3f2fd;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 10px;
  max-width: 80%;
}

.input-area {
  display: flex;
  padding: 20px;
  border-top: 1px solid #ddd;
}

.input-area input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
}

.input-area button {
  padding: 12px 24px;
  background: #ff6b35;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
"""

print(__doc__)
print("\n" + "="*80)
print("Frontend Integration Guide")
print("="*80 + "\n")

print("INTEGRATION OPTIONS:")
print("-" * 80)
print()
print("1. REST API (Simple)")
print("   - Single request/response")
print("   - Use fetch() or axios")
print("   - Endpoint: POST /api/chat")
print()
print("2. WebSocket (Real-time)")
print("   - Streaming timeline updates")
print("   - Live agent execution visibility")
print("   - Endpoint: ws://localhost:8000/ws/chat/{customer_id}")
print()
print("="*80 + "\n")

print("RESPONSE DATA STRUCTURE:")
print("-" * 80)
print("""
{
  "success": true,
  "customer_id": "CUST001",
  "query": "I want shirts",
  "timeline": [
    {
      "agent": "recommendation_agent",
      "timestamp": "2026-01-25T11:53:19",
      "action": "Products recommended",
      "details": "Found 6 products"
    }
  ],
  "recommended_products": [
    {
      "product_id": "SKU205",
      "product_name": "Raymond Shirt",
      "price": 1789,
      "category": "Shirt"
    }
  ],
  "selected_product": {...},
  "inventory_info": {...},
  "channel": "online",
  "payment_status": "success",
  "order_id": "ORD789ABC",
  "loyalty_points_earned": 178,
  "messages": [
    "I found 6 great shirts for you...",
    "The Raymond Shirt is available online...",
    "Payment received successfully..."
  ]
}
""")
print()
print("="*80 + "\n")

print("UI COMPONENTS TO BUILD:")
print("-" * 80)
print()
print("1. Timeline Panel (Left)")
print("   - Shows live agent execution")
print("   - Updates in real-time with WebSocket")
print("   - Color-coded by agent type")
print()
print("2. Chat Panel (Main)")
print("   - Displays agent messages")
print("   - User input area")
print("   - Product recommendations")
print()
print("3. Product Display")
print("   - Grid/list of recommended products")
print("   - Click to select")
print("   - Price, image, availability")
print()
print("4. Loyalty Panel (Right)")
print("   - Current points")
print("   - Points earned")
print("   - Available coupons")
print()
print("="*80 + "\n")

print("EXAMPLE TIMELINE RENDERING:")
print("-" * 80)
print("""
const AgentTimeline = ({ timeline }) => {
  const agentColors = {
    'recommendation_agent': '#4CAF50',
    'inventory_agent': '#2196F3',
    'sales_agent': '#FF9800',
    'payment_agent': '#9C27B0',
    'fulfillment_agent': '#FF5722',
    'loyalty_agent': '#E91E63',
    'post_purchase_agent': '#607D8B'
  };
  
  return (
    <div className="timeline">
      {timeline.map((event, idx) => (
        <div 
          key={idx} 
          className="timeline-item"
          style={{ borderLeftColor: agentColors[event.agent] }}
        >
          <div className="agent-name">
            {event.agent.replace('_', ' ').toUpperCase()}
          </div>
          <div className="timestamp">
            {new Date(event.timestamp).toLocaleTimeString()}
          </div>
          <div className="action">{event.action}</div>
          <div className="details">{event.details}</div>
        </div>
      ))}
    </div>
  );
};
""")
print()
print("="*80)
