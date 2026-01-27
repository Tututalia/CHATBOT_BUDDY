"""
Product Tools - Database-based product search and retrieval
"""

from typing import Dict, Any, List, Optional
from sqlmodel import Session
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from models import Product, Customer, OrderHistory
from crud import product_crud, customer_crud, order_history_crud


class ProductTools:
    """Tools for product search and retrieval from database"""
    
    def __init__(self):
        """Initialize ProductTools with database connection"""
        self.engine = engine
    
    def _get_session(self) -> Session:
        """Get a database session"""
        return Session(self.engine)
    
    def search_products(
        self,
        category: str = None,
        max_price: float = None,
        min_price: float = None,
        gender: str = None,
        season: str = None,
        occasion: str = None,
        online_available: str = None,
        offline_available: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search products with various filters
        
        Args:
            category: Product category (e.g., 'shirt', 'jeans', 'footwear')
            max_price: Maximum price filter
            min_price: Minimum price filter
            gender: Gender filter ('male', 'female', 'unisex')
            season: Season filter ('summer', 'winter', 'all')
            occasion: Occasion/Festival filter
            online_available: 'Yes' or 'No'
            offline_available: 'Yes' or 'No'
            limit: Maximum number of results
            
        Returns:
            List of product dictionaries
        """
        try:
            with self._get_session() as session:
                # Build filters
                filters = {}
                operators = {}
                
                if category:
                    filters['category'] = category.lower()
                    operators['category'] = 'contains'
                
                if gender:
                    filters['gender'] = gender.lower()
                    operators['gender'] = 'contains'
                
                if season:
                    filters['season'] = season.lower()
                    operators['season'] = 'contains'
                
                if online_available:
                    filters['online_available'] = online_available
                
                if offline_available:
                    filters['offline_available'] = offline_available
                
                # Get products with filters
                if filters:
                    products = product_crud.filter(session, filters, operators, limit=limit)
                else:
                    products = product_crud.get_all(session, limit=limit)
                
                # Apply price filters (handled separately for range)
                if min_price is not None:
                    products = [p for p in products if p.price >= min_price]
                
                if max_price is not None:
                    products = [p for p in products if p.price <= max_price]
                
                # Apply occasion/festival filter
                if occasion:
                    occasion_lower = occasion.lower()
                    products = [
                        p for p in products 
                        if p.festival and occasion_lower in p.festival.lower()
                    ]
                
                # Convert to dictionaries
                return [self._product_to_dict(p) for p in products]
                
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a product by its ID
        
        Args:
            product_id: The product ID (e.g., 'P001')
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            with self._get_session() as session:
                product = product_crud.get_by_id(session, product_id)
                if product:
                    return self._product_to_dict(product)
                return None
        except Exception as e:
            print(f"Error getting product {product_id}: {e}")
            return None
    
    def get_all_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all products from database
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries
        """
        try:
            with self._get_session() as session:
                products = product_crud.get_all(session, limit=limit)
                return [self._product_to_dict(p) for p in products]
        except Exception as e:
            print(f"Error getting all products: {e}")
            return []
    
    def get_customer_data(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer data by ID
        
        Args:
            customer_id: The customer ID
            
        Returns:
            Customer dictionary or None if not found
        """
        try:
            with self._get_session() as session:
                customer = customer_crud.get_by_id(session, customer_id)
                if customer:
                    return self._customer_to_dict(customer)
                return None
        except Exception as e:
            print(f"Error getting customer {customer_id}: {e}")
            return None
    
    def get_customer_order_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get customer's order history
        
        Args:
            customer_id: The customer ID
            
        Returns:
            List of order dictionaries
        """
        try:
            with self._get_session() as session:
                orders = order_history_crud.filter(session, {'customer_id': customer_id})
                return [self._order_to_dict(o) for o in orders]
        except Exception as e:
            print(f"Error getting order history for customer {customer_id}: {e}")
            return []
    
    def search_by_text(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products by text query across multiple fields
        
        Args:
            query: Search query text
            limit: Maximum number of results
            
        Returns:
            List of matching product dictionaries
        """
        try:
            with self._get_session() as session:
                # Get all products and filter by query
                products = product_crud.get_all(session, limit=500)
                
                query_lower = query.lower()
                keywords = query_lower.split()
                
                matched = []
                for product in products:
                    score = 0
                    for keyword in keywords:
                        if keyword in product.product_name.lower():
                            score += 3
                        if keyword in product.category.lower():
                            score += 2
                        if product.festival and keyword in product.festival.lower():
                            score += 1
                        if keyword in product.season.lower():
                            score += 1
                        if keyword in product.gender.lower():
                            score += 1
                    
                    if score > 0:
                        matched.append((score, product))
                
                # Sort by score descending and take top results
                matched.sort(key=lambda x: x[0], reverse=True)
                top_products = [p for _, p in matched[:limit]]
                
                return [self._product_to_dict(p) for p in top_products]
                
        except Exception as e:
            print(f"Error searching products by text: {e}")
            return []
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert a Product model to dictionary"""
        return {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "category": product.category,
            "gender": product.gender,
            "price": product.price,
            "online_available": product.online_available,
            "offline_available": product.offline_available,
            "offline_stores": product.offline_stores,
            "store_ids": product.store_ids,
            "festival": product.festival,
            "season": product.season,
            "image_reference": product.image_reference,
            "loyalty_points": product.loyalty_points
        }
    
    def _customer_to_dict(self, customer: Customer) -> Dict[str, Any]:
        """Convert a Customer model to dictionary"""
        return {
            "customer_id": customer.customer_id,
            "customer_name": customer.customer_name,
            "gender": customer.gender,
            "phone": customer.phone,
            "address": customer.address,
            "loyalty_points": customer.loyalty_points,
            "order_history": customer.order_history,
            "order_dates": customer.order_dates,
            "pending_orders": customer.pending_orders
        }
    
    def _order_to_dict(self, order: OrderHistory) -> Dict[str, Any]:
        """Convert an OrderHistory model to dictionary"""
        return {
            "transaction_id": order.transaction_id,
            "customer_id": order.customer_id,
            "customer_name": order.customer_name,
            "product_id": order.product_id,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "order_dates": order.order_dates,
            "loyalty_points": order.loyalty_points
        }
