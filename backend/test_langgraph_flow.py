"""
Test script for LangGraph Agent Orchestration
Run this to test the agent workflow
"""

import asyncio
import os
from dotenv import load_dotenv
from langgraph_orchestrator import RetailAgentOrchestrator

# Load environment variables
load_dotenv()


async def test_agent_workflow():
    """Test the complete agent workflow"""
    
    print("=" * 80)
    print("Testing LangGraph Multi-Agent Retail Chatbot")
    print("=" * 80)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Please create a .env file with your OpenAI API key")
        print("Example: OPENAI_API_KEY=your_key_here")
        return
    
    print(f"✓ API Key found: {api_key[:10]}...")
    print()
    
    # Initialize orchestrator
    print("Initializing LangGraph Orchestrator...")
    try:
        orchestrator = RetailAgentOrchestrator(openai_api_key=api_key)
        print("✓ Orchestrator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        return
    
    print()
    print("-" * 80)
    print("TEST 1: Product Recommendation Flow")
    print("-" * 80)
    
    # Test query
    test_query = "I want to buy shirts for Christmas under 3000 rupees"
    customer_id = "CUST001"
    customer_name = "Raymond"
    
    print(f"Customer: {customer_name} ({customer_id})")
    print(f"Query: {test_query}")
    print()
    print("Running agent workflow...")
    print()
    
    try:
        # Run the workflow
        result = await orchestrator.arun(
            customer_id=customer_id,
            query=test_query,
            customer_name=customer_name
        )
        
        # Display timeline
        print("📋 AGENT TIMELINE:")
        print("-" * 80)
        for event in result.get("timeline", []):
            print(f"[{event.get('agent', 'unknown').upper()}]")
            print(f"  ⏰ {event.get('timestamp', 'N/A')}")
            print(f"  📝 {event.get('action', 'N/A')}")
            print(f"  ℹ️  {event.get('details', 'N/A')}")
            print()
        
        # Display messages
        print("💬 AGENT MESSAGES:")
        print("-" * 80)
        messages = [
            msg.content for msg in result.get("messages", [])
            if hasattr(msg, 'content')
        ]
        for i, msg in enumerate(messages, 1):
            print(f"{i}. {msg}")
            print()
        
        # Display results
        print("📦 RESULTS:")
        print("-" * 80)
        print(f"✓ Recommended Products: {len(result.get('recommended_products', []))} items")
        if result.get('recommended_products'):
            for i, product in enumerate(result['recommended_products'][:3], 1):
                print(f"  {i}. {product.get('product_name', 'N/A')} - ₹{product.get('price', 0)}")
        
        print(f"\n✓ Selected Product: {result.get('selected_product_id', 'None')}")
        print(f"✓ Channel: {result.get('channel', 'N/A')}")
        print(f"✓ Order ID: {result.get('order_id', 'N/A')}")
        print(f"✓ Payment Status: {result.get('payment_status', 'N/A')}")
        print(f"✓ Loyalty Points Earned: {result.get('loyalty_points_earned', 0)}")
        print(f"✓ Workflow Status: {'Completed' if result.get('completed') else 'Incomplete'}")
        
        print()
        print("=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_offline_flow():
    """Test offline purchase flow"""
    
    print("\n\n")
    print("=" * 80)
    print("TEST 2: Offline Purchase Flow")
    print("=" * 80)
    
    api_key = os.getenv("OPENAI_API_KEY")
    orchestrator = RetailAgentOrchestrator(openai_api_key=api_key)
    
    # Query for offline-only product
    test_query = "Looking for boots for winter"
    customer_id = "CUST002"
    
    print(f"Query: {test_query}")
    print()
    
    try:
        result = await orchestrator.arun(
            customer_id=customer_id,
            query=test_query
        )
        
        print(f"✓ Channel: {result.get('channel', 'N/A')}")
        print(f"✓ Available Stores: {len(result.get('available_stores', []))}")
        print(f"✓ Order ID: {result.get('order_id', 'N/A')}")
        print(f"✓ Payment Agent: {'Skipped (Offline)' if result.get('payment_status') is None else 'Executed'}")
        
        print()
        print("✅ Offline flow completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main test function"""
    # Run async tests
    asyncio.run(test_agent_workflow())
    
    # Uncomment to test offline flow
    # asyncio.run(test_offline_flow())


if __name__ == "__main__":
    main()
