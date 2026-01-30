from sqlmodel import SQLModel, create_engine
import os

# Ensure all models are imported so SQLModel.metadata includes all tables
import models

# Path to your SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "retail_agent.db")
engine = create_engine(f"sqlite:///{DB_PATH}")


def main():
    SQLModel.metadata.create_all(engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    main()
