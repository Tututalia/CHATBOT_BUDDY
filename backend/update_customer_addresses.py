"""
Script to update specific customer addresses in the customers table
"""
from database import get_db_session
from models import Customer
from sqlmodel import select

# Data to update
customer_updates = {
    "CUST001": "12 Lake Road, Ballygunge, Kolkata",
    "CUST002": "88 Park Street, Park Street Area, Kolkata",
    "CUST003": "45 Gariahat Road, Gariahat, Kolkata",
    "CUST004": "22 Southern Avenue, Golpark, Kolkata",
    "CUST005": "77 Salt Lake Sector I, Kolkata",
    "CUST006": "19 Salt Lake Sector II, Kolkata",
    "CUST007": "63 New Town Action Area I, Kolkata",
    "CUST008": "11 New Town Action Area II, Kolkata",
    "CUST009": "18 Ballygunge Circular Road, Kolkata",
    "CUST010": "66 New Alipore Road, Kolkata",
    "CUST011": "36 Lake Town Main Road, Kolkata",
    "CUST012": "91 Diamond Harbour Road, Behala, Kolkata",
    "CUST013": "9 Kestopur Main Road, Kolkata",
    "CUST014": "6 Ultadanga Main Road, Kolkata",
    "CUST015": "52 Ballygunge Place, Kolkata",
    "CUST016": "41 Rash Behari Avenue, Kolkata",
    "CUST017": "29 Hazra Road, Kolkata",
    "CUST018": "55 Prince Anwar Shah Road, Kolkata",
    "CUST019": "72 Jadavpur Central Road, Kolkata",
    "CUST020": "14 Tollygunge Circular Road, Kolkata",
    "CUST021": "88 EM Bypass, Kasba, Kolkata",
    "CUST022": "23 Bondel Road, Ballygunge, Kolkata",
    "CUST023": "67 Deshapran Sasmal Road, Kolkata",
    "CUST024": "10 Narkeldanga Main Road, Kolkata",
    "CUST025": "31 APC Road, Shyambazar, Kolkata",
    "CUST026": "44 BT Road, Dunlop, Kolkata",
    "CUST027": "90 Vivekananda Road, Girish Park, Kolkata",
    "CUST028": "18 Lenin Sarani, Bowbazar, Kolkata",
    "CUST029": "77 Chittaranjan Avenue, Kolkata",
    "CUST030": "64 Rabindra Sarani, Burrabazar, Kolkata",
    "CUST031": "15 Strand Road, Fairley Place, Kolkata",
    "CUST032": "22 Jawaharlal Nehru Road, Esplanade, Kolkata",
    "CUST033": "8 Chowringhee Road, Kolkata",
    "CUST034": "59 Shakespeare Sarani, Kolkata",
    "CUST035": "33 Camac Street, Kolkata",
    "CUST036": "71 Park Circus Road, Kolkata",
    "CUST037": "26 Topsia Road, Kolkata",
    "CUST038": "54 Tiljala Road, Kolkata",
    "CUST039": "19 Picnic Garden Road, Kolkata",
    "CUST040": "82 Raja Subodh Chandra Mullick Road, Kolkata",
    "CUST041": "17 Baguiati Road, Kolkata",
    "CUST042": "69 Jessore Road, Dum Dum, Kolkata",
    "CUST043": "28 VIP Road, Kaikhali, Kolkata",
    "CUST044": "91 Ultadanga VIP Road, Kolkata",
    "CUST045": "12 Belgachia Road, Kolkata",
    "CUST046": "34 Cossipore Road, Kolkata",
    "CUST047": "78 Baranagar Road, Kolkata",
    "CUST048": "56 Sinthee More Road, Kolkata",
    "CUST049": "24 Dum Dum Road, Kolkata",
    "CUST050": "11 Beliaghata Main Road, Kolkata",
    "CUST051": "39 Canal South Road, Kolkata",
    "CUST052": "62 Phoolbagan Crossing, Kolkata",
    "CUST053": "85 Maniktala Main Road, Kolkata",
    "CUST054": "14 College Street, Kolkata",
    "CUST055": "92 Amherst Street, Kolkata",
    "CUST056": "27 Brabourne Road, Kolkata",
    "CUST057": "61 NSC Bose Road, Maheshtala, Kolkata",
    "CUST058": "73 MG Road, Kolkata",
    "CUST059": "18 Kidderpore Road, Kolkata",
    "CUST060": "44 Alipore Road, Kolkata",
    "CUST061": "30 Judges Court Road, Alipore, Kolkata",
    "CUST062": "58 Diamond Harbour Road, Kolkata",
    "CUST063": "21 BT Road, Sinthee, Kolkata",
    "CUST064": "90 Southern Avenue, Kolkata",
    "CUST065": "16 Gobra Road, Kolkata",
    "CUST066": "27 Kalighat Road, Kolkata",
    "CUST067": "74 Behala Chowrasta, Kolkata",
    "CUST068": "52 Joka Road, Kolkata",
    "CUST069": "88 Taratala Road, Kolkata",
    "CUST070": "35 Thakurpukur Road, Kolkata",
    "CUST071": "12 Jessore Road, Barasat",
    "CUST072": "45 Taki Road, Barasat",
    "CUST073": "18 NH-12, Kazipara, Barasat",
    "CUST074": "66 Champadali More, Barasat",
    "CUST075": "21 Hridaypur Station Road, Barasat",
    "CUST076": "90 Nabapally, Barasat",
    "CUST077": "34 Madhyamgram Road, Barasat",
    "CUST078": "15 Barasat Station Road, Barasat",
    "CUST079": "58 Kazipara Road, Barasat",
    "CUST080": "11 Banamalipur Road, Barasat",
    "CUST081": "27 Ganganagar Road, Barasat",
    "CUST082": "44 Shibtala Road, Barasat",
    "CUST083": "62 Barasat–Barrackpore Road, Barasat",
    "CUST084": "19 Colony More, Barasat",
    "CUST085": "73 Ashokenagar Road, Barasat",
    "CUST086": "31 Nabapally Main Road, Barasat",
    "CUST087": "88 Champadali Road, Barasat",
    "CUST088": "10 KNC Road, Barasat",
    "CUST089": "54 Hridaypur More, Barasat",
    "CUST090": "23 Barasat Court Road, Barasat",
    "CUST091": "67 East Kazipara, Barasat",
    "CUST092": "39 West Kazipara, Barasat",
    "CUST093": "14 Helabattala Road, Barasat",
    "CUST094": "70 Banamalipur More, Barasat",
    "CUST095": "26 Barasat–Basirhat Road, Barasat",
    "CUST096": "91 Madhyamgram Chowmatha Road, Barasat",
    "CUST097": "18 Vivekananda Road, Barasat",
    "CUST098": "42 Champadali Railway Gate, Barasat",
    "CUST099": "57 Barasat Market Road, Barasat",
    "CUST100": "33 Nabapally Extension, Barasat",
    "CUST101": "64 Hridaypur Extension Road, Barasat",
    "CUST102": "29 Kazipara Extension Road, Barasat"
}


def update_customer_addresses():
    """Update customer addresses in the database"""
    session = get_db_session()

    try:
        print("=== Updating Customer Addresses ===\n")

        updates_made = 0
        for customer_id, new_address in customer_updates.items():
            # Find the customer
            statement = select(Customer).where(
                Customer.customer_id == customer_id)
            customer = session.exec(statement).first()

            if customer:
                old_address = customer.address
                customer.address = new_address

                print(f"Customer {customer_id} ({customer.customer_name}):")
                print(f"  Old: {old_address}")
                print(f"  New: {new_address}")
                print()

                updates_made += 1
            else:
                print(f"WARNING: Customer {customer_id} not found in database")
                print()

        # Commit changes
        session.commit()
        print(f"✓ Successfully updated {updates_made} customer addresses!")

        # Display updated customers
        print("\n=== Verification ===")
        for customer_id in customer_updates.keys():
            statement = select(Customer).where(
                Customer.customer_id == customer_id)
            customer = session.exec(statement).first()
            if customer:
                print(f"{customer.customer_id}: {customer.customer_name}")
                print(f"  Address: {customer.address}")
                print()

    except Exception as e:
        session.rollback()
        print(f"Error updating customer addresses: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    update_customer_addresses()
