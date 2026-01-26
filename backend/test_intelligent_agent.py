"""
Test script for the Intelligent Agent Graph System
Run this to test the agent with sample queries
"""

import asyncio
import os
from intelligent_agent_graph import create_agent_graph, visualize_graph
from langchain_core.messages import HumanMessage


async def test_agent_conversation():
    """Test the intelligent agent with sample conversations"""

    # Set OpenAI API key (make sure to set this in your environment)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set in environment")
        print("Set it using: export OPENAI_API_KEY='your-key-here'")
        print("Or: os.environ['OPENAI_API_KEY'] = 'your-key-here'")
        return

    print("\n" + "="*70)
    print(" "*20 + "🤖 TESTING INTELLIGENT AGENT")
    print("="*70)

    # Create the graph
    graph = create_agent_graph()

    # Test scenarios
    test_queries = [
        {
            "customer_id": "CUST001",
            "query": "Hi! I'm looking for a winter hoodie. Can you show me some options?",
            "description": "Product Browsing"
        },
        {
            "customer_id": "CUST002",
            "query": "I want to buy the Being Human Hoodie. Is it available?",
            "description": "Product Selection & Inventory Check"
        },
        {
            "customer_id": "CUST003",
            "query": "I'll buy it online with my credit card",
            "description": "Online Purchase Flow"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {test['description']}")
        print(f"{'='*70}")
        print(f"\n👤 User Query: {test['query']}")
        print("\n⏳ Processing...\n")

        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=test["query"])],
            "customer_id": test["customer_id"],
            "selected_product": None,
            "inventory_status": None,
            "purchase_channel": None,
            "order_id": None,
            "payment_completed": False,
            "loyalty_points": 0
        }

        try:
            # Run the graph
            result = await graph.ainvoke(initial_state)

            # Print conversation
            print("📝 Conversation Flow:")
            print("-" * 70)

            for msg in result["messages"]:
                msg_type = type(msg).__name__

                if "Human" in msg_type:
                    print(f"\n👤 USER: {msg.content}")
                elif "AI" in msg_type:
                    if msg.content:
                        print(f"\n🤖 AGENT: {msg.content}")
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        print(f"\n🔧 TOOLS CALLED:")
                        for tool_call in msg.tool_calls:
                            print(f"   → {tool_call['name']}")
                elif "Tool" in msg_type:
                    print(f"\n📦 TOOL RESPONSE:")
                    # Print first 200 chars of tool response
                    content_preview = str(msg.content)[:200]
                    print(f"   {content_preview}...")

            print("\n" + "-" * 70)
            print(f"✅ Test {i} completed successfully!")

        except Exception as e:
            print(f"\n❌ Error in Test {i}: {str(e)}")

        print("\n" + "="*70)

    print("\n✅ All tests completed!\n")


async def test_single_query(query: str, customer_id: str = "CUST001"):
    """Test a single query"""

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY environment variable first")
        return

    graph = create_agent_graph()

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "customer_id": customer_id,
        "selected_product": None,
        "inventory_status": None,
        "purchase_channel": None,
        "order_id": None,
        "payment_completed": False,
        "loyalty_points": 0
    }

    print(f"\n{'='*70}")
    print(f"🤖 Processing Query: {query}")
    print(f"{'='*70}\n")

    result = await graph.ainvoke(initial_state)

    # Print last AI message (final response)
    for msg in reversed(result["messages"]):
        if "AI" in type(msg).__name__ and msg.content:
            print(f"🤖 AGENT: {msg.content}\n")
            break

    return result


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*15 + "INTELLIGENT AGENT GRAPH - TEST SUITE")
    print("="*70)

    # First, visualize the graph
    print("\n📊 STEP 1: Visualizing Graph Structure\n")
    visualize_graph()

    # Then run tests
    print("\n🧪 STEP 2: Running Agent Tests\n")
    print("To run agent tests, uncomment the line below and ensure OPENAI_API_KEY is set:\n")
    print("   asyncio.run(test_agent_conversation())")
    print("\nOr test a single query:")
    print("   asyncio.run(test_single_query('Show me some hoodies'))")

    # Uncomment to run tests:
    # asyncio.run(test_agent_conversation())

    print("\n" + "="*70)
    print(" "*15 + "✅ GRAPH SYSTEM READY")
    print("="*70 + "\n")
