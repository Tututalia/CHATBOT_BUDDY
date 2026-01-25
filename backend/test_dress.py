"""
Test the enhanced recommendation agent with dress purchase
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_orchestrator import RetailAgentOrchestrator

async def test_dress_purchase():
    """Test customer buying a dress"""
    
    # Initialize orchestrator
    orchestrator = RetailAgentOrchestrator()
    
    # Test query
    query = "I want to buy a dress for a wedding"
    customer_id = "CUST002"  # Priya Sen, Female customer
    
    print(f"[TEST] Query: {query}")
    print(f"[TEST] Customer: {customer_id} (Priya Sen)")
    print("="*50)
    
    # Run the orchestrator
    result = await orchestrator.arun(
        customer_id=customer_id,
        query=query,
        customer_name="Priya Sen"
    )
    
    # Display results
    print("\n[PRODUCTS] Recommended:")
    for i, product in enumerate(result.get("recommended_products", []), 1):
        marker = ">>> SELECTED" if product["product_id"] == result.get("selected_product_id") else ""
        print(f"  {i}. {product['product_name']} - Rs.{product['price']} ({product['category']}) {marker}")
    
    print(f"\n[SELECTION] LLM selected: {result.get('selected_product_id')}")
    
    print(f"\n[ORDER] Created:")
    print(f"  Order ID: {result.get('order_id', 'N/A')}")
    print(f"  Total: Rs.{result.get('amount', 0)}")
    print(f"  Channel: {result.get('channel', 'N/A')}")
    
    print(f"\n[LOYALTY] Points earned: {result.get('loyalty_points', 0)}")
    
    print(f"\n[STATUS] Workflow: {'COMPLETE' if result.get('order_id') else 'INCOMPLETE'}")
    
    # Show timeline
    print(f"\n[TIMELINE] Agent execution:")
    for step in result.get("timeline", []):
        print(f"  - {step}")

if __name__ == "__main__":
    asyncio.run(test_dress_purchase())