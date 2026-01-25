"""
Recommendation Agent - Suggests products based on user preferences
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.product_tools import ProductTools


class RecommendationAgent:
    """Agent responsible for product recommendations"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.product_tools = ProductTools()
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the recommendation logic
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with product recommendations
        """
        query = state.get("query", "")
        customer_id = state.get("customer_id", "")
        
        # Parse user intent using LLM
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
        
        # Get intent from LLM
        intent_response = self.llm.invoke(intent_prompt)
        intent_text = intent_response.content
        
        # Parse intent (simple extraction)
        import json
        try:
            # Try to extract JSON from response
            start = intent_text.find('{')
            end = intent_text.rfind('}') + 1
            if start >= 0 and end > start:
                intent = json.loads(intent_text[start:end])
            else:
                intent = {}
        except:
            intent = {}
        
        # Get customer purchase history for personalization
        customer_data = self.product_tools.get_customer_data(customer_id)
        
        # Search products using deterministic tool
        # If no intent extracted, do a general search
        category = intent.get("category")
        max_price = intent.get("max_price")
        gender = intent.get("gender")
        occasion = intent.get("occasion")
        
        # Normalize category to handle plurals (shirts -> shirt)
        if category:
            category = category.strip()
            # Remove common plural 's' at the end
            if category.endswith('s') and len(category) > 2:
                # Don't remove 's' from words like 'jeans', 'trousers', 'accessories'
                if category.lower() not in ['jeans', 'trousers', 'accessories', 'pants', 'shorts']:
                    category = category[:-1]
        
        # Debug: print extracted intent
        print(f"DEBUG: Extracted intent - category={category}, max_price={max_price}, gender={gender}, occasion={occasion}")
        
        products = self.product_tools.search_products(
            category=category,
            max_price=max_price or 10000,
            gender=gender,
            occasion=occasion
        )
        
        print(f"DEBUG: Initial search returned {len(products)} products")
        
        # If no products found with all filters, try relaxing filters progressively
        if not products and occasion:
            print(f"DEBUG: Trying search without occasion filter...")
            products = self.product_tools.search_products(
                category=category,
                max_price=max_price or 10000,
                gender=gender
            )
            print(f"DEBUG: Search without occasion returned {len(products)} products")
        
        # If still no products, try just category and price
        if not products and category:
            print(f"DEBUG: Trying search with only category and price...")
            products = self.product_tools.search_products(
                category=category,
                max_price=max_price or 3000
            )
            print(f"DEBUG: Search with category+price returned {len(products)} products")
        
        # Last resort: general search
        if not products:
            print("DEBUG: No products found, trying general search...")
            products = self.product_tools.search_products(max_price=3000)
        
        # Limit to top 5 products for selection
        recommended_products = products[:5]
        
        print(f"DEBUG: Found {len(recommended_products)} products")
        
        # Use LLM to select the best matching product
        best_product = None
        if len(recommended_products) > 0:
            if len(recommended_products) == 1:
                # Only one option, select it
                best_product = recommended_products[0]
                print(f"DEBUG: Only 1 product found, auto-selecting: {best_product['product_name']}")
            else:
                # Multiple products - let LLM pick the closest match
                selection_prompt = f"""
You are a retail expert. A customer asked: "{query}"

We found these products:
{self._format_products_detailed(recommended_products)}

Analyze the customer's query and select THE ONE BEST matching product based on:
1. How well it matches the requested category/type
2. Price appropriateness for their budget
3. Relevance to mentioned occasion/season
4. Overall best fit for their needs

Return ONLY the product_id of the best match (e.g., "PRD028"). Nothing else.
"""
                
                selection_response = self.llm.invoke(selection_prompt)
                selected_id = selection_response.content.strip().upper()
                
                # Find the selected product
                for product in recommended_products:
                    if product["product_id"] in selected_id:
                        best_product = product
                        print(f"DEBUG: LLM selected best match: {best_product['product_name']} ({best_product['product_id']})")
                        break
                
                # Fallback to first product if LLM selection failed
                if not best_product:
                    best_product = recommended_products[0]
                    print(f"DEBUG: LLM selection unclear, defaulting to first product: {best_product['product_name']}")
        
        # Generate narrative using LLM
        if best_product:
            narrative_prompt = f"""
You are a friendly retail assistant. The customer asked: "{query}"

You found the perfect match: {best_product['product_name']} for ₹{best_product['price']}.

Generate a brief, enthusiastic message (2-3 sentences) recommending this product.
Mention why it's a great choice for their needs.
"""
        else:
            narrative_prompt = f"""
You are a friendly retail assistant. The customer asked: "{query}"

Unfortunately, we couldn't find products matching those exact criteria.

Generate a brief, apologetic message (2 sentences) and suggest they try different filters.
"""
        
        narrative_response = self.llm.invoke(narrative_prompt)
        
        # Update state
        state["recommended_products"] = recommended_products
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=narrative_response.content)
        ]
        
        # Set the best matching product
        if best_product:
            state["selected_product_id"] = best_product["product_id"]
        
        return state
    
    def _format_products(self, products: List[Dict[str, Any]]) -> str:
        """Format products for LLM context"""
        formatted = []
        for p in products:
            formatted.append(
                f"- {p['product_name']} (₹{p['price']}) - {p['category']}"
            )
        return "\n".join(formatted)
    
    def _format_products_detailed(self, products: List[Dict[str, Any]]) -> str:
        """Format products with full details for LLM selection"""
        formatted = []
        for i, p in enumerate(products, 1):
            details = [
                f"{i}. Product ID: {p['product_id']}",
                f"   Name: {p['product_name']}",
                f"   Category: {p['category']}",
                f"   Price: ₹{p['price']}",
                f"   Gender: {p.get('gender', 'Unisex')}",
            ]
            if p.get('festival'):
                details.append(f"   Festival: {p['festival']}")
            if p.get('season'):
                details.append(f"   Season: {p['season']}")
            formatted.append("\n".join(details))
        return "\n\n".join(formatted)
