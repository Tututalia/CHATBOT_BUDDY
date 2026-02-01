"""Quick test to verify LLM extracts quantity correctly"""
import asyncio
from intelligent_agent_graph import run_agent


async def test():
    print("="*60)
    print("Testing quantity extraction in agent")
    print("="*60)

    # Test: Add product with explicit quantity
    print("\n📝 User Query: 'Add PRD049 with quantity 4'")
    result = await run_agent("CUST001", "Add PRD049 with quantity 4")

    print("\n🤖 Agent Response:")
    for msg in result["messages"]:
        if hasattr(msg, 'content') and msg.content:
            print(msg.content[:300])
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"\n🔧 Tool Call: {tc['name']}")
                print(f"   Args: {tc['args']}")

asyncio.run(test())
