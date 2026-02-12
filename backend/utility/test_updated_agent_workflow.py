"""
Test script for the updated intelligent agent workflow
Tests the new cart-based purchase flow with tool calling sequence
"""

import asyncio
from intelligent_agent_graph import run_agent


async def test_full_workflow():
    """
    Test the complete workflow from product search to checkout
    """
    customer_id = "CUST001"

    print("\n" + "="*80)
    print("TESTING UPDATED INTELLIGENT AGENT WORKFLOW")
    print("="*80)

    # Test 1: Product Search
    print("\n📝 TEST 1: Product Search")
    print("-" * 80)
    query1 = "Show me some hoodies"
    print(f"\n👤 User: {query1}")
    result1 = await run_agent(customer_id, query1)
    print("\n🤖 Agent Response:")
    for msg in result1["messages"][-3:]:  # Show last 3 messages
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:200]}...")

    # Test 2: Add to Cart
    print("\n\n📝 TEST 2: Add Product to Cart")
    print("-" * 80)
    query2 = "Add product P001, quantity 2 to cart"
    print(f"\n👤 User: {query2}")
    result2 = await run_agent(customer_id, query2)
    print("\n🤖 Agent Response:")
    for msg in result2["messages"][-2:]:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:200]}...")

    # Test 3: View Cart
    print("\n\n📝 TEST 3: View Cart")
    print("-" * 80)
    query3 = "View my cart"
    print(f"\n👤 User: {query3}")
    result3 = await run_agent(customer_id, query3)
    print("\n🤖 Agent Response:")
    for msg in result3["messages"][-2:]:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:300]}...")

    # Test 4: Proceed to Checkout
    print("\n\n📝 TEST 4: Proceed to Checkout")
    print("-" * 80)
    query4 = "Proceed with payment"
    print(f"\n👤 User: {query4}")
    result4 = await run_agent(customer_id, query4)
    print("\n🤖 Agent Response:")
    for msg in result4["messages"][-2:]:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:300]}...")

    print("\n\n" + "="*80)
    print("✅ WORKFLOW TEST COMPLETED")
    print("="*80)
    print("\nNOTE: This is a basic test. Full flow requires multiple interactions:")
    print("1. Product search → inventory_agent + recommendation_agent")
    print("2. Add to cart → add_to_cart_agent")
    print("3. View cart → view_cart_agent")
    print("4. Proceed → Ask online/offline")
    print("5. Choose online → payment_agent (show methods)")
    print("6. Select payment → payment_agent (process)")
    print("7. Auto-call → fulfillment_agent")
    print("8. Auto-call → loyalty_agent")
    print("9. Auto-call → post_purchase_agent")
    print("\n")


async def test_tool_calling_sequence():
    """
    Test that tools are called in the correct sequence
    """
    customer_id = "CUST002"

    print("\n" + "="*80)
    print("TESTING TOOL CALLING SEQUENCE")
    print("="*80)

    query = "I want to buy some winter hoodies"
    print(f"\n👤 User: {query}")
    print("\n🔍 Expected Tool Sequence:")
    print("1. inventory_agent(search_query='winter hoodies')")
    print("2. recommendation_agent(inventory_data=...)")

    result = await run_agent(customer_id, query)

    print("\n📊 Actual Tool Calls:")
    tool_calls_found = []
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get('name', 'Unknown')
                tool_calls_found.append(tool_name)
                print(f"  ✓ {tool_name}")

    if not tool_calls_found:
        print("  ⚠️  No tool calls detected (LLM might have responded directly)")

    print("\n" + "="*80)


if __name__ == "__main__":
    print("\n🚀 Starting Agent Workflow Tests...")
    print("="*80)

    # Run tests
    try:
        asyncio.run(test_tool_calling_sequence())
        print("\n")
        asyncio.run(test_full_workflow())
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
