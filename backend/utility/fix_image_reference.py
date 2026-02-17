import os
import sqlite3


def normalize_image_reference(value: str) -> str:
    # Convert Windows path separators to URL separators
    value = value.replace("\\", "/")

    # Ensure leading slash for relative images paths
    if value.startswith("images/"):
        value = "/" + value

    return value


def fix_image_references():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "retail_agent.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Only target rows that are NOT already in acceptable format '/images/...'
    # and look like our local images paths.
    cursor.execute(
        """
        SELECT product_id, image_reference
        FROM products
        WHERE image_reference IS NOT NULL
          AND (
                image_reference LIKE 'images%'
             OR image_reference LIKE '/images\\%'
          )
          AND image_reference NOT LIKE '/images/%'
        """
    )

    rows = cursor.fetchall()
    print(f"Found {len(rows)} rows to normalize in products.image_reference")

    updated = 0
    for product_id, old_ref in rows:
        if not old_ref:
            continue

        new_ref = normalize_image_reference(old_ref)

        # Safety: don’t touch anything that still doesn’t look right
        if not new_ref.startswith("/images/"):
            print(
                f"Skip {product_id}: unexpected image_reference '{old_ref}' -> '{new_ref}'")
            continue

        if new_ref == old_ref:
            continue

        cursor.execute(
            "UPDATE products SET image_reference = ? WHERE product_id = ?",
            (new_ref, product_id),
        )
        updated += 1

    conn.commit()

    print(f"Updated {updated} rows")

    cursor.execute(
        """
        SELECT product_id, image_reference
        FROM products
        WHERE image_reference LIKE '/images/%'
        ORDER BY product_id
        LIMIT 10
        """
    )
    sample = cursor.fetchall()
    print("\nSample '/images/..' rows:")
    for pid, img in sample:
        print(f"  {pid}: {img}")

    conn.close()


if __name__ == "__main__":
    fix_image_references()
