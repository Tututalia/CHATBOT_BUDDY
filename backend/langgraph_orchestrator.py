"""
LangGraph-based Multi-Agent Orchestrator for Retail Chatbot
This module orchestrates the flow between different agents using LangGraph StateGraph
"""

from typing import TypedDict, Annotated, Sequence, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import operator
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Define the state that will be passed between agents
class AgentState(TypedDict):
    """State shared across all agents in the workflow"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    customer_id: str
    customer_name: Optional[str]
    query: str
    
    # Recommendation Agent outputs
    recommended_products: Optional[List[Dict[str, Any]]]
    selected_product_id: Optional[str]
    
    # Inventory Agent outputs
    inventory_info: Optional[Dict[str, Any]]
    channel: Optional[str]  # "online" or "offline"
    available_stores: Optional[List[str]]
    
    # Payment Agent outputs
    payment_status: Optional[str]
    payment_id: Optional[str]
    amount: Optional[float]
    
    # Fulfillment Agent outputs
    order_id: Optional[str]
    fulfillment_status: Optional[str]
    
    # Loyalty Agent outputs
    loyalty_points_earned: Optional[int]
    loyalty_coupons: Optional[List[Dict[str, Any]]]
    
    # Post Purchase Agent outputs
    post_purchase_offers: Optional[List[Dict[str, Any]]]
    
    # Agent timeline for live tracking
    timeline: Annotated[List[Dict[str, Any]], operator.add]
    
    # Current step in the flow
    current_step: str
    
    # Flag to indicate completion
    completed: bool


class RetailAgentOrchestrator:
    """
    Main orchestrator class that manages the multi-agent workflow using LangGraph
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = None):
        """Initialize the orchestrator with LLM and workflow graph"""
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Use specified model or default to gpt-4o-mini (cheap & fast)
        default_model = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model=default_model,
            api_key=self.api_key,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3"))
        )
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with all agents"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("recommendation_agent", self.recommendation_agent)
        workflow.add_node("inventory_agent", self.inventory_agent)
        workflow.add_node("sales_agent", self.sales_agent)
        workflow.add_node("payment_agent", self.payment_agent)
        workflow.add_node("fulfillment_agent", self.fulfillment_agent)
        workflow.add_node("loyalty_agent", self.loyalty_agent)
        workflow.add_node("post_purchase_agent", self.post_purchase_agent)
        
        # Define the workflow edges
        workflow.set_entry_point("recommendation_agent")
        
        # Recommendation -> Inventory
        workflow.add_edge("recommendation_agent", "inventory_agent")
        
        # Inventory -> Sales (with conditional routing)
        workflow.add_edge("inventory_agent", "sales_agent")
        
        # Sales -> Conditional routing based on channel
        workflow.add_conditional_edges(
            "sales_agent",
            self.route_after_sales,
            {
                "payment": "payment_agent",
                "fulfillment": "fulfillment_agent",
                "end": END
            }
        )
        
        # Payment -> Fulfillment
        workflow.add_edge("payment_agent", "fulfillment_agent")
        
        # Fulfillment -> Loyalty
        workflow.add_edge("fulfillment_agent", "loyalty_agent")
        
        # Loyalty -> Post Purchase
        workflow.add_edge("loyalty_agent", "post_purchase_agent")
        
        # Post Purchase -> END
        workflow.add_edge("post_purchase_agent", END)
        
        return workflow.compile()
    
    def recommendation_agent(self, state: AgentState) -> AgentState:
        """
        Recommendation Agent: Suggests products based on user query
        """
        from agents.recommendation_agent import RecommendationAgent
        
        agent = RecommendationAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "recommendation_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Products recommended",
            "details": f"Found {len(result.get('recommended_products', []))} products"
        }]
        
        result["current_step"] = "recommendation"
        return result
    
    def inventory_agent(self, state: AgentState) -> AgentState:
        """
        Inventory Agent: Checks product availability in online/offline stores
        """
        from agents.inventory_agent import InventoryAgent
        
        agent = InventoryAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "inventory_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Inventory checked",
            "details": f"Available via {result.get('channel', 'unknown')} channel"
        }]
        
        result["current_step"] = "inventory"
        return result
    
    def sales_agent(self, state: AgentState) -> AgentState:
        """
        Sales Agent: Handles product selection and user decisions
        """
        from agents.sales_agent import SalesAgent
        
        agent = SalesAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "sales_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Product selected",
            "details": f"User selected product {result.get('selected_product_id', 'N/A')}"
        }]
        
        result["current_step"] = "sales"
        return result
    
    def payment_agent(self, state: AgentState) -> AgentState:
        """
        Payment Agent: Processes online payments
        """
        from agents.payment_agent import PaymentAgent
        
        agent = PaymentAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "payment_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Payment processed",
            "details": f"Payment {result.get('payment_status', 'unknown')} - Amount: ₹{result.get('amount', 0)}"
        }]
        
        result["current_step"] = "payment"
        return result
    
    def fulfillment_agent(self, state: AgentState) -> AgentState:
        """
        Fulfillment Agent: Handles order fulfillment
        """
        from agents.fulfillment_agent import FulfillmentAgent
        
        agent = FulfillmentAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "fulfillment_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Order confirmed",
            "details": f"Order {result.get('order_id', 'N/A')} - {result.get('fulfillment_status', 'pending')}"
        }]
        
        result["current_step"] = "fulfillment"
        return result
    
    def loyalty_agent(self, state: AgentState) -> AgentState:
        """
        Loyalty Agent: Processes loyalty points and rewards
        """
        from agents.loyalty_agent import LoyaltyAgent
        
        agent = LoyaltyAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "loyalty_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Loyalty rewards processed",
            "details": f"Earned {result.get('loyalty_points_earned', 0)} points"
        }]
        
        result["current_step"] = "loyalty"
        return result
    
    def post_purchase_agent(self, state: AgentState) -> AgentState:
        """
        Post Purchase Agent: Provides post-purchase services and offers
        """
        from agents.post_purchase_agent import PostPurchaseAgent
        
        agent = PostPurchaseAgent(self.llm)
        result = agent.execute(state)
        
        # Add timeline event
        result["timeline"] = [{
            "agent": "post_purchase_agent",
            "timestamp": datetime.now().isoformat(),
            "action": "Post-purchase services setup",
            "details": "Setup complete for order tracking and support"
        }]
        
        result["current_step"] = "post_purchase"
        result["completed"] = True
        return result
    
    def route_after_sales(self, state: AgentState) -> str:
        """
        Conditional routing after sales agent
        - If channel is 'online', go to payment
        - If channel is 'offline', go directly to fulfillment
        - Otherwise end
        """
        channel = state.get("channel") or ""
        channel = channel.lower() if channel else ""
        
        if channel == "online":
            return "payment"
        elif channel == "offline":
            return "fulfillment"
        else:
            return "end"
    
    def run(self, customer_id: str, query: str, customer_name: str = None) -> Dict[str, Any]:
        """
        Execute the complete agent workflow
        
        Args:
            customer_id: The customer's unique identifier
            query: The user's query or message
            customer_name: Optional customer name
            
        Returns:
            Final state with all agent outputs and timeline
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "customer_id": customer_id,
            "customer_name": customer_name,
            "query": query,
            "recommended_products": None,
            "selected_product_id": None,
            "inventory_info": None,
            "channel": None,
            "available_stores": None,
            "payment_status": None,
            "payment_id": None,
            "amount": None,
            "order_id": None,
            "fulfillment_status": None,
            "loyalty_points_earned": None,
            "loyalty_coupons": None,
            "post_purchase_offers": None,
            "timeline": [],
            "current_step": "start",
            "completed": False
        }
        
        # Execute the workflow
        final_state = self.workflow.invoke(initial_state)
        
        return final_state
    
    async def arun(self, customer_id: str, query: str, customer_name: str = None) -> Dict[str, Any]:
        """Async version of run for better performance"""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "customer_id": customer_id,
            "customer_name": customer_name,
            "query": query,
            "recommended_products": None,
            "selected_product_id": None,
            "inventory_info": None,
            "channel": None,
            "available_stores": None,
            "payment_status": None,
            "payment_id": None,
            "amount": None,
            "order_id": None,
            "fulfillment_status": None,
            "loyalty_points_earned": None,
            "loyalty_coupons": None,
            "post_purchase_offers": None,
            "timeline": [],
            "current_step": "start",
            "completed": False
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state
