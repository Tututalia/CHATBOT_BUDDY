"""
Sales Agent - Manages product selection and user decisions
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class SalesAgent:
    """Agent responsible for sales and product selection"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute sales logic - confirm selection and prepare for next step
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with sales confirmation
        """
        selected_product_id = state.get("selected_product_id")
        channel = state.get("channel")
        recommended_products = state.get("recommended_products", [])
        
        # Find selected product details
        selected_product = None
        for p in recommended_products:
            if p["product_id"] == selected_product_id:
                selected_product = p
                break
        
        if not selected_product:
            state["messages"] = state.get("messages", []) + [
                AIMessage(content="Product details not found. Please try again.")
            ]
            return state
        
        # Generate sales confirmation using LLM
        if channel == "online":
            prompt = f"""
You are a sales assistant. The customer is proceeding with an online purchase.

Product: {selected_product['product_name']}
Price: ₹{selected_product['price']}

Generate a brief, friendly message (1-2 sentences) confirming they're proceeding to payment.
"""
        else:
            prompt = f"""
You are a sales assistant. The customer is proceeding with an offline purchase.

Product: {selected_product['product_name']}
Price: ₹{selected_product['price']}
Stores: {', '.join(state.get('available_stores', [])[:3])}

Generate a brief message (1-2 sentences) confirming they can pick it up from these stores.
"""
        
        narrative_response = self.llm.invoke(prompt)
        
        # Update state
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        state["amount"] = selected_product["price"]
        
        return state
