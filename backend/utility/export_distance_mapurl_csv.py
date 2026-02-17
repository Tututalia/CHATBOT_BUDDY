import csv

from sqlmodel import select

from database import get_db_session
from models import Distance

# Exports the already-populated `distance` and `map_url` columns to a CSV file.
# No Google Maps API calls are made.
OUT_CSV = "distance_mapurl_export.csv"

# Include stable keys (customer_id, store_id) so the exported data can be re-applied.
FIELDS = [
    "customer_id",
    "store_id",
    "distance",
    "map_url",
    # Optional but useful for validation/debugging
    "customer_address",
    "store_name",
    "store_address",
]


def main() -> None:
    session = get_db_session()
    rows = session.exec(select(Distance)).all()

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        for r in rows:
            writer.writerow(
                {
                    "customer_id": r.customer_id,
                    "store_id": r.store_id,
                    "distance": r.distance,
                    "map_url": r.map_url or "",
                    "customer_address": r.customer_address,
                    "store_name": r.store_name,
                    "store_address": r.store_address,
                }
            )

    session.close()
    print(f"Exported {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
