"""
Simple test for LangGraph Agent Orchestration
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

async def test_workflow():
    """Test the complete agent workflow"""
    
    print("="*80)
    print("Testing LangGraph Multi-Agent Retail Chatbot")
    print("="*80)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in .env file")
        return
    
    print(f"[OK] API Key found: {api_key[:15]}...")
    print()
    
    # Import orchestrator
    try:
        from langgraph_orchestrator import RetailAgentOrchestrator
        orchestrator = RetailAgentOrchestrator(openai_api_key=api_key)
        print("[OK] Orchestrator initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("-"*80)
    print("TEST: Product Recommendation Flow")
    print("-"*80)
    
    # Test query
    query = "I want to buy shirts for Christmas under 3000 rupees"
    customer_id = "CUST001"
    customer_name = "Raymond"
    
    print(f"\nCustomer: {customer_name}")
    print(f"Query: {query}")
    print()
    
    # Run workflow
    try:
        print("Running agent workflow...")
        result = await orchestrator.arun(
            customer_id=customer_id,
            query=query,
            customer_name=customer_name
        )
        
        print("\n" + "="*80)
        print("RESULTS:")
        print("="*80)
        
        # Timeline
        timeline = result.get("timeline", [])
        print(f"\n[TIMELINE] {len(timeline)} agent actions:")
        for event in timeline:
            print(f"  {event['timestamp']} - {event['agent']}: {event['action']}")
        
        # Products
        products = result.get("recommended_products", [])
        print(f"\n[PRODUCTS] Found {len(products)} recommendations:")
        for product in products:
            # Handle both dictionary and different key formats
            name = product.get('product_name') or product.get('name', 'Unknown')
            price = product.get('price', 0)
            category = product.get('category', 'N/A')
            print(f"  - {name} - Rs.{price} ({category})")
        
        # Order
        if result.get("order_id"):
            print(f"\n[ORDER] Created:")
            print(f"  Order ID: {result['order_id']}")
            print(f"  Total: Rs.{result.get('amount', 0)}")
            print(f"  Channel: {result.get('channel', 'N/A')}")
            print(f"  Status: {result.get('payment_status', 'N/A')}")
        
        # Loyalty
        if result.get("loyalty_points"):
            print(f"\n[LOYALTY] Rewards:")
            print(f"  Points: {result['loyalty_points']}")
            print(f"  Coupons: {', '.join(result.get('coupons_earned', []))}")
        
        # Status
        status = "COMPLETE" if result.get("order_id") else "INCOMPLETE"
        print(f"\n[STATUS] Workflow: {status}")
        
        print("\n" + "="*80)
        print("Test completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_workflow())
