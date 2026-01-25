"""
Post Purchase Agent - Provides post-purchase services
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.post_purchase_tools import PostPurchaseTools


class PostPurchaseAgent:
    """Agent responsible for post-purchase services"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.post_purchase_tools = PostPurchaseTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute post-purchase services
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with post-purchase information
        """
        customer_id = state.get("customer_id")
        order_id = state.get("order_id")
        selected_product_id = state.get("selected_product_id")
        
        # Setup post-purchase services using deterministic tool
        post_purchase_result = self.post_purchase_tools.setup_services(
            customer_id=customer_id,
            order_id=order_id,
            product_id=selected_product_id
        )
        
        offers = post_purchase_result.get("personalized_offers", [])
        tracking_enabled = post_purchase_result.get("tracking_enabled", False)
        
        # Generate narrative using LLM
        prompt = f"""
You are a post-purchase service assistant.

Order ID: {order_id}
Tracking: {'Enabled' if tracking_enabled else 'Not available'}
Personalized Offers: {len(offers)} offers available

Generate a brief, helpful message (2-3 sentences) thanking them for their purchase.
Mention they can track their order and that personalized offers are available.
"""
        
        narrative_response = self.llm.invoke(prompt)
        
        # Update state
        state["post_purchase_offers"] = offers
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        
        return state
