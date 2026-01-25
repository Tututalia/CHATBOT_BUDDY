"""
Loyalty Agent - Manages loyalty points and rewards
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.loyalty_tools import LoyaltyTools


class LoyaltyAgent:
    """Agent responsible for loyalty rewards and points"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.loyalty_tools = LoyaltyTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute loyalty processing
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with loyalty information
        """
        customer_id = state.get("customer_id")
        amount = state.get("amount", 0)
        order_id = state.get("order_id")
        
        # Process loyalty points using deterministic tool
        loyalty_result = self.loyalty_tools.process_loyalty(
            customer_id=customer_id,
            order_amount=amount,
            order_id=order_id
        )
        
        points_earned = loyalty_result.get("points_earned", 0)
        total_points = loyalty_result.get("total_points", 0)
        coupons = loyalty_result.get("available_coupons", [])
        
        # Generate narrative using LLM
        prompt = f"""
You are a loyalty rewards assistant.

Points Earned: {points_earned}
Total Loyalty Points: {total_points}
Available Coupons: {len(coupons)} coupons

Generate a brief, enthusiastic message (2-3 sentences) congratulating them on earning points.
Mention they have coupons available if any.
"""
        
        narrative_response = self.llm.invoke(prompt)
        
        # Update state
        state["loyalty_points_earned"] = points_earned
        state["loyalty_coupons"] = coupons
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        
        return state
