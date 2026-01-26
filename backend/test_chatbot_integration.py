"""
Quick test script to verify the chatbot integration works
"""
import asyncio
import os
from intelligent_agent_graph import run_agent
from dotenv import load_dotenv
load_dotenv()


async def test_chatbot():
    """Test the intelligent agent with sample queries"""

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set it using: export OPENAI_API_KEY='your-key-here'")
        return

    print("=" * 60)
    print("TESTING CHATBOT INTEGRATION")
    print("=" * 60)

    test_queries = [
        "Show me some hoodies",
        "I want product P001",
    ]

    customer_id = "CUST001"

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}: {query}")
        print("=" * 60)

        try:
            result = await run_agent(customer_id, query)

            print("\n📝 Agent Response:")
            for message in result["messages"]:
                if hasattr(message, 'content') and message.content:
                    if not hasattr(message, 'tool_calls'):
                        print(message.content)

            print("\n🔧 Tools Called:")
            agent_calls = []
            for message in result["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        agent_calls.append(tool_call["name"])

            if agent_calls:
                for agent in agent_calls:
                    print(f"  - {agent}")
            else:
                print("  No tools called")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Chatbot test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_chatbot())
