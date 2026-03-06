from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import event
from typing import Optional, List
from models import Customer, Product, Store, OrderHistory, StoreKeeperTransaction, AdminDashboardData, Cart, Distance, Feedback

# Database configuration
DATABASE_URL = "sqlite:///./retail_agent.db"
engine = create_engine(DATABASE_URL, echo=True, connect_args={
                       "check_same_thread": False})


# Ensure SQLite enforces foreign key constraints on every new connection
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        dbapi_connection.execute('PRAGMA foreign_keys=ON')
    except Exception:
        # Some DBAPIs may require cursor execution
        cur = dbapi_connection.cursor()
        cur.execute('PRAGMA foreign_keys=ON')
        cur.close()


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

