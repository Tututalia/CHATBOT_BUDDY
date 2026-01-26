"""
Visual representation of the Intelligent Sales Agent Graph Flow
This script prints the graph structure without requiring full dependencies
"""


def print_agent_flow():
    """Print the complete agent graph structure and flow"""

    print("\n" + "="*70)
    print(" "*15 + "INTELLIGENT SALES AGENT SYSTEM")
    print(" "*20 + "Using LangGraph & OpenAI GPT-4 mini")
    print("="*70)

    print("\n📊 GRAPH STRUCTURE:")
    print("─" * 70)
    print("""
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
         ▼
    ┌────────────────────────────────────────────┐
    │         AGENT NODE (LLM Decision)          │
    │  • Analyzes user query & conversation      │
    │  • Decides which tools to call (if any)    │
    │  • Uses OpenAI GPT-4 mini                  │
    └────┬───────────────────────────────────┬───┘
         │                                   │
         │ (if tools needed)                 │ (if done)
         ▼                                   ▼
    ┌─────────────────────┐            ┌─────────┐
    │    TOOLS NODE       │            │   END   │
    │  Executes agent     │            └─────────┘
    │  tools as needed    │
    └──────────┬──────────┘
               │
               │ (returns results)
               │
               └──────┐
                      ▼
              (back to AGENT NODE to process results)
    """)

    print("\n" + "="*70)
    print(" "*20 + "🛠️  AVAILABLE AGENT TOOLS")
    print("="*70)

    tools_info = [
        {
            "name": "recommendation_agent",
            "purpose": "Shows product recommendations",
            "trigger": "User wants to browse/see products",
            "output": "List of recommended products with details",
            "example": "User: 'Show me hoodies' → Tool shows 3-5 hoodies"
        },
        {
            "name": "inventory_agent",
            "purpose": "Checks product availability",
            "trigger": "User selects a specific product",
            "output": "Availability status + Online/Offline options",
            "example": "User: 'I want PRD001' → Shows stock & purchase options"
        },
        {
            "name": "payment_agent",
            "purpose": "Processes online payment",
            "trigger": "User chooses online purchase",
            "output": "Payment confirmation + Order ID",
            "example": "User chooses online → Payment gateway → Order confirmed"
        },
        {
            "name": "fulfillment_agent",
            "purpose": "Handles order fulfillment",
            "trigger": "After payment OR offline selection",
            "output": "Delivery details (online) OR Kiosk message (offline)",
            "example": "Online: Delivery in 3-5 days | Offline: Visit kiosk"
        },
        {
            "name": "loyalty_agent",
            "purpose": "Awards loyalty points & coupons",
            "trigger": "After order fulfillment",
            "output": "Loyalty points earned + Coupon codes",
            "example": "Earned 150 points + SAVE20 coupon"
        },
        {
            "name": "post_purchase_agent",
            "purpose": "Post-purchase feedback & support",
            "trigger": "Final step after loyalty",
            "output": "Feedback link + Support contact info",
            "example": "Feedback link + Support email/phone"
        }
    ]

    for i, tool in enumerate(tools_info, 1):
        print(f"\n{i}. {tool['name'].upper()}")
        print(f"   ├─ Purpose: {tool['purpose']}")
        print(f"   ├─ Triggered when: {tool['trigger']}")
        print(f"   ├─ Output: {tool['output']}")
        print(f"   └─ Example: {tool['example']}")

    print("\n" + "="*70)
    print(" "*20 + "💡 HOW IT WORKS")
    print("="*70)

    workflow = [
        "1. User sends a query to the system",
        "2. LLM (GPT-4 mini) analyzes the query and conversation context",
        "3. LLM intelligently decides which agent tools to call",
        "4. Selected tools execute and return results",
        "5. LLM processes tool results and formulates a response",
        "6. LLM sends response back to user",
        "7. Process repeats based on user's next query",
        "8. Conversation continues until user is satisfied"
    ]

    for step in workflow:
        print(f"\n   {step}")

    print("\n" + "="*70)
    print(" "*20 + "📋 EXAMPLE CONVERSATION FLOW")
    print("="*70)

    conversation_example = """
    USER: "Hi! I'm looking for a winter hoodie"
         ↓
    LLM: Calls → recommendation_agent(query="winter hoodie")
         ↓
    TOOL: Returns 3 hoodies with details
         ↓
    LLM: "Here are some great winter hoodies for you: ..."
    
    ─────────────────────────────────────────────────────────
    
    USER: "I like the Being Human Hoodie PRD001"
         ↓
    LLM: Calls → inventory_agent(product_id="PRD001")
         ↓
    TOOL: Returns availability + online/offline options
         ↓
    LLM: "Great choice! It's available. Would you like to buy online or offline?"
    
    ─────────────────────────────────────────────────────────
    
    USER: "I'll buy it online"
         ↓
    LLM: Calls → payment_agent(product_id="PRD001", payment_details="online")
         ↓
    TOOL: Returns payment confirmation + order ID
         ↓
    LLM: "Payment successful! Your order ID is ORD12345"
         ↓
    LLM: Calls → fulfillment_agent(order_id="ORD12345", channel="online")
         ↓
    TOOL: Returns delivery details
         ↓
    LLM: "Your order will be delivered in 3-5 days"
         ↓
    LLM: Calls → loyalty_agent(customer_id="CUST001", order_id="ORD12345")
         ↓
    TOOL: Returns loyalty points + coupons
         ↓
    LLM: "You earned 150 points and a SAVE20 coupon!"
         ↓
    LLM: Calls → post_purchase_agent(order_id="ORD12345")
         ↓
    TOOL: Returns feedback link
         ↓
    LLM: "Thanks for shopping! Please share your feedback: [link]"
    """

    print(conversation_example)

    print("\n" + "="*70)
    print(" "*20 + "⚡ KEY FEATURES")
    print("="*70)

    features = [
        "✓ Non-linear flow: LLM decides tool calls dynamically",
        "✓ Intelligent routing: Tools called only when needed",
        "✓ Context-aware: LLM remembers entire conversation",
        "✓ Flexible: Can handle various user queries and flows",
        "✓ Natural: Conversation feels human-like, not scripted",
        "✓ Efficient: Only necessary agents are triggered"
    ]

    for feature in features:
        print(f"\n   {feature}")

    print("\n" + "="*70)
    print(" "*20 + "🔧 TECHNICAL DETAILS")
    print("="*70)

    print("\n   • Framework: LangGraph (StateGraph)")
    print("   • LLM: OpenAI GPT-4 mini")
    print("   • Architecture: Agent + Tools pattern")
    print("   • State Management: TypedDict with message history")
    print("   • Tool Binding: LLM.bind_tools()")
    print("   • Conditional Edges: tools_condition for smart routing")
    print("   • Execution: Async/Await for better performance")

    print("\n" + "="*70)
    print(" "*15 + "✅ GRAPH SUCCESSFULLY DEFINED")
    print("="*70 + "\n")


if __name__ == "__main__":
    print_agent_flow()
