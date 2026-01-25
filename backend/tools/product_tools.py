"""
Product Tools - Deterministic tools for product data access
"""

import pandas as pd
import os
from typing import List, Dict, Any, Optional


class ProductTools:
    """Tools for accessing product and customer data"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self._product_df = None
        self._customer_df = None
        
    @property
    def product_df(self) -> pd.DataFrame:
        """Lazy load product data"""
        if self._product_df is None:
            csv_path = os.path.join(self.data_dir, "product_data.csv")
            self._product_df = pd.read_csv(csv_path)
        return self._product_df
    
    @property
    def customer_df(self) -> pd.DataFrame:
        """Lazy load customer data"""
        if self._customer_df is None:
            csv_path = os.path.join(self.data_dir, "customer_data.csv")
            self._customer_df = pd.read_csv(csv_path)
        return self._customer_df
    
    def search_products(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        gender: Optional[str] = None,
        occasion: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search products with filters
        
        Args:
            category: Product category (e.g., 'shirt', 'jeans')
            max_price: Maximum price filter
            gender: Gender filter ('male', 'female', 'unisex')
            occasion: Festival or season occasion
            limit: Maximum number of results
            
        Returns:
            List of matching products
        """
        df = self.product_df.copy()
        
        # Apply filters
        if category:
            # Case-insensitive partial match
            df = df[df['category'].str.lower().str.contains(category.lower(), na=False)]
        
        if max_price:
            df = df[df['price'] <= max_price]
        
        if gender:
            # Match gender or unisex
            df = df[
                (df['gender'].str.lower() == gender.lower()) | 
                (df['gender'].str.lower() == 'unisex')
            ]
        
        if occasion:
            # Check if occasion appears in festival or season columns
            df = df[
                df['festival'].str.contains(occasion, case=False, na=False) |
                df['season'].str.contains(occasion, case=False, na=False)
            ]
        
        # Sort by price (ascending) and limit
        df = df.sort_values('price').head(limit)
        
        # Convert to list of dicts
        return df.to_dict('records')
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product details by ID
        
        Args:
            product_id: Product ID (e.g., 'PRD001')
            
        Returns:
            Product dictionary or None if not found
        """
        df = self.product_df
        product = df[df['product_id'] == product_id]
        
        if product.empty:
            return None
        
        return product.iloc[0].to_dict()
    
    def get_customer_data(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer information
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer data dictionary or None if not found
        """
        try:
            df = self.customer_df
            customer = df[df['customer_id'] == customer_id]
            
            if customer.empty:
                return None
            
            return customer.iloc[0].to_dict()
        except Exception:
            # If customer data doesn't exist, return default
            return {
                "customer_id": customer_id,
                "customer_name": "Guest",
                "loyalty_points": 0
            }
    
    def get_trending_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get trending products (for demo: highest priced items or specific IDs)
        
        Args:
            limit: Number of trending products to return
            
        Returns:
            List of trending products
        """
        # For demo, return products that are typically trending
        # In production, this would query actual sales/trending data
        trending_ids = ['SKU205', 'SKU101', 'SKU333', 'SKU502', 'SKU401']
        
        df = self.product_df
        trending = df[df['product_id'].isin(trending_ids)].head(limit)
        
        if trending.empty:
            # Fallback: return top priced items
            trending = df.nlargest(limit, 'price')
        
        return trending.to_dict('records')
