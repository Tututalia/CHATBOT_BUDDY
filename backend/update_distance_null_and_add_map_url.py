from database import get_db_session
from models import Distance
from sqlmodel import select
from sqlalchemy import text


def update_distance_table():
    session = get_db_session()
    # Set distance values to 0 only where they are NULL (backward-compatible safety)
    session.execute(text("UPDATE distance SET distance = 0 WHERE distance IS NULL"))
    # Add new column map_url if not exists
    try:
        session.execute(text("ALTER TABLE distance ADD COLUMN map_url TEXT"))
    except Exception as e:
        # Ignore error if column already exists
        print("map_url column may already exist.")
    session.commit()
    session.close()
    print("All distance values set to 0 and map_url column added.")


if __name__ == "__main__":
    update_distance_table()
