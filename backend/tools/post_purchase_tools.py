"""
Post Purchase Tools - Handle post-purchase services
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class PostPurchaseTools:
    """Tools for post-purchase services"""
    
    def setup_services(
        self,
        customer_id: str,
        order_id: str,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Setup post-purchase services
        
        Args:
            customer_id: Customer ID
            order_id: Order ID
            product_id: Product ID
            
        Returns:
            Post-purchase service details
        """
        # Enable order tracking
        tracking_enabled = True
        
        # Generate personalized offers
        offers = self._generate_personalized_offers(customer_id, product_id)
        
        # Setup feedback collection (after 7 days)
        feedback_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        return {
            "customer_id": customer_id,
            "order_id": order_id,
            "tracking_enabled": tracking_enabled,
            "personalized_offers": offers,
            "feedback_scheduled": feedback_date,
            "support_available": True,
            "return_policy_days": 30
        }
    
    def _generate_personalized_offers(
        self,
        customer_id: str,
        product_id: str
    ) -> List[Dict[str, Any]]:
        """Generate personalized offers based on purchase"""
        offers = [
            {
                "title": "Free delivery on next order",
                "code": "FREESHIP",
                "valid_until": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            },
            {
                "title": "Refer a friend and earn ₹500",
                "code": "REFER500",
                "valid_until": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
            }
        ]
        
        return offers
    
    def collect_feedback(
        self,
        order_id: str,
        rating: int,
        comments: str = ""
    ) -> Dict[str, Any]:
        """
        Collect customer feedback
        
        Args:
            order_id: Order ID
            rating: Rating (1-5)
            comments: Optional comments
            
        Returns:
            Feedback confirmation
        """
        return {
            "order_id": order_id,
            "rating": rating,
            "comments": comments,
            "submitted_at": datetime.now().isoformat(),
            "reward_points": 50  # Bonus points for feedback
        }
    
    def initiate_return(
        self,
        order_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Initiate return process
        
        Args:
            order_id: Order ID
            reason: Return reason
            
        Returns:
            Return request details
        """
        import uuid
        return_id = f"RET{uuid.uuid4().hex[:6].upper()}"
        
        return {
            "return_id": return_id,
            "order_id": order_id,
            "status": "initiated",
            "reason": reason,
            "pickup_scheduled": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "refund_eta": "7-10 business days",
            "created_at": datetime.now().isoformat()
        }
    
    def get_support_info(self, order_id: str) -> Dict[str, Any]:
        """
        Get customer support information
        
        Args:
            order_id: Order ID
            
        Returns:
            Support contact information
        """
        return {
            "order_id": order_id,
            "support_channels": [
                {
                    "type": "chat",
                    "available": True,
                    "response_time": "< 5 minutes"
                },
                {
                    "type": "phone",
                    "number": "1800-XXX-XXXX",
                    "hours": "9 AM - 9 PM"
                },
                {
                    "type": "email",
                    "address": "support@retaildeepcare.com",
                    "response_time": "24 hours"
                }
            ]
        }
