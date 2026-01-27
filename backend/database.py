from sqlmodel import SQLModel, create_engine, Session, select
from typing import Optional, List
from models import Customer, Product, Store, OrderHistory, StoreKeeperTransaction, AdminDashboardData, Cart

# Database configuration
DATABASE_URL = "sqlite:///./retail_agent.db"
engine = create_engine(DATABASE_URL, echo=True, connect_args={
                       "check_same_thread": False})


# Initialize database
def init_db():
    """Create all tables in the database"""
    SQLModel.metadata.create_all(engine)


# Get database session
def get_session():
    """Get a database session"""
    with Session(engine) as session:
        yield session


def get_db_session():
    """Get a database session for direct use"""
    return Session(engine)
