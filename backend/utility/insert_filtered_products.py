import sqlite3
import csv
import os


def insert_filtered_products():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "retail_agent.db")
    csv_path = os.path.join(base_dir, "data", "filtered_products.csv")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read CSV and insert rows
    inserted = 0
    skipped = 0

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO products (
                        product_id, category, gender, product_name,
                        price, image_reference, quantity, online_available,
                        offline_available, festival, season, loyalty_points, discount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["product_id"],
                    row["category"],
                    row["gender"],
                    row["product_name"],
                    row["price"],
                    row["image_reference"],
                    int(row["quantity"]),
                    row["online_available"],
                    row["offline_available"],
                    row["festival"],
                    row["season"],
                    int(row["loyalty_points"]),
                    int(row["discount"])
                ))
                inserted += 1
            except sqlite3.IntegrityError as e:
                skipped += 1
                print(f"Skipped {row['product_id']}: {e}")
            except Exception as e:
                skipped += 1
                print(f"Error inserting {row['product_id']}: {e}")

    conn.commit()
    conn.close()

    print(f"\n--- Insert Summary ---")
    print(f"Total inserted: {inserted}")
    print(f"Total skipped:  {skipped}")
    print(f"Database path:  {db_path}")


if __name__ == "__main__":
    insert_filtered_products()
