import sqlite3
import os
import random
import sys
import argparse
from typing import Optional

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE, "retail_agent.db")


def main(min_q: int, max_q: int, seed: Optional[int], sample: int):
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        sys.exit(1)

    if seed is not None:
        random.seed(seed)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("SELECT product_id FROM products").fetchall()
    if not rows:
        print("No products found to update.")
        conn.close()
        sys.exit(0)

    # Deterministic ordering: sort product IDs so same seed gives same assignments
    product_ids = sorted([r[0] for r in rows])

    for product_id in product_ids:
        qty = random.randint(min_q, max_q)
        cur.execute(
            "UPDATE products SET quantity = ? WHERE product_id = ?", (qty, product_id))

    conn.commit()
    print(
        f"Updated {len(product_ids)} products with random quantities in range [{min_q},{max_q}] (seed={seed}).")

    if sample > 0:
        samples = cur.execute(
            "SELECT product_id, product_name, quantity FROM products LIMIT ?", (sample,)).fetchall()
        for pid, name, q in samples:
            print(pid, name, q)

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Populate products.quantity with random values')
    parser.add_argument('--min', type=int, default=1,
                        help='Minimum random quantity')
    parser.add_argument('--max', type=int, default=200,
                        help='Maximum random quantity')
    parser.add_argument('--seed', type=int, default=None,
                        help='Optional RNG seed for reproducible values')
    parser.add_argument('--sample', type=int, default=5,
                        help='Show N sample rows after update')
    args = parser.parse_args()
    main(args.min, args.max, args.seed, args.sample)
