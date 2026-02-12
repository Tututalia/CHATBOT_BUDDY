"""
Interactive test script for intelligent agent
Type your queries and see which agent tools the LLM calls
"""

import asyncio
from intelligent_agent_graph import run_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


async def interactive_test():
    """
    Interactive testing - type queries and see agent responses
    """
    customer_id = "CUST001"

    print("\n" + "="*80)
    print("🤖 INTELLIGENT AGENT - INTERACTIVE TEST")
    print("="*80)
    print("\nCustomer ID:", customer_id)
    print("\nType your queries to test the agent workflow.")
    print("Example queries:")
    print("  - Show me hoodies")
    print("  - Add product PRD001, quantity 2")
    print("  - View my cart")
    print("  - Proceed to checkout")
    print("  - Online")
    print("  - UPI")
    print("\nType 'exit' or 'quit' to stop.\n")
    print("="*80 + "\n")

    conversation_history = []

    while True:
        # Get user input
        try:
            query = input("👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Exiting interactive test...")
            break

        if not query:
            continue

        if query.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Exiting interactive test...")
            break

        print("\n" + "-"*80)
        print("🔄 Processing your request...\n")

        # Run agent
        try:
            result = await run_agent(customer_id, query)

            # Extract tool calls and responses
            messages = result["messages"]

            print("📋 AGENT RESPONSE:")
            print("-"*80)

            tool_calls_found = False

            for i, msg in enumerate(messages):
                # Show tool calls
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls_found = True
                    print("\n🔧 TOOLS CALLED:")
                    for tc in msg.tool_calls:
                        print(f"  ✓ {tc['name']}()")
                        if tc.get('args'):
                            for key, val in tc['args'].items():
                                if len(str(val)) > 100:
                                    print(f"      {key}: {str(val)[:100]}...")
                                else:
                                    print(f"      {key}: {val}")
                    print()

                # Show tool results
                elif isinstance(msg, ToolMessage):
                    content = msg.content
                    if len(content) > 500:
                        content = content[:500] + "..."
                    print(f"📦 Tool Result:\n{content}\n")

                # Show AI response
                elif isinstance(msg, AIMessage) and msg.content:
                    print(f"🤖 Agent: {msg.content}\n")

            if not tool_calls_found:
                # Check if there's a final AI message
                last_ai_msg = None
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        last_ai_msg = msg.content
                        break

                if last_ai_msg:
                    print(f"🤖 Agent: {last_ai_msg}\n")
                else:
                    print("⚠️  No tools called - LLM responded directly\n")

            print("-"*80 + "\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            print("-"*80 + "\n")

if __name__ == "__main__":
    print("\n🚀 Starting interactive agent test...")
    asyncio.run(interactive_test())
