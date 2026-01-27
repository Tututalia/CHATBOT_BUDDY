from sqlmodel import Session, select, or_, and_, func
from typing import Optional, List, Dict, Any
from models import (
    Customer, Product, Store, OrderHistory,
    StoreKeeperTransaction, AdminDashboardData
)


# ==================== CUSTOMER CRUD ====================

class CustomerCRUD:
    @staticmethod
    def create(session: Session, customer: Customer) -> Customer:
        """Add a new customer"""
        session.add(customer)
        session.commit()
        session.refresh(customer)
        return customer

    @staticmethod
    def get_by_id(session: Session, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        statement = select(Customer).where(Customer.customer_id == customer_id)
        return session.exec(statement).first()

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        """List all customers with pagination"""
        statement = select(Customer).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    def filter(
        session: Session,
        customer_name: Optional[str] = None,
        gender: Optional[str] = None,
        min_loyalty_points: Optional[int] = None,
        phone: Optional[str] = None
    ) -> List[Customer]:
        """Filter customers by various criteria"""
        statement = select(Customer)

        if customer_name:
            statement = statement.where(
                Customer.customer_name.contains(customer_name))
        if gender:
            statement = statement.where(Customer.gender == gender)
        if min_loyalty_points is not None:
            statement = statement.where(
                Customer.loyalty_points >= min_loyalty_points)
        if phone:
            statement = statement.where(Customer.phone == phone)

        return session.exec(statement).all()

    @staticmethod
    def update(session: Session, customer_id: str, data: Dict[str, Any]) -> Optional[Customer]:
        """Update customer information"""
        customer = CustomerCRUD.get_by_id(session, customer_id)
        if customer:
            for key, value in data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            session.add(customer)
            session.commit()
            session.refresh(customer)
        return customer

    @staticmethod
    def delete(session: Session, customer_id: str) -> bool:
        """Delete a customer"""
        customer = CustomerCRUD.get_by_id(session, customer_id)
        if customer:
            session.delete(customer)
            session.commit()
            return True
        return False


# ==================== PRODUCT CRUD ====================

class ProductCRUD:
    @staticmethod
    def create(session: Session, product: Product) -> Product:
        """Add a new product"""
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    @staticmethod
    def get_by_id(session: Session, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        statement = select(Product).where(Product.product_id == product_id)
        return session.exec(statement).first()

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        """List all products with pagination"""
        statement = select(Product).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    def filter(
        session: Session,
        product_name: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        online_available: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[Product]:
        """Filter products by various criteria"""
        statement = select(Product)

        if product_name:
            statement = statement.where(
                Product.product_name.contains(product_name))
        if category:
            statement = statement.where(Product.category == category)
        if gender:
            statement = statement.where(Product.gender == gender)
        if min_price is not None:
            statement = statement.where(Product.price >= min_price)
        if max_price is not None:
            statement = statement.where(Product.price <= max_price)
        if online_available:
            statement = statement.where(
                Product.online_available == online_available)
        if season:
            statement = statement.where(Product.season == season)

        return session.exec(statement).all()

    @staticmethod
    def update(session: Session, product_id: str, data: Dict[str, Any]) -> Optional[Product]:
        """Update product information"""
        product = ProductCRUD.get_by_id(session, product_id)
        if product:
            for key, value in data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            session.add(product)
            session.commit()
            session.refresh(product)
        return product

    @staticmethod
    def delete(session: Session, product_id: str) -> bool:
        """Delete a product"""
        product = ProductCRUD.get_by_id(session, product_id)
        if product:
            session.delete(product)
            session.commit()
            return True
        return False


# ==================== STORE CRUD ====================

class StoreCRUD:
    @staticmethod
    def create(session: Session, store: Store) -> Store:
        """Add a new store"""
        session.add(store)
        session.commit()
        session.refresh(store)
        return store

    @staticmethod
    def get_by_id(session: Session, store_id: str) -> Optional[Store]:
        """Get store by ID"""
        statement = select(Store).where(Store.store_id == store_id)
        return session.exec(statement).first()

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Store]:
        """List all stores with pagination"""
        statement = select(Store).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    def filter(
        session: Session,
        store_name: Optional[str] = None,
        manager_name: Optional[str] = None
    ) -> List[Store]:
        """Filter stores by various criteria"""
        statement = select(Store)

        if store_name:
            statement = statement.where(Store.store_name.contains(store_name))
        if manager_name:
            statement = statement.where(
                Store.manager_name.contains(manager_name))

        return session.exec(statement).all()

    @staticmethod
    def update(session: Session, store_id: str, data: Dict[str, Any]) -> Optional[Store]:
        """Update store information"""
        store = StoreCRUD.get_by_id(session, store_id)
        if store:
            for key, value in data.items():
                if hasattr(store, key):
                    setattr(store, key, value)
            session.add(store)
            session.commit()
            session.refresh(store)
        return store

    @staticmethod
    def delete(session: Session, store_id: str) -> bool:
        """Delete a store"""
        store = StoreCRUD.get_by_id(session, store_id)
        if store:
            session.delete(store)
            session.commit()
            return True
        return False


# ==================== ORDER HISTORY CRUD ====================

class OrderHistoryCRUD:
    @staticmethod
    def create(session: Session, order: OrderHistory) -> OrderHistory:
        """Add a new order"""
        session.add(order)
        session.commit()
        session.refresh(order)
        return order

    @staticmethod
    def get_by_id(session: Session, transaction_id: str) -> Optional[OrderHistory]:
        """Get order by transaction ID"""
        statement = select(OrderHistory).where(
            OrderHistory.transaction_id == transaction_id)
        return session.exec(statement).first()

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[OrderHistory]:
        """List all orders with pagination"""
        statement = select(OrderHistory).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    def filter(
        session: Session,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        min_quantity: Optional[int] = None
    ) -> List[OrderHistory]:
        """Filter orders by various criteria"""
        statement = select(OrderHistory)

        if customer_id:
            statement = statement.where(
                OrderHistory.customer_id == customer_id)
        if product_id:
            statement = statement.where(OrderHistory.product_id == product_id)
        if customer_name:
            statement = statement.where(
                OrderHistory.customer_name.contains(customer_name))
        if min_quantity is not None:
            statement = statement.where(OrderHistory.quantity >= min_quantity)

        return session.exec(statement).all()

    @staticmethod
    def get_by_customer(session: Session, customer_id: str) -> List[OrderHistory]:
        """Get all orders for a specific customer"""
        statement = select(OrderHistory).where(
            OrderHistory.customer_id == customer_id)
        return session.exec(statement).all()

    @staticmethod
    def update(session: Session, transaction_id: str, data: Dict[str, Any]) -> Optional[OrderHistory]:
        """Update order information"""
        order = OrderHistoryCRUD.get_by_id(session, transaction_id)
        if order:
            for key, value in data.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            session.add(order)
            session.commit()
            session.refresh(order)
        return order

    @staticmethod
    def delete(session: Session, transaction_id: str) -> bool:
        """Delete an order"""
        order = OrderHistoryCRUD.get_by_id(session, transaction_id)
        if order:
            session.delete(order)
            session.commit()
            return True
        return False


# ==================== STORE KEEPER TRANSACTION CRUD ====================

class StoreKeeperTransactionCRUD:
    @staticmethod
    def create(session: Session, transaction: StoreKeeperTransaction) -> StoreKeeperTransaction:
        """Add a new store keeper transaction"""
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction

    @staticmethod
    def get_by_id(session: Session, transaction_id: int) -> Optional[StoreKeeperTransaction]:
        """Get transaction by ID"""
        statement = select(StoreKeeperTransaction).where(
            StoreKeeperTransaction.id == transaction_id)
        return session.exec(statement).first()

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[StoreKeeperTransaction]:
        """List all transactions with pagination"""
        statement = select(StoreKeeperTransaction).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    def filter(
        session: Session,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        store_name: Optional[str] = None,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> List[StoreKeeperTransaction]:
        """Filter transactions by various criteria"""
        statement = select(StoreKeeperTransaction)

        if customer_id:
            statement = statement.where(
                StoreKeeperTransaction.customer_id == customer_id)
        if product_id:
            statement = statement.where(
                StoreKeeperTransaction.product_id == product_id)
        if store_name:
            statement = statement.where(
                StoreKeeperTransaction.store_name.contains(store_name))
        if mode:
            statement = statement.where(StoreKeeperTransaction.mode == mode)
        if status:
            statement = statement.where(
                StoreKeeperTransaction.status == status)
        if min_amount is not None:
            statement = statement.where(
                StoreKeeperTransaction.amount >= min_amount)
        if max_amount is not None:
            statement = statement.where(
                StoreKeeperTransaction.amount <= max_amount)

        return session.exec(statement).all()

    @staticmethod
    def update(session: Session, transaction_id: int, data: Dict[str, Any]) -> Optional[StoreKeeperTransaction]:
        """Update transaction information"""
        transaction = StoreKeeperTransactionCRUD.get_by_id(
            session, transaction_id)
        if transaction:
            for key, value in data.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
        return transaction

    @staticmethod
    def delete(session: Session, transaction_id: int) -> bool:
        """Delete a transaction"""
        transaction = StoreKeeperTransactionCRUD.get_by_id(
            session, transaction_id)
        if transaction:
            session.delete(transaction)
            session.commit()
            return True
        return False


# ==================== ADMIN DASHBOARD DATA CRUD ====================

class AdminDashboardDataCRUD:
    @staticmethod
    def create(session: Session, data: AdminDashboardData) -> AdminDashboardData:
        """Add a new admin dashboard entry"""
        session.add(data)
        session.commit()
        session.refresh(data)
        return data

    @staticmethod
    def get_by_id(session: Session, data_id: int) -> Optional[AdminDashboardData]:
        """Get entry by ID"""
        statement = select(AdminDashboardData).where(
            AdminDashboardData.id == data_id)
        return session.exec(statement).first()

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[AdminDashboardData]:
        """List all entries with pagination"""
        statement = select(AdminDashboardData).offset(skip).limit(limit)
        return session.exec(statement).all()

    @staticmethod
    def filter(
        session: Session,
        user_name: Optional[str] = None,
        product: Optional[str] = None,
        mode: Optional[str] = None,
        store_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[AdminDashboardData]:
        """Filter admin dashboard data by various criteria"""
        statement = select(AdminDashboardData)

        if user_name:
            statement = statement.where(
                AdminDashboardData.user_name.contains(user_name))
        if product:
            statement = statement.where(
                AdminDashboardData.product.contains(product))
        if mode:
            statement = statement.where(AdminDashboardData.mode == mode)
        if store_name:
            statement = statement.where(
                AdminDashboardData.store_name.contains(store_name))
        if status:
            statement = statement.where(AdminDashboardData.status == status)

        return session.exec(statement).all()

    @staticmethod
    def update(session: Session, data_id: int, data: Dict[str, Any]) -> Optional[AdminDashboardData]:
        """Update admin dashboard entry"""
        entry = AdminDashboardDataCRUD.get_by_id(session, data_id)
        if entry:
            for key, value in data.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            session.add(entry)
            session.commit()
            session.refresh(entry)
        return entry

    @staticmethod
    def delete(session: Session, data_id: int) -> bool:
        """Delete an admin dashboard entry"""
        entry = AdminDashboardDataCRUD.get_by_id(session, data_id)
        if entry:
            session.delete(entry)
            session.commit()
            return True
        return False


# ==================== ANALYTICS & AGGREGATIONS ====================

class AnalyticsCRUD:
    @staticmethod
    def get_customer_total_spending(session: Session, customer_id: str) -> float:
        """Get total spending for a customer"""
        statement = select(func.sum(StoreKeeperTransaction.amount)).where(
            StoreKeeperTransaction.customer_id == customer_id
        )
        result = session.exec(statement).first()
        return result if result else 0.0

    @staticmethod
    def get_product_sales_count(session: Session, product_id: str) -> int:
        """Get total sales count for a product"""
        statement = select(func.count(OrderHistory.transaction_id)).where(
            OrderHistory.product_id == product_id
        )
        result = session.exec(statement).first()
        return result if result else 0

    @staticmethod
    def get_top_customers(session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by loyalty points"""
        statement = select(Customer).order_by(
            Customer.loyalty_points.desc()).limit(limit)
        customers = session.exec(statement).all()
        return [{"customer_id": c.customer_id, "name": c.customer_name, "loyalty_points": c.loyalty_points}
                for c in customers]

    @staticmethod
    def get_store_revenue(session: Session, store_name: str) -> float:
        """Get total revenue for a store"""
        statement = select(func.sum(StoreKeeperTransaction.amount)).where(
            StoreKeeperTransaction.store_name == store_name
        )
        result = session.exec(statement).first()
        return result if result else 0.0
