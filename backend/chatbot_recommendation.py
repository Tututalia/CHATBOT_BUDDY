"""
Modified Recommendation Agent for Chatbot with User Choice
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.product_tools import ProductTools


class ChatbotRecommendationAgent:
    """Agent responsible for product recommendations with user choice"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.product_tools = ProductTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute recommendation logic for chatbot interaction
        """
        query = state.get("query", "")
        
        # Extract intent using LLM (same as before)
        intent = self._extract_intent(query)
        
        # Search products using deterministic tools (same as before)
        products = self._search_products(intent)
        
        # Instead of auto-selecting, present options to user
        if len(products) == 0:
            narrative = "I couldn't find any products matching your criteria. Could you try different filters?"
            state["awaiting_user_input"] = False
            
        elif len(products) == 1:
            # Only one option - auto-select and proceed
            state["selected_product_id"] = products[0]["product_id"]
            narrative = f"Perfect! I found the ideal match: {products[0]['product_name']} for ₹{products[0]['price']}. Let me proceed with this."
            state["awaiting_user_input"] = False
            
        else:
            # Multiple options - let user choose
            narrative = self._create_choice_message(products, query)
            state["awaiting_user_input"] = True
            state["choice_context"] = "product_selection"
            
        state["recommended_products"] = products
        state["messages"] = state.get("messages", []) + [AIMessage(content=narrative)]
        
        return state
        
    def handle_user_choice(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        Handle user's product choice
        """
        products = state.get("recommended_products", [])
        
        try:
            # Parse user choice (1, 2, 3, etc.)
            choice_index = int(user_input.strip()) - 1
            
            if 0 <= choice_index < len(products):
                selected_product = products[choice_index]
                state["selected_product_id"] = selected_product["product_id"]
                
                # Generate confirmation message
                confirmation = f"Excellent choice! You've selected {selected_product['product_name']} for ₹{selected_product['price']}. Let me check availability and proceed with your order."
                
                state["messages"] = state.get("messages", []) + [AIMessage(content=confirmation)]
                state["awaiting_user_input"] = False
                state["choice_context"] = None
                
            else:
                # Invalid choice
                error_msg = f"Please enter a number between 1 and {len(products)}."
                state["messages"] = state.get("messages", []) + [AIMessage(content=error_msg)]
                # Keep awaiting input
                
        except ValueError:
            # Invalid input format
            error_msg = f"Please enter the number of your choice (1-{len(products)})."
            state["messages"] = state.get("messages", []) + [AIMessage(content=error_msg)]
            # Keep awaiting input
            
        return state
    
    def _extract_intent(self, query: str) -> Dict[str, Any]:
        """Extract user intent using LLM (same as current implementation)"""
        intent_prompt = f"""
        You are a retail recommendation agent. Analyze this customer query and extract:
        1. Product category (e.g., shirts, jeans, footwear)
        2. Price range preference (if mentioned)
        3. Gender preference (if mentioned) 
        4. Occasion (festival, season) if mentioned

        Query: "{query}"

        Return ONLY a JSON object with keys: category, max_price, gender, occasion
        Example: {{"category": "shirt", "max_price": 3000, "gender": "male", "occasion": null}}
        """
        
        intent_response = self.llm.invoke(intent_prompt)
        # Parse JSON response (same logic as current implementation)
        # ... implementation details ...
        return {}
    
    def _search_products(self, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search products using deterministic tools (same as current implementation)"""
        # ... same search logic as current implementation ...
        return []
    
    def _create_choice_message(self, products: List[Dict[str, Any]], query: str) -> str:
        """Create user-friendly choice message"""
        
        choice_prompt = f"""
        Create a friendly chatbot response showing {len(products)} product options.
        User asked: "{query}"
        
        Format the response like:
        "Here are {len(products)} great options I found:
        
        1. [Product Name] - ₹[Price]
           • Brief appealing description
           
        2. [Product Name] - ₹[Price]  
           • Brief appealing description
           
        Which one would you like? Just type the number (1, 2, etc.)"
        
        Keep it conversational and helpful.
        """
        
        # Include product details in prompt
        products_text = ""
        for i, product in enumerate(products, 1):
            products_text += f"{i}. {product['product_name']} - ₹{product['price']} ({product['category']})\n"
        
        choice_prompt += f"\n\nProducts:\n{products_text}"
        
        response = self.llm.invoke(choice_prompt)
        return response.content


class ChatbotOrchestrator:
    """
    Modified orchestrator that handles user choices
    """
    
    def __init__(self):
        # ... initialization ...
        pass
        
    async def process_user_message(self, message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user message and manage conversation state
        """
        
        if session_state.get("awaiting_user_input"):
            # Handle user choice
            choice_context = session_state.get("choice_context")
            
            if choice_context == "product_selection":
                # User is choosing a product
                session_state = self.recommendation_agent.handle_user_choice(session_state, message)
                
                if not session_state.get("awaiting_user_input"):
                    # Choice made, continue workflow
                    return await self._continue_workflow(session_state)
                else:
                    # Still awaiting valid choice
                    return session_state
                    
        else:
            # New query - start workflow
            session_state["query"] = message
            return await self._start_workflow(session_state)
    
    async def _start_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Start the agent workflow"""
        # Run recommendation agent
        state = self.recommendation_agent.execute(state)
        
        if not state.get("awaiting_user_input"):
            # No user choice needed, continue workflow
            return await self._continue_workflow(state)
        else:
            # Waiting for user choice, return state
            return state
    
    async def _continue_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Continue with inventory, sales, payment, etc."""
        # Run rest of the agents (inventory -> sales -> payment -> ...)
        # Same as current implementation
        return state