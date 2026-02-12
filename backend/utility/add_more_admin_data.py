"""
Script to add 100 more unique customers and increase offline store transactions
"""
from database import get_db_session
from models import AdminDashboardData
from datetime import datetime, timedelta
import random

# 100 New unique customer names
new_customer_names = [
    "Aakash Sharma", "Bhavna Patel", "Chirag Desai", "Deepika Singh", "Eshan Gupta",
    "Farhan Khan", "Gauri Reddy", "Harsh Mehta", "Ira Joshi", "Jay Kumar",
    "Kavya Shah", "Lakshay Verma", "Manan Agarwal", "Nandini Roy", "Omkar Rao",
    "Preeti Malhotra", "Qadir Ali", "Ruchi Bansal", "Sahil Kapoor", "Tanuja Pillai",
    "Uday Singh", "Vandana Kulkarni", "Wasim Sheikh", "Yashika Bose", "Zara Khan",
    "Amar Thakur", "Bhumi Trivedi", "Chetan Nair", "Divya Iyer", "Ekta Saxena",
    "Farhan Ahmed", "Geeta Choudhary", "Himanshu Das", "Iqbal Hussain", "Jyoti Menon",
    "Kiran Pandey", "Lalit Mishra", "Mohan Patil", "Neeta Jain", "Ojas Tiwari",
    "Pankaj Yadav", "Qasim Malik", "Radha Ghosh", "Sagar Sinha", "Tanu Banerjee",
    "Urvashi Dutta", "Vijay Naik", "Waqar Khan", "Yamini Arora", "Zaheer Abbas",
    "Anmol Bhatia", "Bhavesh Pawar", "Chandni Ahluwalia", "Dhruv Bhatt", "Eklavya Rai",
    "Farah Ansari", "Gaurav Jha", "Hetal Shukla", "Ishaan Chopra", "Jatin Kohli",
    "Komal Solanki", "Lalit Rawal", "Manisha Rana", "Nisha Saini", "Om Prakash",
    "Pooja Rathore", "Qamar Jahan", "Rajat Anand", "Seema Kashyap", "Tarun Bhardwaj",
    "Uma Shankar", "Vinay Dubey", "Waseem Qureshi", "Yuvraj Gill", "Zainab Siddiqui",
    "Aarush Pandya", "Bhumika Chawla", "Chiranjeev Dubey", "Devika Mathur", "Ekta Rawat",
    "Fahad Rizvi", "Gayatri Shetty", "Hardik Thakkar", "Indira Prasad", "Javed Akhtar",
    "Kiara Bhandari", "Lalit Goswami", "Madhav Jain", "Naina Kapadia", "Ojaswi Puri",
    "Pradeep Mahajan", "Qutub Khan", "Rashmi Dalal", "Sameer Patel", "Tina Sethi",
    "Ujjwal Singh", "Vrinda Mehra", "Wasif Ahmed", "Yash Soni", "Zoya Malik"
]

# 100 New unique addresses
new_addresses = [
    "45 Brigade Road Bengaluru", "23 MG Road Mumbai", "67 Park Street Delhi",
    "89 Linking Road Mumbai", "12 Connaught Place Delhi", "34 Anna Salai Chennai",
    "56 Bandra West Mumbai", "78 Jayanagar Bengaluru", "90 Sector 17 Chandigarh",
    "11 Rajpur Road Dehradun", "33 Station Road Jaipur", "55 Mall Road Shimla",
    "77 Civil Lines Allahabad", "99 Hazratganj Lucknow", "22 Park Lane Kolkata",
    "44 Camac Street Kolkata", "66 Russell Street Kolkata", "88 Theatre Road Kolkata",
    "13 Salt Lake City Kolkata", "35 New Town Action Area Kolkata", "57 EM Bypass Kolkata",
    "79 VIP Road Kolkata", "14 Rajarhat Kolkata", "36 Garia Kolkata", "58 Jadavpur Kolkata",
    "80 Tollygunge Kolkata", "15 Alipore Kolkata", "37 Bhowanipore Kolkata", "59 Dharmatala Kolkata",
    "81 Esplanade Kolkata", "16 Howrah Station Road", "38 Shibpur Howrah", "60 Liluah Howrah",
    "82 Belur Howrah", "17 Durgapur City Centre", "39 Asansol Court Road", "61 Siliguri Mall Road",
    "83 Kharagpur Station Road", "18 Burdwan Town", "40 Haldia Township", "62 Malda Bazaar",
    "84 Darjeeling Chowrasta", "19 Medinipur Town", "41 Barasat Station Road", "63 Barrackpore Cantonment",
    "85 Naihati Station Road", "20 Dum Dum Airport", "42 Sealdah Station", "64 Bidhan Nagar Sector 2",
    "86 Kasba Kolkata", "21 Lake Gardens Kolkata", "43 Southern Avenue Kolkata", "65 Ballygunge Circular Road",
    "87 Rashbehari Avenue Kolkata", "24 Hazra Road Kolkata", "46 Lansdowne Road Kolkata", "68 Sarat Bose Road",
    "90 Rash Behari Connector", "25 Gariahat Main Road", "47 Gariahat Crossing", "69 Triangular Park",
    "91 Deshapriya Park", "26 Lake Market Kolkata", "48 Dover Lane Market", "70 Elgin Road Kolkata",
    "92 Rawdon Street Kolkata", "27 Loudon Street Kolkata", "49 Free School Street", "71 Shakespeare Sarani",
    "93 AJC Bose Road Kolkata", "28 Park Circus Kolkata", "50 Beckbagan Kolkata", "72 Tangra Kolkata",
    "94 Topsia Kolkata", "29 Tiljala Kolkata", "51 Entally Kolkata", "73 Beleghata Kolkata",
    "95 Phoolbagan Kolkata", "30 Rajabazar Kolkata", "52 Shyambazar Kolkata", "74 Hatibagan Kolkata",
    "96 Maniktala Kolkata", "31 Ultadanga Main Road", "53 Belgachia Kolkata", "75 Narkeldanga Kolkata",
    "97 Kankurgachi Kolkata", "32 Bidhannagar Road", "54 New Market Area", "76 BBD Bag Kolkata",
    "98 Brabourne Road Kolkata", "100 Princep Street Kolkata", "101 Bentinck Street", "102 Ripon Street Kolkata"
]

# 100 New phone numbers
new_phones = [
    "9234567890", "9345678901", "9456789012", "9567890123", "9678901234",
    "9789012345", "9890123456", "9901234567", "9012345678", "9123456789",
    "9234560123", "9345670234", "9456780345", "9567890456", "9678900567",
    "9789010678", "9890120789", "9901230890", "9012340901", "9123450012",
    "9234561234", "9345672345", "9456783456", "9567894567", "9678905678",
    "9789016789", "9890127890", "9901238901", "9012349012", "9123450123",
    "9234567891", "9345678902", "9456789013", "9567890124", "9678901235",
    "9789012346", "9890123457", "9901234568", "9012345679", "9123456780",
    "9234560124", "9345670235", "9456780346", "9567890457", "9678900568",
    "9789010679", "9890120780", "9901230891", "9012340902", "9123450013",
    "9234561235", "9345672346", "9456783457", "9567894568", "9678905679",
    "9789016780", "9890127891", "9901238902", "9012349013", "9123450124",
    "9234567892", "9345678903", "9456789014", "9567890125", "9678901236",
    "9789012347", "9890123458", "9901234569", "9012345670", "9123456781",
    "9234560125", "9345670236", "9456780347", "9567890458", "9678900569",
    "9789010670", "9890120781", "9901230892", "9012340903", "9123450014",
    "9234561236", "9345672347", "9456783458", "9567894569", "9678905670",
    "9789016781", "9890127892", "9901238903", "9012349014", "9123450125",
    "9234567893", "9345678904", "9456789015", "9567890126", "9678901237",
    "9789012348", "9890123459", "9901234560", "9012345671", "9123456782"
]

# Existing store names plus more variations
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

# Products and prices (same as before)
products_prices = [
    ("Being Human Hoodie", 1999), ("Flying Machine Shorts", 899), ("John Players Kurta", 1299),
    ("Louis Philippe Shirt", 2199), ("Arrow Jeans", 1599), ("Tommy Hilfiger Sweater", 2999),
    ("Woodland Boots", 3799), ("Levis Leather Jacket", 5999), ("Fastrack Watch", 1499),
    ("Spykar Denim", 1699), ("Adidas Track Pants", 2499), ("Zara Casual Top", 1999),
    ("Nike Running Shoes", 5499), ("Biba Kurti Set", 3299), ("US Polo Shirt", 2799),
    ("Allen Solly Dress", 3499), ("Puma Sports Shoes", 4999), ("Global Desi Kurti", 2599),
    ("HRX Gym Jacket", 3999), ("Max Long Dress", 2199), ("Peter England Trousers", 2999),
    ("Only Denim Jacket", 4299), ("Reebok Sportswear", 2199), ("H&M Casual Shirt", 1899),
    ("Calvin Klein Jeans", 4599), ("Lee Classic Tee", 799), ("Superdry Windcheater", 3499),
    ("Gap Cotton Shirt", 1599), ("Oxemberg Formal Pants", 2199), ("Monte Carlo Sweater", 1899),
    ("Fossil Leather Belt", 699), ("Hrx Training Tee", 999), ("Van Heusen Formal Shirt", 2499),
    ("Allen Solly Chinos", 2199), ("Reebok Gym Shorts", 799), ("Nautica Polo", 1299),
    ("Pepe Jeans Denim", 2899), ("United Colors Hoodie", 1799), ("Tom Tailor Denim Jacket", 3299),
    ("Wrangler Casual Shirt", 1399), ("US Polo Polo Shirt", 1799), ("Arrow Formal Belt", 599),
    ("Lee Denim Jacket", 2699), ("Peter England Sweatshirt", 1599), ("Gap Denim Shorts", 999),
    ("Calvin Klein Trousers", 3799), ("Nike Sports Tee", 1299), ("Adidas Running Shoes", 4499),
    ("Biba Anarkali Set", 3599), ("Global Desi Maxi Kurta", 2799), ("Only Floral Dress", 2399),
    ("Levi's Classic Jeans", 3199), ("Max Solid Shirt", 1299), ("Zara Knit Top", 1999),
    ("Puma Sports Hoodie", 2199), ("W Global Women Kurti", 1899), ("AND Floral Maxi Dress", 2799),
    ("Biba Printed Anarkali", 3999), ("Zara Pleated Skirt", 1999), ("H&M Women Crop Top", 1499),
    ("Global Desi Palazzo Pants", 2199), ("Only Women Denim Jacket", 3299), ("Forever New Party Dress", 4499),
    ("Catwalk Women Heels", 2599), ("Baggit Ladies Handbag", 2999), ("Libas Cotton Kurta Set", 3499),
    ("Nykaa Fashion Ethnic Gown", 5999)
]

def generate_date_distribution_new():
    """Generate dates distributed across last 7 days, last month, and older"""
    now = datetime.now()
    dates = []
    
    # Last 7 days - 120 records (30%)
    for _ in range(120):
        days_ago = random.randint(0, 6)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%m/%d/%Y"))
    
    # Last month (8-30 days ago) - 160 records (40%)
    for _ in range(160):
        days_ago = random.randint(8, 30)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%m/%d/%Y"))
    
    # Older than 1 month (31-90 days ago) - 120 records (30%)
    for _ in range(120):
        days_ago = random.randint(31, 90)
        date = now - timedelta(days=days_ago)
        dates.append(date.strftime("%m/%d/%Y"))
    
    random.shuffle(dates)
    return dates

def add_more_data():
    """Add 400 more records with 100 unique customers and increased offline transactions"""
    
    print("Adding more data to admin_dashboard_data table...")
    
    dates = generate_date_distribution_new()
    records = []
    
    with get_db_session() as session:
        # Get current max ID to avoid conflicts
        from sqlmodel import select, func
        max_id = session.exec(select(func.max(AdminDashboardData.id))).one()
        start_id = (max_id or 0) + 1
        
        for i in range(400):
            # Select from new customers (100 unique customers, cycling through them)
            customer_idx = i % len(new_customer_names)
            address_idx = i % len(new_addresses)
            phone_idx = i % len(new_phones)
            product_idx = random.randint(0, len(products_prices) - 1)
            
            user_name = new_customer_names[customer_idx]
            address = new_addresses[address_idx]
            phone = new_phones[phone_idx]
            
            product, price = products_prices[product_idx]
            quantity = random.randint(3, 12)
            amount = price * quantity
            
            # 75% offline, 25% online (increased offline percentage)
            mode = "Offline" if random.random() < 0.75 else "Online"
            
            # For offline, assign random store; for online, use "NA"
            store_name = random.choice(store_names) if mode == "Offline" else "NA"
            
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
        
        print(f"✅ Successfully added {len(records)} more records to admin_dashboard_data table")
        print(f"   - ID range: {start_id} to {start_id + len(records) - 1}")
        print(f"   - Unique customers: {len(new_customer_names)}")
        print(f"   - Date distribution:")
        print(f"     • Last 7 days: ~120 records")
        print(f"     • Last 1 month: ~160 records")
        print(f"     • Older than 1 month: ~120 records")
        print(f"   - Mode distribution:")
        
        online_count = sum(1 for r in records if r.mode == "Online")
        offline_count = sum(1 for r in records if r.mode == "Offline")
        print(f"     • Online: {online_count} records")
        print(f"     • Offline: {offline_count} records")
        
        total_amount = sum(r.amount for r in records)
        print(f"   - Total transaction amount: ₹{total_amount:,.2f}")
        
        # Calculate transactions per store
        store_counts = {}
        for r in records:
            if r.mode == "Offline":
                store_counts[r.store_name] = store_counts.get(r.store_name, 0) + r.qty
        
        print(f"   - Store transactions added:")
        for store, count in sorted(store_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     • {store}: {count} items")

if __name__ == "__main__":
    try:
        add_more_data()
        print("\n✅ Additional data population completed successfully!")
        print("\n📊 Total dataset now contains:")
        print("   - 200 (original) + 400 (new) = 600 total records")
        print("   - 100 original customers + 100 new customers = 200 unique customers")
        print("   - Significantly increased offline store purchase counts")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
