"""
Script to add 200 random store keeper transactions to the database
"""
import random
from datetime import datetime, timedelta
from sqlmodel import Session
from database import engine
from models import StoreKeeperTransaction
from crud import store_keeper_transaction_crud

# Store data
STORES = {
    "STR001": "Quest Mall Kolkata",
    "STR002": "South City Mall Kolkata",
    "STR003": "Axis Mall Sector V Kolkata",
    "STR004": "City Centre Salt Lake Kolkata",
    "STR005": "City Centre New Town Kolkata",
    "STR006": "Mani Square Mall Kolkata",
    "STR007": "Acropolis Mall Kolkata",
    "STR008": "Diamond Plaza Mall Kolkata",
    "STR009": "Zudio Ground Floor",
    "STR010": "Zudio Park Street Ground Floor",
    "STR011": "ABFRL Store South City",
    "STR012": "Eden Pavilion Mall Third Floor",
    "STR013": "Mani Square Mall First Floor",
    "STR014": "Acropolis Mall Ground Floor",
    "STR015": "Acropolis Mall First Floor",
    "STR016": "South City Mall Second Floor",
    "STR017": "Quest Mall First Floor",
    "STR018": "Forum Mall Second Floor",
    "STR019": "City Centre Mall Ground Floor",
    "STR020": "Axis Mall Ground Floor",
    "STR021": "Zara Store Park Street",
    "STR022": "H&M Store Park Street",
    "STR023": "Max Store City Centre"
}

# Customer data
CUSTOMERS = {
    "CUST001": "Arujn Bose",
    "CUST002": "Priya Sen",
    "CUST003": "Amit Verma",
    "CUST004": "Neha Gupta",
    "CUST005": "Arjun Das",
    "CUST006": "Sanya Malhotra",
    "CUST007": "Rohit Kapoor",
    "CUST008": "Anjali Mehta",
    "CUST009": "Soumya Roy",
    "CUST010": "Ritika Banerjee",
    "CUST011": "Kunal Mishra",
    "CUST012": "Pooja Nair",
    "CUST013": "Ankit Singh",
    "CUST014": "Nisha Agarwal",
    "CUST015": "Rahul Meena",
    "CUST016": "Ishita Paul",
    "CUST017": "Varun Chatterjee",
    "CUST018": "Tanvi Joshi",
    "CUST019": "Manish Kumar",
    "CUST020": "Reema Saxena",
    "CUST021": "Siddharth Rao",
    "CUST022": "Kavita Iyer",
    "CUST023": "Deepak Yadav",
    "CUST024": "Mehul Jain",
    "CUST025": "Sneha Kulkarni",
    "CUST026": "Abhishek Pandey",
    "CUST027": "Pallavi Deshmukh",
    "CUST028": "Rakesh Sinha",
    "CUST029": "Rajeev Mallick",
    "CUST030": "Swati Ghosh",
    "CUST031": "Nikhil Arora",
    "CUST032": "Monika Reddy",
    "CUST033": "Ayush Tiwari",
    "CUST034": "Shruti Kulkarni",
    "CUST035": "Vikram Bansal",
    "CUST036": "Alisha Khan",
    "CUST037": "Karthik Iyer",
    "CUST038": "Rhea Mukherjee",
    "CUST039": "Sameer Sheikh",
    "CUST040": "Payal Sood",
    "CUST041": "Aditya Sengupta",
    "CUST042": "Sonal Tripathi",
    "CUST043": "Harsh Vardhan",
    "CUST044": "Isha Dutta",
    "CUST045": "Pranav Kulshreshtha",
    "CUST046": "Madhuri Patil",
    "CUST047": "Aakash Choudhary",
    "CUST048": "Priyanka Menon",
    "CUST049": "Rahul Sharma",
    "CUST050": "Ananya Dey",
    "CUST051": "Vishal Sharma",
    "CUST052": "Lakshmi Reddy",
    "CUST053": "Rajesh Kumar",
    "CUST054": "Divya Sharma",
    "CUST055": "Suresh Patel",
    "CUST056": "Preeti Agarwal",
    "CUST057": "Ashok Reddy",
    "CUST058": "Sunita Patel",
    "CUST059": "Ramesh Singh",
    "CUST060": "Kavya Nair",
    "CUST061": "Sandeep Jain",
    "CUST062": "Rekha Gupta",
    "CUST063": "Manoj Gupta",
    "CUST064": "Meena Iyer",
    "CUST065": "Ravi Nair",
    "CUST066": "Shweta Singh",
    "CUST067": "Prakash Iyer",
    "CUST068": "Deepa Kumar",
    "CUST069": "Anil Desai",
    "CUST070": "Anjana Menon",
    "CUST071": "Vinod Pillai",
    "CUST072": "Vidya Deshmukh",
    "CUST073": "Naveen Rao",
    "CUST074": "Gayatri Rao",
    "CUST075": "Gopal Krishna",
    "CUST076": "Savita Joshi",
    "CUST077": "Sanjay Menon",
    "CUST078": "Urmila Bansal",
    "CUST079": "Dinesh Kulkarni",
    "CUST080": "Radha Mishra",
    "CUST081": "Nishant Verma",
    "CUST082": "Tanisha Bose",
    "CUST083": "Rohan Kapadia",
    "CUST084": "Simran Kaur",
    "CUST085": "Aryan Chatterjee",
    "CUST086": "Prachi Desai",
    "CUST087": "Yash Mehta",
    "CUST088": "Diya Agarwal",
    "CUST089": "Karan Singh",
    "CUST090": "Riya Kapoor",
    "CUST091": "Aditya Kumar",
    "CUST092": "Shreya Reddy",
    "CUST093": "Varun Malhotra",
    "CUST094": "Anushka Singh",
    "CUST095": "Arnav Gupta",
    "CUST096": "Ishita Sharma",
    "CUST097": "Siddharth Joshi",
    "CUST098": "Ananya Roy",
    "CUST099": "Aarav Nair",
    "CUST100": "Meera Patel",
    "CUST101": "Kabir Shah",
    "CUST102": "Tanya Menon"
}

# Product data
PRODUCTS = {
    "PRD001": "Being Human Hoodie",
    "PRD002": "Flying Machine Shorts",
    "PRD003": "John Players Kurta",
    "PRD004": "Louis Philippe Shirt",
    "PRD005": "Arrow Jeans",
    "PRD006": "Tommy Hilfiger Sweater",
    "PRD007": "Woodland Boots",
    "PRD008": "Levis Leather Jacket",
    "PRD009": "Fastrack Watch",
    "PRD010": "Spykar Denim",
    "PRD011": "Adidas Track Pants",
    "PRD012": "Zara Casual Top",
    "PRD013": "Nike Running Shoes",
    "PRD014": "Biba Kurti Set",
    "PRD015": "US Polo Shirt",
    "PRD016": "Allen Solly Dress",
    "PRD017": "Puma Sports Shoes",
    "PRD018": "Global Desi Kurti",
    "PRD019": "HRX Gym Jacket",
    "PRD020": "Max Long Dress",
    "PRD021": "Peter England Trousers",
    "PRD022": "Only Denim Jacket",
    "PRD023": "Reebok Sportswear",
    "PRD024": "H&M Casual Shirt",
    "PRD025": "Calvin Klein Jeans",
    "PRD026": "Lee Classic Tee",
    "PRD027": "Superdry Windcheater",
    "PRD028": "Gap Cotton Shirt",
    "PRD029": "Oxemberg Formal Pants",
    "PRD030": "Monte Carlo Sweater",
    "PRD031": "Fossil Leather Belt",
    "PRD032": "Hrx Training Tee",
    "PRD033": "Van Heusen Formal Shirt",
    "PRD034": "Allen Solly Chinos",
    "PRD035": "Reebok Gym Shorts",
    "PRD036": "Nautica Polo",
    "PRD037": "Pepe Jeans Denim",
    "PRD038": "United Colors Hoodie",
    "PRD039": "Tom Tailor Denim Jacket",
    "PRD040": "Wrangler Casual Shirt",
    "PRD041": "US Polo Polo Shirt",
    "PRD042": "Arrow Formal Belt",
    "PRD043": "Lee Denim Jacket",
    "PRD044": "Peter England Sweatshirt",
    "PRD045": "Gap Denim Shorts",
    "PRD046": "Calvin Klein Trousers",
    "PRD047": "Nike Sports Tee",
    "PRD048": "Adidas Running Shoes",
    "PRD049": "Biba Anarkali Set",
    "PRD050": "Global Desi Maxi Kurta",
    "PRD051": "Only Floral Dress",
    "PRD052": "Levi's Classic Jeans",
    "PRD053": "Max Solid Shirt",
    "PRD054": "Zara Knit Top",
    "PRD055": "Puma Sports Hoodie",
    "PRD056": "W Global Women Kurti",
    "PRD057": "AND Floral Maxi Dress",
    "PRD058": "Biba Printed Anarkali",
    "PRD059": "Zara Pleated Skirt",
    "PRD060": "H&M Women Crop Top",
    "PRD061": "Global Desi Palazzo Pants",
    "PRD062": "Only Women Denim Jacket",
    "PRD063": "Forever New Party Dress",
    "PRD064": "Catwalk Women Heels",
    "PRD065": "Baggit Ladies Handbag",
    "PRD066": "Libas Cotton Kurta Set",
    "PRD067": "Nykaa Fashion Ethnic Gown"
}

# Price ranges for different product types (in INR)
PRICE_RANGES = {
    "Hoodie": (800, 2500),
    "Shorts": (500, 1500),
    "Kurta": (600, 2000),
    "Shirt": (700, 2500),
    "Jeans": (1000, 3500),
    "Sweater": (900, 2800),
    "Boots": (2000, 5000),
    "Jacket": (1500, 5000),
    "Watch": (1500, 8000),
    "Denim": (1200, 3500),
    "Pants": (800, 2500),
    "Shoes": (1500, 6000),
    "Set": (1500, 4000),
    "Dress": (800, 3500),
    "Sportswear": (600, 2000),
    "Tee": (400, 1200),
    "Windcheater": (1500, 4000),
    "Belt": (500, 2000),
    "Polo": (700, 2200),
    "Chinos": (1000, 3000),
    "Sweatshirt": (800, 2500),
    "Top": (500, 1800),
    "Skirt": (600, 2000),
    "Heels": (1000, 4000),
    "Handbag": (1500, 6000),
    "Gown": (2000, 8000),
    "Anarkali": (1500, 5000),
    "Maxi": (1000, 3500),
    "Palazzo": (600, 1800),
    "Kurti": (500, 1500),
    "default": (500, 3000)
}

# Sample addresses in Kolkata
ADDRESSES = [
    "12 Park Street, Kolkata 700016",
    "45 Salt Lake Sector V, Kolkata 700091",
    "23 Ballygunge, Kolkata 700019",
    "78 Alipore, Kolkata 700027",
    "56 New Alipore, Kolkata 700053",
    "34 Kasba, Kolkata 700042",
    "89 Jadavpur, Kolkata 700032",
    "67 Behala, Kolkata 700034",
    "12 Rajarhat, Kolkata 700135",
    "45 New Town, Kolkata 700156",
    "23 Dum Dum, Kolkata 700030",
    "78 Barasat, Kolkata 700124",
    "56 Howrah, Howrah 711101",
    "34 Baranagar, Kolkata 700036",
    "89 Belgharia, Kolkata 700056",
    "67 South City, Kolkata 700068",
    "12 Garia, Kolkata 700084",
    "45 Tollygunge, Kolkata 700033",
    "23 Lake Gardens, Kolkata 700045",
    "78 Dhakuria, Kolkata 700031"
]

# Sample phone numbers


def generate_phone():
    return f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"


def get_price_for_product(product_name):
    """Get price based on product type"""
    for key, price_range in PRICE_RANGES.items():
        if key.lower() in product_name.lower():
            return random.randint(*price_range)
    return random.randint(*PRICE_RANGES["default"])


def generate_random_date():
    """Generate a random date within the last 6 months"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    random_days = random.randint(0, 180)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime("%m/%d/%Y")


def add_transactions(count=200):
    """Add specified number of random transactions"""
    with Session(engine) as session:
        added_count = 0
        failed_count = 0

        # Get the current max ID to avoid conflicts
        existing_transactions = store_keeper_transaction_crud.get_all(
            session, skip=0, limit=10000)
        max_id = max([t.id for t in existing_transactions]
                     ) if existing_transactions else 0

        for i in range(count):
            try:
                # Random selection
                store_id = random.choice(list(STORES.keys()))
                store_name = STORES[store_id]
                customer_id = random.choice(list(CUSTOMERS.keys()))
                customer_name = CUSTOMERS[customer_id]
                product_id = random.choice(list(PRODUCTS.keys()))
                product_name = PRODUCTS[product_id]

                # Generate transaction data
                qty = random.randint(1, 5)
                price = get_price_for_product(product_name)
                amount = price * qty
                mode = "Offline"
                status = random.choice(
                    ["Complete", "Complete", "Complete", "Pending"])  # More complete
                date = generate_random_date()
                address = random.choice(ADDRESSES)
                phone = generate_phone()

                # Create transaction
                transaction = StoreKeeperTransaction(
                    id=max_id + i + 1,
                    customer_id=customer_id,
                    product_id=product_id,
                    date=date,
                    user_name=customer_name,
                    product=product_name,
                    qty=qty,
                    mode=mode,
                    store_name=store_name,
                    store_id=store_id,
                    status=status,
                    amount=amount,
                    address=address,
                    phone=phone
                )

                # Add to database
                store_keeper_transaction_crud.create(session, transaction)
                added_count += 1

                if (added_count) % 50 == 0:
                    print(f"Added {added_count} transactions...")

            except Exception as e:
                failed_count += 1
                print(f"Error adding transaction {i+1}: {e}")
                continue

        print(f"\n✅ Successfully added {added_count} transactions")
        if failed_count > 0:
            print(f"⚠️  Failed to add {failed_count} transactions")


if __name__ == "__main__":
    print("Starting to add 200 store keeper transactions...")
    add_transactions(200)
    print("Done!")
