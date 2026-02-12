"""Append products from master_products.csv into the existing products table.

This script ONLY APPENDS:
- It will not overwrite any existing product rows.
- It skips rows whose `product_id` already exists in the DB.
- It is safe to re-run.

Usage (from repo root):
    python backend/append_master_products_to_products.py

Optional:
    python backend/append_master_products_to_products.py --dry-run
    python backend/append_master_products_to_products.py --csv-path backend/data/master_products.csv --db-path backend/retail_agent.db
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


_NULL_LIKE = {"", "null", "none", "nan"}


def _nullify(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned.lower() in _NULL_LIKE:
        return None
    return cleaned


def _to_int(value: Any, *, field_name: str) -> int:
    if value is None:
        raise ValueError(f"Missing integer field: {field_name}")
    text = str(value).strip()
    if text.lower() in _NULL_LIKE:
        return 0
    return int(float(text))


def _to_float(value: Any, *, field_name: str) -> float:
    if value is None:
        raise ValueError(f"Missing float field: {field_name}")
    text = str(value).strip()
    if text.lower() in _NULL_LIKE:
        return 0.0
    return float(text)


def _get_products_table_columns(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("PRAGMA table_info(products)")
    rows = cur.fetchall()
    # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
    return [r[1] for r in rows]


def _iter_csv_rows(csv_path: str) -> Iterable[Dict[str, str]]:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        yield from reader


def _required_columns_present(fieldnames: Iterable[str]) -> Tuple[bool, Set[str]]:
    required = {
        "product_id",
        "product_name",
        "category",
        "gender",
        "price",
        "quantity",
        "online_available",
        "offline_available",
        "season",
        "image_reference",
        "loyalty_points",
        "discount",
    }
    present = {name.strip() for name in fieldnames}
    missing = required - present
    return (len(missing) == 0, missing)


def _load_existing_product_ids(conn: sqlite3.Connection) -> Set[str]:
    cur = conn.execute("SELECT product_id FROM products")
    return {r[0] for r in cur.fetchall() if r and r[0] is not None}


def _build_insert_statement(columns: Sequence[str]) -> str:
    cols_sql = ", ".join([f'"{c}"' for c in columns])
    placeholders = ", ".join(["?"] * len(columns))
    return f"INSERT OR IGNORE INTO products ({cols_sql}) VALUES ({placeholders})"


def append_master_products(
    *,
    db_path: str,
    csv_path: str,
    dry_run: bool,
    commit_every: int,
) -> None:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")

        # Fail fast if products table isn't there.
        table_check = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
        ).fetchone()
        if not table_check:
            raise RuntimeError(
                "Table 'products' not found in the DB. "
                "Create tables first (e.g., run backend/create_tables.py)."
            )

        existing_ids = _load_existing_product_ids(conn)
        db_columns = _get_products_table_columns(conn)

        seen_in_csv: Set[str] = set()
        total_rows = 0
        duplicate_in_csv = 0
        skipped_existing = 0
        to_insert = 0

        # Validate header early
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV has no header row")
            ok, missing = _required_columns_present(reader.fieldnames)
            if not ok:
                raise ValueError(
                    "CSV missing required columns: " +
                    ", ".join(sorted(missing))
                )

        insert_columns = [
            c
            for c in [
                "product_id",
                "product_name",
                "category",
                "gender",
                "price",
                "quantity",
                "online_available",
                "offline_available",
                "offline_stores",
                "store_ids",
                "festival",
                "season",
                "image_reference",
                "loyalty_points",
                "discount",
            ]
            if c in db_columns
        ]
        if "product_id" not in insert_columns:
            raise RuntimeError(
                "products table does not have product_id column")

        insert_sql = _build_insert_statement(insert_columns)
        pending: List[Tuple[Any, ...]] = []

        for row in _iter_csv_rows(csv_path):
            total_rows += 1
            product_id = _nullify(row.get("product_id"))
            if not product_id:
                raise ValueError(f"Row {total_rows}: missing product_id")

            if product_id in seen_in_csv:
                duplicate_in_csv += 1
                continue
            seen_in_csv.add(product_id)

            if product_id in existing_ids:
                skipped_existing += 1
                continue

            # Build row values in insert_columns order
            values_by_col: Dict[str, Any] = {
                "product_id": product_id,
                "product_name": _nullify(row.get("product_name")) or "",
                "category": _nullify(row.get("category")) or "",
                "gender": _nullify(row.get("gender")) or "",
                "price": _to_float(row.get("price"), field_name="price"),
                "quantity": _to_int(row.get("quantity"), field_name="quantity"),
                "online_available": _nullify(row.get("online_available")) or "",
                "offline_available": _nullify(row.get("offline_available")) or "",
                "offline_stores": _nullify(row.get("offline_stores")),
                "store_ids": _nullify(row.get("store_ids")),
                "festival": _nullify(row.get("festival")),
                "season": _nullify(row.get("season")) or "",
                "image_reference": _nullify(row.get("image_reference")) or "",
                "loyalty_points": _to_int(
                    row.get("loyalty_points"), field_name="loyalty_points"
                ),
                "discount": _to_int(row.get("discount"), field_name="discount"),
            }

            pending.append(tuple(values_by_col[c] for c in insert_columns))
            to_insert += 1

            if commit_every > 0 and len(pending) >= commit_every:
                if not dry_run:
                    conn.executemany(insert_sql, pending)
                    conn.commit()
                pending.clear()

        if pending:
            if not dry_run:
                conn.executemany(insert_sql, pending)
                conn.commit()

        if dry_run:
            conn.rollback()
    finally:
        conn.close()

    mode = "DRY-RUN" if dry_run else "COMMITTED"
    print("=" * 70)
    print(f"Append master_products -> products ({mode})")
    print("=" * 70)
    print(f"DB:  {db_path}")
    print(f"CSV: {csv_path}")
    print(f"CSV rows read:           {total_rows}")
    print(f"Duplicate in CSV skipped:{duplicate_in_csv}")
    print(f"Already in DB skipped:   {skipped_existing}")
    print(f"New rows inserted:       {to_insert}")


def main() -> None:
    here = os.path.dirname(__file__)
    default_db = os.path.join(here, "retail_agent.db")
    default_csv = os.path.join(here, "data", "master_products.csv")

    parser = argparse.ArgumentParser(
        description=(
            "Append products from backend/data/master_products.csv "
            "into the existing products table in retail_agent.db "
            "without overwriting existing rows."
        )
    )
    parser.add_argument(
        "--db-path",
        default=default_db,
        help=f"Path to SQLite DB (default: {default_db})",
    )
    parser.add_argument(
        "--csv-path",
        default=default_csv,
        help=f"Path to master_products.csv (default: {default_csv})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute what would be inserted, but do not commit.",
    )
    parser.add_argument(
        "--commit-every",
        type=int,
        default=500,
        help="Commit every N inserts (0 = only final commit). Default: 500",
    )

    args = parser.parse_args()

    append_master_products(
        db_path=os.path.abspath(args.db_path),
        csv_path=os.path.abspath(args.csv_path),
        dry_run=args.dry_run,
        commit_every=args.commit_every,
    )


if __name__ == "__main__":
    main()
