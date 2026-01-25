"""
Loyalty Tools - Manage loyalty points and rewards
"""

import pandas as pd
import os
from typing import Dict, Any, List
from datetime import datetime


class LoyaltyTools:
    """Tools for loyalty program management"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self._customer_df = None
        
    @property
    def customer_df(self) -> pd.DataFrame:
        """Lazy load customer data"""
        if self._customer_df is None:
            csv_path = os.path.join(self.data_dir, "customer_data.csv")
            try:
                self._customer_df = pd.read_csv(csv_path)
            except:
                # Create empty dataframe if file doesn't exist
                self._customer_df = pd.DataFrame(columns=['customer_id', 'customer_name', 'loyalty_points'])
        return self._customer_df
    
    def process_loyalty(
        self,
        customer_id: str,
        order_amount: float,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Process loyalty points for an order
        
        Args:
            customer_id: Customer ID
            order_amount: Order amount
            order_id: Order ID
            
        Returns:
            Loyalty processing result
        """
        # Calculate points: 1 point per ₹10 spent
        points_earned = int(order_amount / 10)
        
        # Get current loyalty points
        try:
            customer = self.customer_df[self.customer_df['customer_id'] == customer_id]
            if not customer.empty:
                current_points = int(customer.iloc[0].get('loyalty_points', 0))
            else:
                current_points = 0
        except:
            current_points = 0
        
        total_points = current_points + points_earned
        
        # Check for available coupons based on tier
        coupons = self._get_available_coupons(total_points)
        
        # Determine tier
        tier = self._get_loyalty_tier(total_points)
        
        return {
            "customer_id": customer_id,
            "order_id": order_id,
            "points_earned": points_earned,
            "total_points": total_points,
            "tier": tier,
            "available_coupons": coupons,
            "processed_at": datetime.now().isoformat()
        }
    
    def _get_loyalty_tier(self, points: int) -> str:
        """Determine loyalty tier based on points"""
        if points >= 1000:
            return "Gold"
        elif points >= 500:
            return "Silver"
        else:
            return "Bronze"
    
    def _get_available_coupons(self, points: int) -> List[Dict[str, Any]]:
        """Get available coupons based on points"""
        coupons = []
        
        # Demo coupons
        if points >= 100:
            coupons.append({
                "code": "FIRST10",
                "description": "10% discount on next purchase",
                "min_amount": 1000,
                "discount_percent": 10
            })
        
        if points >= 500:
            coupons.append({
                "code": "FREESHIP",
                "description": "Free delivery on next order",
                "min_amount": 0,
                "discount_percent": 0
            })
        
        return coupons
    
    def get_customer_loyalty_info(self, customer_id: str) -> Dict[str, Any]:
        """
        Get complete loyalty information for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Loyalty information
        """
        try:
            customer = self.customer_df[self.customer_df['customer_id'] == customer_id]
            if not customer.empty:
                points = int(customer.iloc[0].get('loyalty_points', 0))
            else:
                points = 0
        except:
            points = 0
        
        tier = self._get_loyalty_tier(points)
        coupons = self._get_available_coupons(points)
        
        return {
            "customer_id": customer_id,
            "loyalty_points": points,
            "tier": tier,
            "available_coupons": coupons
        }
    
    def redeem_points(
        self,
        customer_id: str,
        points_to_redeem: int
    ) -> Dict[str, Any]:
        """
        Redeem loyalty points
        
        Args:
            customer_id: Customer ID
            points_to_redeem: Points to redeem
            
        Returns:
            Redemption result
        """
        customer_info = self.get_customer_loyalty_info(customer_id)
        current_points = customer_info['loyalty_points']
        
        if points_to_redeem > current_points:
            return {
                "success": False,
                "message": "Insufficient loyalty points",
                "available_points": current_points
            }
        
        # Calculate discount value: 1 point = ₹1
        discount_value = points_to_redeem
        new_balance = current_points - points_to_redeem
        
        return {
            "success": True,
            "points_redeemed": points_to_redeem,
            "discount_value": discount_value,
            "new_balance": new_balance,
            "redeemed_at": datetime.now().isoformat()
        }
