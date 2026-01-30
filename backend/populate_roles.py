from sqlmodel import Session, create_engine
from models import Role
import os

# Path to your SQLite database file
db_path = os.path.join(os.path.dirname(__file__), "retail_agent.db")
engine = create_engine(f"sqlite:///{db_path}")

roles = [
    Role(id=1, role_type="customer"),
    Role(id=2, role_type="store_keeper"),
    Role(id=3, role_type="admin"),
]


def main():
    with Session(engine) as session:
        for role in roles:
            session.merge(role)  # merge to avoid duplicate insert
        session.commit()
    print("Role table populated with default roles.")


if __name__ == "__main__":
    main()
