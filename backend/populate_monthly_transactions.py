"""
Script to populate admin_dashboard_data table with monthly transaction data
Ensures each month has at least 85 online and 67 offline transactions
"""

from database import get_db_session
from models import AdminDashboardData
from sqlmodel import select
import random
from datetime import datetime, timedelta

# Product names from the database
PRODUCTS = [
    "Biba Kurti Set", "Adidas Track Pants", "Global Desi Kurti", "Tommy Hilfiger Sweater",
    "Being Human Hoodie", "Arrow Jeans", "Louis Philippe Shirt", "Flying Machine Shorts",
    "John Players Kurta", "Puma Joggers", "Nike Sneakers", "Levi's Jeans",
    "Reebok T-Shirt", "Peter England Shirt", "Allen Solly Trousers", "Van Heusen Blazer",
    "Raymond Suit", "Park Avenue Formal Shirt", "Blackberrys Pants", "ColorPlus Casual Shirt"
]

# Store names
STORES = [
    "Zudio, Ground Floor", "Eden Pavilion Mall, Third Floor", "Acropolis Mall, Ground Floor",
    "South City Mall", "Quest Mall", "City Centre Salt Lake", "Forum Mall"
]

# Customer names
CUSTOMERS = [
    "Arujn Bose", "Priya Khan", "Rohit Bhandari", "Sonal Das", "Vidya Saxena",
    "Amit Sharma", "Neha Gupta", "Rahul Verma", "Anjali Singh", "Karan Patel",
    "Sneha Reddy", "Vikram Joshi", "Pooja Mehta", "Raj Kumar", "Divya Iyer"
]

# Addresses in Kolkata
ADDRESSES = [
    "128 Main Street, City 8", "36 Main Street, City 16", "89 Main Street, City 9",
    "108 Main Street, City 8", "78 Main Street, City 18", "66 Main Street, City 6",
    "45 Park Street, Kolkata", "23 Salt Lake, Kolkata", "67 Ballygunge, Kolkata",
    "89 New Town, Kolkata", "12 Howrah, Kolkata", "56 Jadavpur, Kolkata"
]

# Phone numbers
PHONES = [
    "555-1128", "555-1036", "555-1089", "555-1108", "555-1078", "555-1066",
    "555-2001", "555-2002", "555-2003", "555-2004", "555-2005", "555-2006"
]


def generate_transactions_for_month(month_name, month_num, year=2025, min_online=85, min_offline=67):
    """Generate transactions for a specific month"""
    transactions = []
    
    # Generate online transactions
    online_count = random.randint(min_online, min_online + 50)
    for i in range(online_count):
        day = random.randint(1, 28)  # Keep it safe for all months
        date_str = f"{month_num}/{day}/{year}"
        
        product = random.choice(PRODUCTS)
        qty = random.randint(1, 3)
        base_price = random.randint(800, 3500)
        amount = base_price * qty
        
        tx = {
            "date": date_str,
            "user_name": random.choice(CUSTOMERS),
            "product": product,
            "qty": qty,
            "mode": "Online",
            "store_name": "NA",
            "status": "Complete",
            "amount": float(amount),
            "address": random.choice(ADDRESSES),
            "phone": random.choice(PHONES)
        }
        transactions.append(tx)
    
    # Generate offline transactions
    offline_count = random.randint(min_offline, min_offline + 40)
    for i in range(offline_count):
        day = random.randint(1, 28)
        date_str = f"{month_num}/{day}/{year}"
        
        product = random.choice(PRODUCTS)
        qty = random.randint(1, 3)
        base_price = random.randint(800, 3500)
        amount = base_price * qty
        
        tx = {
            "date": date_str,
            "user_name": random.choice(CUSTOMERS),
            "product": product,
            "qty": qty,
            "mode": "Offline",
            "store_name": random.choice(STORES),
            "status": "Complete",
            "amount": float(amount),
            "address": random.choice(ADDRESSES),
            "phone": random.choice(PHONES)
        }
        transactions.append(tx)
    
    print(f"Generated {online_count} online and {offline_count} offline transactions for {month_name}")
    return transactions


def main():
    """Main function to populate monthly transaction data"""
    
    # Month mapping
    months = [
        ("Jan", 1), ("Feb", 2), ("Mar", 3), ("Apr", 4),
        ("May", 5), ("Jun", 6), ("Jul", 7), ("Aug", 8),
        ("Sep", 9), ("Oct", 10), ("Nov", 11), ("Dec", 12)
    ]
    
    with get_db_session() as session:
        # Get current max ID
        result = session.exec(select(AdminDashboardData).order_by(AdminDashboardData.id.desc()).limit(1)).first()
        current_max_id = result.id if result else 0
        
        print(f"Current max ID in database: {current_max_id}")
        print(f"\nGenerating transactions for all 12 months...")
        print("=" * 60)
        
        all_transactions = []
        
        # Generate transactions for each month
        for month_name, month_num in months:
            month_transactions = generate_transactions_for_month(month_name, month_num)
            all_transactions.extend(month_transactions)
        
        print("=" * 60)
        print(f"\nTotal transactions generated: {len(all_transactions)}")
        print(f"\nInserting transactions into database...")
        
        # Insert all transactions
        new_id = current_max_id + 1
        for tx_data in all_transactions:
            tx = AdminDashboardData(
                id=new_id,
                date=tx_data["date"],
                user_name=tx_data["user_name"],
                product=tx_data["product"],
                qty=tx_data["qty"],
                mode=tx_data["mode"],
                store_name=tx_data["store_name"],
                status=tx_data["status"],
                amount=tx_data["amount"],
                address=tx_data["address"],
                phone=tx_data["phone"]
            )
            session.add(tx)
            new_id += 1
        
        session.commit()
        print(f"\n✅ Successfully inserted {len(all_transactions)} transactions!")
        print(f"ID range: {current_max_id + 1} to {new_id - 1}")
        
        # Verify the data
        print("\nVerifying monthly distribution...")
        print("=" * 60)
        
        for month_name, month_num in months:
            online_count = session.exec(
                select(AdminDashboardData).where(
                    AdminDashboardData.date.like(f"{month_num}/%/2025"),
                    AdminDashboardData.mode == "Online"
                )
            ).all()
            
            offline_count = session.exec(
                select(AdminDashboardData).where(
                    AdminDashboardData.date.like(f"{month_num}/%/2025"),
                    AdminDashboardData.mode == "Offline"
                )
            ).all()
            
            print(f"{month_name}: Online={len(online_count)}, Offline={len(offline_count)}, Total={len(online_count) + len(offline_count)}")


if __name__ == "__main__":
    main()
