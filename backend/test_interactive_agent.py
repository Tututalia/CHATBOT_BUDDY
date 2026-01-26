"""
Interactive Test for Intelligent Agent Graph
Run this to chat with the AI agent using OpenAI GPT-4 mini
"""

import asyncio
import os
from dotenv import load_dotenv
from intelligent_agent_graph import create_agent_graph, AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Load environment variables from .env file
load_dotenv()


async def interactive_chat():
    """Interactive chat session with the intelligent agent"""

    print("\n" + "="*70)
    print(" "*15 + "🤖 INTELLIGENT SALES AGENT CHAT")
    print(" "*20 + "OpenAI GPT-4 mini")
    print("="*70)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found!")
        print("\nPlease set your OpenAI API key:")
        print("  Windows: $env:OPENAI_API_KEY='your-key-here'")
        print("  Linux/Mac: export OPENAI_API_KEY='your-key-here'")
        return

    print("\n✅ OpenAI API Key found!")

    # Get customer ID
    customer_id = input(
        "\n👤 Enter Customer ID (or press Enter for CUST001): ").strip()
    if not customer_id:
        customer_id = "CUST001"

    print(f"\n✅ Customer ID: {customer_id}")
    print("\n" + "="*70)
    print("💬 CHAT SESSION STARTED")
    print("="*70)
    print("\nCommands:")
    print("  • Type your message to chat with the agent")
    print("  • Type 'quit' or 'exit' to end the session")
    print("  • Type 'new' to start a new conversation")
    print("\n" + "="*70)

    # Initialize graph
    graph = create_agent_graph()

    # Conversation history
    messages = []

    while True:
        # Get user input
        user_input = input("\n👤 You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Goodbye! Thanks for chatting!")
            break

        if user_input.lower() == 'new':
            messages = []
            print("\n🔄 New conversation started!")
            continue

        # Add user message
        messages.append(HumanMessage(content=user_input))

        # Create state
        state = {
            "messages": messages,
            "customer_id": customer_id,
            "selected_product": None,
            "inventory_status": None,
            "purchase_channel": None,
            "order_id": None,
            "payment_completed": False,
            "loyalty_points": 0
        }

        print("\n⏳ Agent is thinking...")

        try:
            # Run the graph
            result = await graph.ainvoke(state)

            # Update messages with full conversation
            messages = result["messages"]

            # Display the conversation
            print("\n" + "─"*70)

            # Show tool calls if any
            tool_calls_found = False
            for msg in result["messages"]:
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    if not tool_calls_found:
                        print("\n🔧 Agent called tools:")
                        tool_calls_found = True
                    for tool_call in msg.tool_calls:
                        print(
                            f"   → {tool_call['name']}({', '.join(f'{k}={v}' for k, v in tool_call['args'].items())})")

            if tool_calls_found:
                print("\n📦 Tool results received...")

            # Show final agent response
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    print(f"\n🤖 Agent: {msg.content}")
                    break

            print("─"*70)

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("\nPlease try again or type 'quit' to exit.")


async def single_query_test(query: str, customer_id: str = "CUST001"):
    """Test a single query without interactive mode"""

    print("\n" + "="*70)
    print(" "*20 + "🧪 SINGLE QUERY TEST")
    print("="*70)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not set!")
        return

    print(f"\n👤 Customer: {customer_id}")
    print(f"💬 Query: {query}")
    print("\n" + "─"*70)

    # Create graph
    graph = create_agent_graph()

    # Create state
    state = {
        "messages": [HumanMessage(content=query)],
        "customer_id": customer_id,
        "selected_product": None,
        "inventory_status": None,
        "purchase_channel": None,
        "order_id": None,
        "payment_completed": False,
        "loyalty_points": 0
    }

    try:
        # Run graph
        result = await graph.ainvoke(state)

        # Display results
        print("\n📝 CONVERSATION FLOW:")
        print("─"*70)

        for i, msg in enumerate(result["messages"], 1):
            if isinstance(msg, HumanMessage):
                print(f"\n{i}. 👤 USER: {msg.content}")

            elif isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"\n{i}. 🤖 AGENT → Calling tools:")
                    for tool_call in msg.tool_calls:
                        args_str = ', '.join(
                            f'{k}={v}' for k, v in tool_call['args'].items())
                        print(f"      → {tool_call['name']}({args_str})")
                elif msg.content:
                    print(f"\n{i}. 🤖 AGENT: {msg.content}")

            elif isinstance(msg, ToolMessage):
                # Show abbreviated tool result
                content_preview = msg.content[:150] + \
                    "..." if len(msg.content) > 150 else msg.content
                print(f"\n{i}. 🔧 TOOL RESULT: {content_preview}")

        print("\n" + "─"*70)
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print(" "*10 + "🚀 INTELLIGENT AGENT GRAPH - INTERACTIVE TESTER")
    print("="*70)

    print("\nSelect mode:")
    print("  1. Interactive Chat (recommended)")
    print("  2. Single Query Test")
    print("  3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        asyncio.run(interactive_chat())

    elif choice == "2":
        query = input("\nEnter your query: ").strip()
        if query:
            customer_id = input(
                "Enter Customer ID (or press Enter for CUST001): ").strip()
            if not customer_id:
                customer_id = "CUST001"
            asyncio.run(single_query_test(query, customer_id))
        else:
            print("❌ Query cannot be empty!")

    elif choice == "3":
        print("\n👋 Goodbye!")

    else:
        print("\n❌ Invalid choice!")


if __name__ == "__main__":
    main()
