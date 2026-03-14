"""
Script to update the 'distance' table for CUST082.
Reads customer_address, distance, and map_url from the
distance_mapurl_export.csv file and applies them to every row
in the distance table where customer_id = 'CUST082'.
Rows are matched by (customer_id + store_id).
"""

import sqlite3
import csv
import os

TARGET_CUSTOMER_ID = "CUST082"

# Absolute paths — work correctly from any directory
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BACKEND_DIR, "retail_agent.db")
CSV_PATH = os.path.join(BACKEND_DIR, "data", "distance_mapurl_export.csv")


def update_distance_for_cust082():
    # ── Validate paths ──────────────────────────────────────────────────────
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at: {DB_PATH}")
        return

    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] CSV file not found at: {CSV_PATH}")
        return

    print(f"[INFO] Database : {DB_PATH}")
    print(f"[INFO] CSV file : {CSV_PATH}")

    # ── Read matching rows from CSV ─────────────────────────────────────────
    csv_rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("customer_id", "").strip() == TARGET_CUSTOMER_ID:
                csv_rows.append({
                    "store_id":         row["store_id"].strip(),
                    "customer_address": row["customer_address"].strip(),
                    "distance":         row["distance"].strip(),
                    "map_url":          row["map_url"].strip(),
                })

    if not csv_rows:
        print(
            f"[WARNING] No rows found for customer_id '{TARGET_CUSTOMER_ID}' in the CSV.")
        return

    print(
        f"[INFO] Found {len(csv_rows)} row(s) for '{TARGET_CUSTOMER_ID}' in the CSV.")

    # ── Apply updates to the database ───────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    updated = 0
    not_found = 0

    for row in csv_rows:
        # Verify the (customer_id, store_id) pair exists in the distance table
        cursor.execute(
            "SELECT 1 FROM distance WHERE customer_id = ? AND store_id = ?",
            (TARGET_CUSTOMER_ID, row["store_id"]),
        )
        exists = cursor.fetchone()

        if not exists:
            print(
                f"[SKIP] No distance row found for customer_id='{TARGET_CUSTOMER_ID}', store_id='{row['store_id']}'")
            not_found += 1
            continue

        cursor.execute(
            """
            UPDATE distance
               SET customer_address = ?,
                   distance         = ?,
                   map_url          = ?
             WHERE customer_id = ?
               AND store_id    = ?
            """,
            (
                row["customer_address"],
                row["distance"],
                row["map_url"],
                TARGET_CUSTOMER_ID,
                row["store_id"],
            ),
        )
        updated += 1

    conn.commit()
    conn.close()

    print(f"\n[SUCCESS] Updated  : {updated} row(s)")
    if not_found:
        print(
            f"[WARNING] Not found: {not_found} row(s) (store_id missing in distance table)")


if __name__ == "__main__":
    update_distance_for_cust082()
