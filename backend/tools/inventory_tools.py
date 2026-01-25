"""
Inventory Tools - Check product availability across channels
"""

import pandas as pd
import os
from typing import Dict, Any, List, Optional


class InventoryTools:
    """Tools for checking inventory and availability"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self._product_df = None
        
    @property
    def product_df(self) -> pd.DataFrame:
        """Lazy load product data"""
        if self._product_df is None:
            csv_path = os.path.join(self.data_dir, "product_data.csv")
            self._product_df = pd.read_csv(csv_path)
        return self._product_df
    
    def check_availability(self, product_id: str) -> Dict[str, Any]:
        """
        Check product availability across online and offline channels
        
        Args:
            product_id: Product ID to check
            
        Returns:
            Dictionary with availability information
        """
        product = self.product_df[self.product_df['product_id'] == product_id]
        
        if product.empty:
            return {
                "product_id": product_id,
                "online_available": False,
                "offline_available": False,
                "offline_stores": []
            }
        
        product_data = product.iloc[0]
        
        # Parse offline stores
        offline_stores = []
        if product_data['offline_available'].lower() == 'yes':
            stores_str = product_data['offline_stores']
            if pd.notna(stores_str) and stores_str:
                # Split by semicolon and clean up
                offline_stores = [s.strip() for s in stores_str.split(';') if s.strip()]
        
        return {
            "product_id": product_id,
            "online_available": product_data['online_available'].lower() == 'yes',
            "offline_available": product_data['offline_available'].lower() == 'yes',
            "offline_stores": offline_stores
        }
    
    def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Get full product details
        
        Args:
            product_id: Product ID
            
        Returns:
            Product details dictionary
        """
        product = self.product_df[self.product_df['product_id'] == product_id]
        
        if product.empty:
            return {}
        
        return product.iloc[0].to_dict()
    
    def check_size_availability(
        self,
        product_id: str,
        size: str,
        location: str = None
    ) -> Dict[str, Any]:
        """
        Check if specific size is available
        
        Args:
            product_id: Product ID
            size: Size to check (e.g., '40', 'L', 'M')
            location: Optional location filter
            
        Returns:
            Availability information for the size
        """
        # For demo purposes, simulate size availability
        # In production, this would query actual inventory database
        
        availability = self.check_availability(product_id)
        
        # Simulate size check
        # For demo: sizes are available if product is available
        if availability['online_available']:
            online_stock = 12  # Demo stock level
        else:
            online_stock = 0
        
        # Check offline stores
        store_availability = []
        for store in availability['offline_stores']:
            # Demo: alternate between in-stock and low-stock
            stock = 3 if 'South City' in store or 'Kolkata' in store else 1
            store_availability.append({
                "store": store,
                "stock": stock,
                "available": stock > 0
            })
        
        return {
            "product_id": product_id,
            "size": size,
            "online_stock": online_stock,
            "offline_stores": store_availability
        }
    
    def get_nearby_stores(
        self,
        product_id: str,
        region: str = "Kolkata"
    ) -> List[Dict[str, Any]]:
        """
        Get nearby stores with product availability
        
        Args:
            product_id: Product ID
            region: Region to search (default: Kolkata)
            
        Returns:
            List of nearby stores with availability
        """
        availability = self.check_availability(product_id)
        stores = availability['offline_stores']
        
        # Filter stores by region
        nearby_stores = []
        for store in stores:
            if region.lower() in store.lower() or 'kolkata' in store.lower():
                nearby_stores.append({
                    "name": store,
                    "distance": "2.5 km",  # Demo distance
                    "stock": 3  # Demo stock
                })
        
        return nearby_stores[:3]  # Return top 3
