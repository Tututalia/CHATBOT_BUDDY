"""
LangGraph Flow Visualizer - Shows the agent workflow structure
"""

def print_langgraph_flow():
    """Print the complete LangGraph workflow structure"""
    
    print("🔄 LANGGRAPH MULTI-AGENT RETAIL WORKFLOW")
    print("=" * 60)
    
    print("\n📊 WORKFLOW ARCHITECTURE:")
    print("""
    START
      ↓
    ┌─────────────────────┐
    │ RECOMMENDATION      │ ← Extract intent via LLM
    │ AGENT               │   Search products via pandas
    │                     │   LLM selects best match
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ INVENTORY           │ ← Check product availability
    │ AGENT               │   Determine online/offline channel
    │                     │   Get store information
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ SALES               │ ← Confirm product selection
    │ AGENT               │   Generate sales narrative
    │                     │   Prepare for transaction
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ CONDITIONAL         │ ← Route based on channel:
    │ ROUTING             │   • Online  → Payment Agent
    │                     │   • Offline → Fulfillment Agent
    └─────────────────────┘
         ↓         ↓
    [ONLINE]   [OFFLINE]
         ↓         ↓
    ┌─────────────────────┐         ↓
    │ PAYMENT             │         ↓
    │ AGENT               │ ← Process online payment
    │                     │   Generate payment ID
    └─────────────────────┘         ↓
              ↓                     ↓
              ↓ ←-------------------┘
    ┌─────────────────────┐
    │ FULFILLMENT         │ ← Create order ID
    │ AGENT               │   Confirm fulfillment
    │                     │   Setup delivery/pickup
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ LOYALTY             │ ← Calculate loyalty points
    │ AGENT               │   Generate loyalty coupons
    │                     │   Update customer profile
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ POST-PURCHASE       │ ← Setup order tracking
    │ AGENT               │   Provide customer support
    │                     │   Generate follow-up offers
    └─────────────────────┘
              ↓
            END
    """)
    
    print("\n🧠 AGENT RESPONSIBILITIES:")
    print("-" * 40)
    
    agents = [
        {
            "name": "RECOMMENDATION AGENT",
            "icon": "🔍",
            "responsibilities": [
                "Extract user intent using OpenAI GPT-4o-mini",
                "Parse category, price, gender, occasion from query",
                "Search products using deterministic pandas tools",
                "LLM analyzes and selects best matching product",
                "Handle plural/singular category normalization"
            ]
        },
        {
            "name": "INVENTORY AGENT", 
            "icon": "📦",
            "responsibilities": [
                "Check product availability in inventory",
                "Determine online vs offline availability",
                "Get list of stores with product in stock",
                "Set preferred channel (online/offline)"
            ]
        },
        {
            "name": "SALES AGENT",
            "icon": "💼", 
            "responsibilities": [
                "Confirm user's product selection",
                "Generate sales conversation narrative",
                "Prepare product details for transaction",
                "Handle any sales-related questions"
            ]
        },
        {
            "name": "PAYMENT AGENT",
            "icon": "💳",
            "responsibilities": [
                "Process online payments (online channel only)",
                "Generate payment confirmation ID", 
                "Calculate total amount including taxes",
                "Handle payment success/failure scenarios"
            ]
        },
        {
            "name": "FULFILLMENT AGENT",
            "icon": "🚚",
            "responsibilities": [
                "Generate unique order ID",
                "Confirm order fulfillment status",
                "Setup delivery (online) or pickup (offline)",
                "Provide order tracking information"
            ]
        },
        {
            "name": "LOYALTY AGENT",
            "icon": "⭐",
            "responsibilities": [
                "Calculate loyalty points earned",
                "Generate loyalty coupons and offers", 
                "Update customer loyalty profile",
                "Provide tier upgrade notifications"
            ]
        },
        {
            "name": "POST-PURCHASE AGENT",
            "icon": "📞",
            "responsibilities": [
                "Setup order tracking and notifications",
                "Provide customer support contact info",
                "Generate follow-up purchase offers",
                "Complete the transaction workflow"
            ]
        }
    ]
    
    for agent in agents:
        print(f"\n{agent['icon']} {agent['name']}")
        for resp in agent['responsibilities']:
            print(f"   • {resp}")
    
    print("\n🔀 ROUTING LOGIC:")
    print("-" * 20)
    print("After Sales Agent:")
    print("  • If channel = 'online'  → Payment Agent → Fulfillment Agent")
    print("  • If channel = 'offline' → Fulfillment Agent (skip payment)")
    print("  • If channel = None      → END (error case)")
    
    print("\n📊 STATE MANAGEMENT:")
    print("-" * 20)
    print("Shared state between agents includes:")
    print("  • messages: Conversation history")
    print("  • customer_id: Customer identifier") 
    print("  • query: Original user request")
    print("  • recommended_products: List of product matches")
    print("  • selected_product_id: Chosen product")
    print("  • channel: online/offline")
    print("  • payment_status: success/failure")
    print("  • order_id: Generated order identifier")
    print("  • loyalty_points_earned: Points calculation")
    print("  • timeline: Agent execution history")
    
    print("\n🎯 KEY FEATURES:")
    print("-" * 15)
    print("  ✅ LLM-powered intent extraction")
    print("  ✅ Deterministic product search via pandas")
    print("  ✅ Smart product selection by LLM analysis")
    print("  ✅ Conditional routing (online vs offline)")
    print("  ✅ Complete transaction lifecycle")
    print("  ✅ Real-time timeline tracking")
    print("  ✅ Error handling and fallbacks")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_langgraph_flow()