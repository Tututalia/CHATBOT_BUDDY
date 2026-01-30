from sqlmodel import SQLModel, create_engine
import os

# Path to your SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "data.db")
engine = create_engine(f"sqlite:///{DB_PATH}")


def main():
    SQLModel.metadata.create_all(engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    main()
