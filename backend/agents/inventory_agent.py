"""
Inventory Agent - Checks product availability across channels
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.inventory_tools import InventoryTools


class InventoryAgent:
    """Agent responsible for checking inventory availability"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.inventory_tools = InventoryTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute inventory checking logic
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with inventory information
        """
        selected_product_id = state.get("selected_product_id")
        
        if not selected_product_id:
            state["messages"] = state.get("messages", []) + [
                AIMessage(content="No product was selected. Please choose a product first.")
            ]
            return state
        
        # Check inventory using deterministic tool
        inventory_info = self.inventory_tools.check_availability(selected_product_id)
        
        # Get product details
        product_details = self.inventory_tools.get_product_details(selected_product_id)
        
        # Prepare inventory summary
        online_available = inventory_info.get("online_available", False)
        offline_stores = inventory_info.get("offline_stores", [])
        
        # Generate narrative using LLM
        narrative_prompt = f"""
You are a retail inventory assistant. 

Product: {product_details.get('product_name', 'Unknown')}
Price: ₹{product_details.get('price', 0)}
Online Available: {online_available}
Offline Stores: {', '.join(offline_stores) if offline_stores else 'None'}

Generate a brief message (2-3 sentences) explaining availability to the customer.
Mention size 40 availability if asked (for demo, say it's available).
Be friendly and helpful.
"""
        
        narrative_response = self.llm.invoke(narrative_prompt)
        
        # Determine channel preference
        # For demo: prefer online if available, otherwise offline
        if online_available:
            channel = "online"
        elif offline_stores:
            channel = "offline"
        else:
            channel = None
        
        # Update state
        state["inventory_info"] = inventory_info
        state["channel"] = channel
        state["available_stores"] = offline_stores
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        
        return state
