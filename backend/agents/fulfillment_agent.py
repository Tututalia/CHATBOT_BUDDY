"""
Fulfillment Agent - Handles order fulfillment and dispatch
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.fulfillment_tools import FulfillmentTools
import uuid


class FulfillmentAgent:
    """Agent responsible for order fulfillment"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.fulfillment_tools = FulfillmentTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute fulfillment processing
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with fulfillment information
        """
        customer_id = state.get("customer_id")
        selected_product_id = state.get("selected_product_id")
        channel = state.get("channel")
        payment_status = state.get("payment_status")
        
        # Create order using deterministic tool
        order_result = self.fulfillment_tools.create_order(
            customer_id=customer_id,
            product_id=selected_product_id,
            channel=channel,
            payment_verified=(payment_status == "success")
        )
        
        order_id = order_result.get("order_id", "")
        fulfillment_status = order_result.get("status", "pending")
        
        # Generate narrative using LLM
        if channel == "online":
            prompt = f"""
You are a fulfillment assistant.

Order ID: {order_id}
Status: Order confirmed and being prepared for dispatch

Generate a brief message (1-2 sentences) confirming the order will be shipped soon.
"""
        else:
            prompt = f"""
You are a fulfillment assistant.

Order ID: {order_id}
Status: Ready for pickup at store

Generate a brief message (1-2 sentences) confirming the order is ready for pickup.
"""
        
        narrative_response = self.llm.invoke(prompt)
        
        # Update state
        state["order_id"] = order_id
        state["fulfillment_status"] = fulfillment_status
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        
        return state
