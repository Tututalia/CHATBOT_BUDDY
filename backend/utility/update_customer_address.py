import sqlite3
import os

# Path to the SQLite database (relative to this utility script)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "retail_agent.db")

CUSTOMER_ID = "CUST082"
NEW_ADDRESS = "54 Tiljala Road, Kolkata"
OLD_ADDRESS = "EE Block, Sector II, Bidhannagar, Kolkata, West Bengal 700091"


def update_customer_address():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify the customer exists and show current address
    cursor.execute(
        "SELECT customer_id, address FROM customers WHERE customer_id = ?",
        (CUSTOMER_ID,)
    )
    row = cursor.fetchone()

    if not row:
        print(
            f"[ERROR] Customer '{CUSTOMER_ID}' not found in the customers table.")
        conn.close()
        return

    print(f"[INFO] Current address for {CUSTOMER_ID}: {row[1]}")

    # Perform the update
    cursor.execute(
        "UPDATE customers SET address = ? WHERE customer_id = ?",
        (NEW_ADDRESS, CUSTOMER_ID)
    )
    conn.commit()

    # Confirm the update
    cursor.execute(
        "SELECT customer_id, address FROM customers WHERE customer_id = ?",
        (CUSTOMER_ID,)
    )
    updated_row = cursor.fetchone()
    print(f"[SUCCESS] Address updated for {CUSTOMER_ID}.")
    print(f"[INFO] New address: {updated_row[1]}")

    conn.close()


if __name__ == "__main__":
    update_customer_address()
