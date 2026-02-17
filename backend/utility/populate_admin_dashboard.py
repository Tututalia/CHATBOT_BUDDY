"""
Script to populate admin_dashboard_data table with sample data
"""
from database import get_db_session
from models import AdminDashboardData
from datetime import datetime, timedelta
import random

# Customer names
customer_names = [
    "Arujn Bose", "Priya Sen", "Amit Verma", "Neha Gupta", "Arjun Das",
    "Sanya Malhotra", "Rohit Kapoor", "Anjali Mehta", "Soumya Roy", "Ritika Banerjee",
    "Kunal Mishra", "Pooja Nair", "Ankit Singh", "Nisha Agarwal", "Rahul Meena",
    "Ishita Paul", "Varun Chatterjee", "Tanvi Joshi", "Manish Kumar", "Reema Saxena",
    "Siddharth Rao", "Kavita Iyer", "Deepak Yadav", "Mehul Jain", "Sneha Kulkarni",
    "Abhishek Pandey", "Pallavi Deshmukh", "Rakesh Sinha", "Rajeev Mallick", "Swati Ghosh",
    "Nikhil Arora", "Monika Reddy", "Ayush Tiwari", "Shruti Kulkarni", "Vikram Bansal",
    "Alisha Khan", "Karthik Iyer", "Rhea Mukherjee", "Sameer Sheikh", "Payal Sood",
    "Aditya Sengupta", "Sonal Tripathi", "Harsh Vardhan", "Isha Dutta", "Pranav Kulshreshtha",
    "Madhuri Patil", "Aakash Choudhary", "Priyanka Menon", "Rahul Sharma", "Ananya Dey",
    "Vishal Sharma", "Lakshmi Reddy", "Rajesh Kumar", "Divya Sharma", "Suresh Patel",
    "Preeti Agarwal", "Ashok Reddy", "Sunita Patel", "Ramesh Singh", "Kavya Nair",
    "Sandeep Jain", "Rekha Gupta", "Manoj Gupta", "Meena Iyer", "Ravi Nair",
    "Shweta Singh", "Prakash Iyer", "Deepa Kumar", "Anil Desai", "Anjana Menon",
    "Vinod Pillai", "Vidya Deshmukh", "Naveen Rao", "Gayatri Rao", "Gopal Krishna",
    "Savita Joshi", "Sanjay Menon", "Urmila Bansal", "Dinesh Kulkarni", "Radha Mishra",
    "Nishant Verma", "Tanisha Bose", "Rohan Kapadia", "Simran Kaur", "Aryan Chatterjee",
    "Prachi Desai", "Yash Mehta", "Diya Agarwal", "Karan Singh", "Riya Kapoor",
    "Aditya Kumar", "Shreya Reddy", "Varun Malhotra", "Anushka Singh", "Arnav Gupta",
    "Ishita Sharma", "Siddharth Joshi", "Ananya Roy", "Aarav Nair", "Meera Patel",
    "Kabir Shah", "Tanya Menon"
]

# Addresses
addresses = [
    "12 Lake Road Kolkata", "88 Park Street Kolkata", "45 MG Road Bengaluru",
    "22 Civil Lines Delhi", "77 Salt Lake Kolkata", "19 Sector 15 Gurgaon",
    "88 Lajpat Nagar Delhi", "42 Satellite Road Ahmedabad", "63 New Town Kolkata",
    "11 Gariahat Road Kolkata", "54 Indiranagar Bengaluru", "19 Vyttila Kochi",
    "72 Gomti Nagar Lucknow", "33 MI Road Jaipur", "41 Vijay Nagar Indore",
    "18 Ballygunge Kolkata", "66 New Alipore Kolkata", "27 Kothrud Pune",
    "90 Ashok Nagar Ranchi", "14 Arera Colony Bhopal", "21 Whitefield Bengaluru",
    "9 Adyar Chennai", "55 Sector 62 Noida", "73 C Scheme Jaipur",
    "18 Karve Nagar Pune", "64 Kankarbagh Patna", "29 Baner Road Pune",
    "84 Kankarbagh Patna", "36 Lake Town Kolkata", "91 Behala Kolkata",
    "15 Rohini Sector 9 Delhi", "44 Jubilee Hills Hyderabad", "7 MP Nagar Bhopal",
    "31 Wakad Pune", "12 Model Town Ludhiana", "88 Jogeshwari Mumbai",
    "27 Velachery Chennai", "10 Ballygunge Kolkata", "22 Andheri West Mumbai",
    "16 Sector 20 Panchkula", "19 Golf Green Kolkata", "50 Alambagh Lucknow",
    "8 Rajendra Nagar Patna", "6 Ultadanga Kolkata", "41 Lashkar Gwalior",
    "29 Hadapsar Pune", "17 Civil Lines Aligarh", "66 Panampilly Nagar Kochi",
    "23 Malviya Nagar Jaipur", "9 Kestopur Kolkata", "34 Hitech City Hyderabad",
    "56 Anna Nagar Chennai", "78 Koramangala Bengaluru", "90 Banjara Hills Hyderabad",
    "12 T Nagar Chennai", "45 Jayanagar Bengaluru", "23 Malleshwaram Bengaluru",
    "67 Guindy Chennai", "89 Madhapur Hyderabad", "11 Indiranagar Bengaluru",
    "33 Velachery Chennai", "55 Jubilee Hills Hyderabad", "77 Paldi Ahmedabad",
    "99 Satellite Ahmedabad", "22 Vastrapur Ahmedabad", "44 Navrangpura Ahmedabad",
    "66 Maninagar Ahmedabad", "88 Bodakdev Ahmedabad", "13 Civil Lines Jaipur",
    "35 Mansarovar Jaipur", "57 Vaishali Nagar Jaipur", "79 Raja Park Jaipur",
    "14 Hazratganj Lucknow", "36 Gomti Nagar Lucknow", "58 Alambagh Lucknow",
    "80 Indira Nagar Lucknow", "15 Boring Road Patna", "37 Kankarbagh Patna",
    "59 Fraser Road Patna", "81 Rajendra Nagar Patna", "43 Malviya Nagar Delhi",
    "28 Sector 18 Noida", "91 Linking Road Mumbai", "66 Model Town Chandigarh",
    "52 Ballygunge Kolkata", "34 SG Highway Ahmedabad", "18 Borivali Mumbai",
    "72 Koramangala Bengaluru", "45 Sector 29 Gurgaon", "19 Lajpat Nagar Delhi",
    "83 Andheri East Mumbai", "27 Banjara Hills Hyderabad", "61 Greater Kailash Delhi",
    "54 Jubilee Hills Hyderabad", "39 Vasant Kunj Delhi", "24 Whitefield Bengaluru",
    "88 Powai Mumbai", "77 Salt Lake Kolkata", "45 Indiranagar Bengaluru",
    "92 Navrangpura Ahmedabad", "33 Marine Drive Mumbai", "56 Velachery Chennai"
]

# Phone numbers
phones = [
    "9876543210", "9123456789", "9012345678", "9988776655", "9090909090",
    "9345678901", "9567890123", "9789012345", "9890123456", "9654321098",
    "9812345678", "9876501234", "9123409876", "9765432109", "9654321987",
    "9988123456", "9345609871", "9898765432", "9567012345", "9753102468",
    "9871203456", "9823456701", "9456789012", "9765012349", "9887654321",
    "9312456708", "9798456123", "9654789012", "9876540123", "9765432198",
    "9811122233", "9877098765", "9123450098", "9898981234", "9001122334",
    "9345612345", "9823001122", "9765430012", "9876509876", "9123987654",
    "9810098765", "9098765432", "9871234509", "9345672211", "9786543210",
    "9867543201", "9911223344", "9845012399", "9988776601", "9876500112",
    "9230641255", "9553234612", "9460742737", "9399735852", "9691319790",
    "9148831176", "9198897368", "9144708570", "9705446496", "9774420365",
    "9562492664", "9272956752", "9510491922", "9017140457", "9540476922",
    "9075379120", "9653729135", "9631099282", "9616661739", "9777748622",
    "9291184464", "9050851115", "9640837759", "9475865391", "9006807937",
    "9541311195", "9119169645", "9024221299", "9094964642", "9235018898",
    "9876512340", "9123498765", "9876543201", "9988123478", "9345612389",
    "9765432187", "9812345690", "9901234567", "9123456780", "9988776655",
    "9876501234", "9345678912", "9765432190", "9123450987", "9876549876",
    "9988012345", "9345609876", "9765490123", "9123456098", "9876523456",
    "9988654321", "9345612309"
]

# Store names
store_names = [
    "Quest Mall, Kolkata", "South City Mall, Kolkata", "Axis Mall, Sector V, Kolkata",
    "City Centre, Salt Lake, Kolkata", "City Centre, New Town, Kolkata", "Mani Square Mall, Kolkata",
    "Acropolis Mall, Kolkata", "Diamond Plaza Mall, Kolkata", "Zudio, Ground Floor",
    "Zudio Park Street, Ground Floor", "ABFRL Store, South City", "Eden Pavilion Mall, Third Floor",
    "Mani Square Mall, First Floor", "Acropolis Mall, Ground Floor", "Acropolis Mall, First Floor",
    "South City Mall, Second Floor", "Quest Mall, First Floor", "Forum Mall, Second Floor",
    "City Centre Mall, Ground Floor", "Axis Mall, Ground Floor", "Zara Store, Park Street",
    "H&M Store, Park Street", "Max Store, City Centre"
]

# Products and prices
products_prices = [
    ("Being Human Hoodie", 1999), ("Flying Machine Shorts",
                                   899), ("John Players Kurta", 1299),
    ("Louis Philippe Shirt", 2199), ("Arrow Jeans",
                                     1599), ("Tommy Hilfiger Sweater", 2999),
    ("Woodland Boots", 3799), ("Levis Leather Jacket", 5999), ("Fastrack Watch", 1499),
    ("Spykar Denim", 1699), ("Adidas Track Pants", 2499), ("Zara Casual Top", 1999),
    ("Nike Running Shoes", 5499), ("Biba Kurti Set", 3299), ("US Polo Shirt", 2799),
    ("Allen Solly Dress", 3499), ("Puma Sports Shoes",
                                  4999), ("Global Desi Kurti", 2599),
    ("HRX Gym Jacket", 3999), ("Max Long Dress",
                               2199), ("Peter England Trousers", 2999),
    ("Only Denim Jacket", 4299), ("Reebok Sportswear",
                                  2199), ("H&M Casual Shirt", 1899),
    ("Calvin Klein Jeans", 4599), ("Lee Classic Tee",
                                   799), ("Superdry Windcheater", 3499),
    ("Gap Cotton Shirt", 1599), ("Oxemberg Formal Pants",
                                 2199), ("Monte Carlo Sweater", 1899),
    ("Fossil Leather Belt", 699), ("Hrx Training Tee",
                                   999), ("Van Heusen Formal Shirt", 2499),
    ("Allen Solly Chinos", 2199), ("Reebok Gym Shorts", 799), ("Nautica Polo", 1299),
    ("Pepe Jeans Denim", 2899), ("United Colors Hoodie",
                                 1799), ("Tom Tailor Denim Jacket", 3299),
    ("Wrangler Casual Shirt", 1399), ("US Polo Polo Shirt",
                                      1799), ("Arrow Formal Belt", 599),
    ("Lee Denim Jacket", 2699), ("Peter England Sweatshirt",
                                 1599), ("Gap Denim Shorts", 999),
    ("Calvin Klein Trousers", 3799), ("Nike Sports Tee",
                                      1299), ("Adidas Running Shoes", 4499),
    ("Biba Anarkali Set", 3599), ("Global Desi Maxi Kurta",
                                  2799), ("Only Floral Dress", 2399),
    ("Levi's Classic Jeans", 3199), ("Max Solid Shirt", 1299), ("Zara Knit Top", 1999),
    ("Puma Sports Hoodie", 2199), ("W Global Women Kurti",
                                   1899), ("AND Floral Maxi Dress", 2799),
    ("Biba Printed Anarkali", 3999), ("Zara Pleated Skirt",
                                      1999), ("H&M Women Crop Top", 1499),
    ("Global Desi Palazzo Pants", 2199), ("Only Women Denim Jacket",
                                          3299), ("Forever New Party Dress", 4499),
    ("Catwalk Women Heels", 2599), ("Baggit Ladies Handbag",
                                    2999), ("Libas Cotton Kurta Set", 3499),
    ("Nykaa Fashion Ethnic Gown", 5999)
]


def generate_date_distribution():
    """Generate dates distributed across last 7 days, last month, and older"""
    now = datetime.now()
    dates = []

    # Last 7 days - 60 records (30%)
    for _ in range(60):
        days_ago = random.randint(0, 6)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%m/%d/%Y"))

    # Last month (8-30 days ago) - 80 records (40%)
    for _ in range(80):
        days_ago = random.randint(8, 30)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%m/%d/%Y"))

    # Older than 1 month (31-90 days ago) - 60 records (30%)
    for _ in range(60):
        days_ago = random.randint(31, 90)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%m/%d/%Y"))

    random.shuffle(dates)
    return dates


def populate_admin_dashboard():
    """Populate admin_dashboard_data table with 200 records"""

    print("Starting population of admin_dashboard_data table...")

    dates = generate_date_distribution()
    records = []

    with get_db_session() as session:
        # Get current max ID to avoid conflicts
        from sqlmodel import select, func
        max_id = session.exec(select(func.max(AdminDashboardData.id))).one()
        start_id = (max_id or 0) + 1

        for i in range(200):
            # Select random data
            customer_idx = i % len(customer_names)
            product_idx = random.randint(0, len(products_prices) - 1)

            user_name = customer_names[customer_idx]
            address = addresses[customer_idx]
            phone = phones[customer_idx]

            product, price = products_prices[product_idx]
            quantity = random.randint(3, 12)
            amount = price * quantity

            # 60% offline, 40% online
            mode = "Offline" if random.random() < 0.6 else "Online"

            # For offline, assign random store; for online, use "NA"
            store_name = random.choice(
                store_names) if mode == "Offline" else "NA"

            record = AdminDashboardData(
                id=start_id + i,
                date=dates[i],
                user_name=user_name,
                product=product,
                qty=quantity,
                mode=mode,
                store_name=store_name,
                status="Complete",
                amount=amount,
                address=address,
                phone=phone
            )

            records.append(record)

        # Bulk insert all records
        session.add_all(records)
        session.commit()

        print(
            f"✅ Successfully added {len(records)} records to admin_dashboard_data table")
        print(f"   - ID range: {start_id} to {start_id + len(records) - 1}")
        print(f"   - Date distribution:")
        print(f"     • Last 7 days: ~60 records")
        print(f"     • Last 1 month: ~80 records")
        print(f"     • Older than 1 month: ~60 records")
        print(f"   - Mode distribution:")

        online_count = sum(1 for r in records if r.mode == "Online")
        offline_count = sum(1 for r in records if r.mode == "Offline")
        print(f"     • Online: {online_count} records")
        print(f"     • Offline: {offline_count} records")

        total_amount = sum(r.amount for r in records)
        print(f"   - Total transaction amount: ₹{total_amount:,.2f}")


if __name__ == "__main__":
    try:
        populate_admin_dashboard()
        print("\n✅ Population completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
