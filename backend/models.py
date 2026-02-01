
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date

# Role Model


class Role(SQLModel, table=True):
    __tablename__ = "role"

    id: int = Field(primary_key=True)
    role_type: str


# Customer Model
class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    customer_id: str = Field(primary_key=True, index=True)
    customer_name: str = Field(index=True)
    gender: str
    phone: str
    address: str
    loyalty_points: int = Field(default=0)
    order_history: Optional[str] = None  # Comma-separated transaction IDs
    order_dates: Optional[str] = None    # Comma-separated dates
    pending_orders: Optional[str] = None
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")

    # Relationships
    orders: List["OrderHistory"] = Relationship(back_populates="customer")
    store_transactions: List["StoreKeeperTransaction"] = Relationship(
        back_populates="customer")


# Product Model
class Product(SQLModel, table=True):
    __tablename__ = "products"

    product_id: str = Field(primary_key=True, index=True)
    product_name: str = Field(index=True)
    category: str = Field(index=True)
    gender: str
    price: float
    quantity: int = Field(default=0)  # Available quantity for each product
    online_available: str  # Yes/No
    offline_available: str  # Yes/No
    offline_stores: Optional[str] = None  # Semicolon-separated store names
    store_ids: Optional[str] = None       # Semicolon-separated store IDs
    festival: Optional[str] = None        # Comma-separated festivals
    season: str
    image_reference: str
    loyalty_points: int = Field(default=0)

    # Relationships
    orders: List["OrderHistory"] = Relationship(back_populates="product")
    store_transactions: List["StoreKeeperTransaction"] = Relationship(
        back_populates="product_ref")


# Store/Outlet Model
class Store(SQLModel, table=True):
    __tablename__ = "stores"

    store_id: str = Field(primary_key=True, index=True)
    store_name: str = Field(index=True)
    address: str
    manager_name: str
    store_phone: str

    # Relationships
    store_transactions: List["StoreKeeperTransaction"] = Relationship(
        back_populates="store")


# Order History Model
class OrderHistory(SQLModel, table=True):
    __tablename__ = "order_history"

    transaction_id: str = Field(primary_key=True, index=True)
    customer_id: str = Field(foreign_key="customers.customer_id", index=True)
    customer_name: str
    product_id: str = Field(foreign_key="products.product_id", index=True)
    product_name: str
    quantity: int
    order_dates: str  # Date as string
    loyalty_points: int

    # Relationships
    customer: Optional[Customer] = Relationship(back_populates="orders")
    product: Optional[Product] = Relationship(back_populates="orders")


# Store Keeper Transaction Model
class StoreKeeperTransaction(SQLModel, table=True):
    __tablename__ = "store_keeper_transactions"

    id: int = Field(primary_key=True)  # ID column
    customer_id: str = Field(foreign_key="customers.customer_id", index=True)
    product_id: str = Field(foreign_key="products.product_id", index=True)
    date: str  # Date as string
    user_name: str
    product: str  # Product name
    qty: int
    mode: str  # Online/Offline
    # store_name is a human-readable name; use `store_id` as the FK to `stores.store_id`
    store_name: str = Field(index=True)
    store_id: Optional[str] = Field(
        default=None, foreign_key="stores.store_id", index=True)
    status: str  # Complete/Pending
    amount: float
    address: str
    phone: str

    # Relationships
    customer: Optional[Customer] = Relationship(
        back_populates="store_transactions")
    product_ref: Optional[Product] = Relationship(
        back_populates="store_transactions")
    store: Optional[Store] = Relationship(back_populates="store_transactions")


# Admin Dashboard Data Model
class AdminDashboardData(SQLModel, table=True):
    __tablename__ = "admin_dashboard_data"

    id: int = Field(primary_key=True)
    date: str
    user_name: str = Field(index=True)
    product: str = Field(index=True)
    qty: int
    mode: str  # Online/Offline
    store_name: str
    status: str  # Complete/Pending
    amount: float
    address: str
    phone: str


# Cart Model
class Cart(SQLModel, table=True):
    __tablename__ = "cart"

    order_id: str = Field(primary_key=True, index=True)
    customer_id: Optional[str] = Field(
        default=None, foreign_key="customers.customer_id", index=True)
    product_id: Optional[str] = Field(
        default=None, foreign_key="products.product_id", index=True)
    store_id: Optional[str] = Field(
        default=None, foreign_key="stores.store_id", index=True)
    channel: Optional[str] = Field(default="online")
    status: Optional[str] = Field(default="pending")
    created_at: Optional[str] = Field(default=None)
    quantity: int = Field(default=1)  # Quantity of product in cart

    # Relationships
    customer: Optional[Customer] = Relationship()
    product: Optional[Product] = Relationship()
    store: Optional[Store] = Relationship()
