"""
Script to update store names and addresses in the stores table
"""
from database import get_db_session
from models import Store
from sqlmodel import select

# Data to update
store_data = [
    {
        "store_name": "Quest Mall Kolkata",
        "address": "Quest Mall, 33, Beck Bagan Row, Park Circus, Ballygunge, Kolkata, West Bengal 700017"
    },
    {
        "store_name": "South City Mall Kolkata",
        "address": "South City Mall, 375, Prince Anwar Shah Rd, South City Complex, Jadavpur, Kolkata, West Bengal 700068"
    },
    {
        "store_name": "Axis Mall Sector V Kolkata",
        "address": "Axis Mall, Major Arterial Road(South-East), CF Block(Newtown), Action Area 1C, Newtown, New Town, West Bengal 700107"
    },
    {
        "store_name": "City Centre Salt Lake Kolkata",
        "address": "City Centre Salt Lake, DC Block, Sector 1, Bidhannagar, Kolkata, West Bengal 700064"
    },
    {
        "store_name": "City Centre New Town Kolkata",
        "address": "City Centre New Town, Ground Floor, Service Rd, AA II, Action Area IID, Rajarhat, New Town, West Bengal 700161"
    },
    {
        "store_name": "Mani Square Mall Kolkata",
        "address": "Mani Square, 164/1 Maniktala Main Road, Eastern Metropolitan Bypass, Kolkata, West Bengal 700054"
    },
    {
        "store_name": "Acropolis Mall Kolkata",
        "address": "Acropolis Mall, Sector 1, 1858/1, Rajdanga Main Rd, East Kolkata Twp, Kolkata, West Bengal 700107"
    },
    {
        "store_name": "Diamond Plaza Mall Kolkata",
        "address": "Diamond Plaza, Ward Number 23, Nagerbazar, Kamardanga, Kolkata, West Bengal 700055"
    },
    {
        "store_name": "Zudio Ground Floor",
        "address": "Zudio - Gariahat, Kolkata, 171 A, Rash Behari Ave, Gariahat Market, Ekdalia, Ballygunge, Kolkata, West Bengal 700019"
    },
    {
        "store_name": "Zudio Park Street Ground Floor",
        "address": "Zudio - Bangur Bfl Estate, Kolkata, 77 1, Park St, Park Street area, Kolkata, West Bengal 700016"
    },
    {
        "store_name": "Pantaloons (South City Mall, Kolkata)",
        "address": "Pantaloons (South City Mall, Kolkata), Shop No 375, Prince Anwar Shah Rd, South City Complex, Jadavpur, Located, Kolkata, West Bengal 700068"
    },
    {
        "store_name": "Eden Pavilion Mall Third Floor",
        "address": "Mani Square, 164/1 Maniktala Main Road, Eastern Metropolitan Bypass, Kolkata, West Bengal 700054"
    },
    {
        "store_name": "Mani Square Mall First Floor",
        "address": "Mani Square, 164/1 Maniktala Main Road, Eastern Metropolitan Bypass, Kolkata, West Bengal 700054"
    },
    {
        "store_name": "Acropolis Mall Ground Floor",
        "address": "Acropolis Mall, Sector 1, 1858/1, Rajdanga Main Rd, East Kolkata Twp, Kolkata, West Bengal 700107"
    },
    {
        "store_name": "Acropolis Mall First Floor",
        "address": "Cinepolis Acropolis Mall, 3rd Floor, ACROPOLIS MALL, CINEPOLIS INDIA PVT LTD, 1858, Rajdanga Main Rd, beside GEETANJALI STADIUM, Shantipally, Sector B, East Kolkata Twp, Kolkata, West Bengal 700107"
    },
    {
        "store_name": "South City Mall Second Floor",
        "address": "South City Mall, 375, Prince Anwar Shah Rd, South City Complex, Jadavpur, Kolkata, West Bengal 700068"
    },
    {
        "store_name": "Quest Mall First Floor",
        "address": "Quest Mall, 33, Beck Bagan Row, Park Circus, Ballygunge, Kolkata, West Bengal 700017"
    },
    {
        "store_name": "Forum Mall Second Floor",
        "address": "Forum Courtyard Mall, 10/3, Elgin Rd, Sreepally, Bhowanipore, Kolkata, West Bengal 700020"
    },
    {
        "store_name": "City Centre Mall Ground Floor",
        "address": "City Centre Salt Lake, DC Block, Sector 1, Bidhannagar, Kolkata, West Bengal 700064"
    },
    {
        "store_name": "Axis Mall Ground Floor",
        "address": "Axis Mall, Major Arterial Road(South-East), CF Block(Newtown), Action Area 1C, Newtown, New Town, West Bengal 700107"
    },
    {
        "store_name": "Zara Store Park Street",
        "address": "Zara Garments, Shop No. 1011A, 1, Ho Chi Minh Sarani, Metro Shopping Centre, Kankaria Estates, Park Street area, Kolkata, West Bengal 700071"
    },
    {
        "store_name": "H&M Store Park Street",
        "address": "H&M, 5A, Wood Burn Rd, Sreepally, Bhowanipore, Kolkata, West Bengal 700020"
    },
    {
        "store_name": "Max Store City Centre",
        "address": "Max, City Centre, Salt Lake, DC Block, Sector 1, Bidhannagar, Kolkata, West Bengal 700064"
    }
]


def update_stores():
    """Update store names and addresses in the database"""
    session = get_db_session()

    try:
        # Get all stores ordered by store_id
        statement = select(Store).order_by(Store.store_id)
        stores = session.exec(statement).all()

        print(f"Found {len(stores)} stores in database")
        print(f"Have {len(store_data)} updates to apply\n")

        if len(stores) < len(store_data):
            print(
                f"WARNING: Database has fewer stores ({len(stores)}) than update data ({len(store_data)})")
            print("Will update only the available stores\n")

        # Update each store
        updates_made = 0
        for i, store in enumerate(stores):
            if i < len(store_data):
                old_name = store.store_name
                old_address = store.address

                store.store_name = store_data[i]["store_name"]
                store.address = store_data[i]["address"]

                print(f"Store {store.store_id}:")
                print(f"  Name: {old_name} -> {store.store_name}")
                print(
                    f"  Address: {old_address[:50]}... -> {store.address[:50]}...")
                print()

                updates_made += 1

        # Commit changes
        session.commit()
        print(f"\n✓ Successfully updated {updates_made} stores!")

        # Display updated stores
        print("\n=== Updated Stores ===")
        statement = select(Store).order_by(Store.store_id)
        updated_stores = session.exec(statement).all()
        for store in updated_stores:
            print(f"\n{store.store_id}: {store.store_name}")
            print(f"  Address: {store.address}")

    except Exception as e:
        session.rollback()
        print(f"Error updating stores: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=== Updating Store Data ===\n")
    update_stores()
