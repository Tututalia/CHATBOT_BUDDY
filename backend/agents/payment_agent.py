"""
Payment Agent - Processes online payments
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.payment_tools import PaymentTools
import uuid


class PaymentAgent:
    """Agent responsible for payment processing"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.payment_tools = PaymentTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute payment processing
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with payment confirmation
        """
        amount = state.get("amount", 0)
        customer_id = state.get("customer_id")
        selected_product_id = state.get("selected_product_id")
        
        # Process payment using deterministic tool
        payment_result = self.payment_tools.process_payment(
            customer_id=customer_id,
            amount=amount,
            product_id=selected_product_id
        )
        
        payment_status = payment_result.get("status", "failed")
        payment_id = payment_result.get("payment_id", "")
        
        # Generate narrative using LLM
        if payment_status == "success":
            prompt = f"""
You are a payment confirmation assistant.

Amount: ₹{amount}
Payment ID: {payment_id}

Generate a brief, professional message (1-2 sentences) confirming the payment was successful.
"""
        else:
            prompt = f"""
You are a payment assistant.

Payment failed for amount ₹{amount}.

Generate a brief, apologetic message (1-2 sentences) explaining the payment failed and to try again.
"""
        
        narrative_response = self.llm.invoke(prompt)
        
        # Update state
        state["payment_status"] = payment_status
        state["payment_id"] = payment_id
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        
        return state
