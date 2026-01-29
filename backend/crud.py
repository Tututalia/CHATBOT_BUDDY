from sqlmodel import Session, select, or_, and_, func, SQLModel
from typing import Optional, List, Dict, Any, Type, Union
from models import (
    Customer, Product, Store, OrderHistory,
    StoreKeeperTransaction, AdminDashboardData, Cart
)


# ==================== UNIVERSAL DYNAMIC CRUD ====================

class UniversalCRUD:
    """
    A universal CRUD class that works with any SQLModel table.
    Provides dynamic operations for create, read, update, delete, and filter.
    """

    def __init__(self, model: Type[SQLModel], primary_key: str = "id"):
        """
        Initialize the CRUD instance with a model.

        Args:
            model: The SQLModel class to perform operations on
            primary_key: The name of the primary key field (default: "id")
        """
        self.model = model
        self.primary_key = primary_key

    def create(self, session: Session, data: Union[SQLModel, Dict[str, Any]]) -> SQLModel:
        """
        Create a new record.

        Args:
            session: Database session
            data: Model instance or dictionary of field values

        Returns:
            Created model instance
        """
        if isinstance(data, dict):
            instance = self.model(**data)
        else:
            instance = data

        session.add(instance)
        session.commit()
        session.refresh(instance)
        return instance

    def bulk_create(self, session: Session, data_list: List[Union[SQLModel, Dict[str, Any]]]) -> List[SQLModel]:
        """
        Create multiple records at once.

        Args:
            session: Database session
            data_list: List of model instances or dictionaries

        Returns:
            List of created model instances
        """
        instances = []
        for data in data_list:
            if isinstance(data, dict):
                instance = self.model(**data)
            else:
                instance = data
            instances.append(instance)
            session.add(instance)

        session.commit()
        for instance in instances:
            session.refresh(instance)
        return instances

    def get_by_id(self, session: Session, record_id: Any) -> Optional[SQLModel]:
        """
        Get a single record by its primary key.

        Args:
            session: Database session
            record_id: Value of the primary key

        Returns:
            Model instance or None if not found
        """
        statement = select(self.model).where(
            getattr(self.model, self.primary_key) == record_id
        )
        return session.exec(statement).first()

    def get_all(self, session: Session, skip: int = 0, limit: int = 100) -> List[SQLModel]:
        """
        Get all records with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        statement = select(self.model).offset(skip).limit(limit)
        return session.exec(statement).all()

    def filter(self, session: Session, filters: Dict[str, Any] = None,
               operators: Dict[str, str] = None,
               order_by: str = None,
               order_desc: bool = False,
               skip: int = 0,
               limit: int = 100) -> List[SQLModel]:
        """
        Filter records based on dynamic criteria.

        Args:
            session: Database session
            filters: Dictionary of field_name: value pairs
            operators: Dictionary of field_name: operator pairs
                      Supported operators: '==', '!=', '>', '<', '>=', '<=', 'contains', 'in', 'like'
            order_by: Field name to order results by
            order_desc: Whether to order in descending order
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered model instances
        """
        statement = select(self.model)

        if filters:
            for field, value in filters.items():
                if not hasattr(self.model, field):
                    continue

                column = getattr(self.model, field)
                operator = operators.get(field, '==') if operators else '=='

                if operator == '==':
                    statement = statement.where(column == value)
                elif operator == '!=':
                    statement = statement.where(column != value)
                elif operator == '>':
                    statement = statement.where(column > value)
                elif operator == '<':
                    statement = statement.where(column < value)
                elif operator == '>=':
                    statement = statement.where(column >= value)
                elif operator == '<=':
                    statement = statement.where(column <= value)
                elif operator == 'contains':
                    statement = statement.where(column.contains(value))
                elif operator == 'in':
                    statement = statement.where(column.in_(value))
                elif operator == 'like':
                    statement = statement.where(column.like(value))

        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                statement = statement.order_by(order_column.desc())
            else:
                statement = statement.order_by(order_column)

        statement = statement.offset(skip).limit(limit)
        return session.exec(statement).all()

    def update(self, session: Session, record_id: Any, data: Dict[str, Any]) -> Optional[SQLModel]:
        """
        Update a record by its primary key.

        Args:
            session: Database session
            record_id: Value of the primary key
            data: Dictionary of field_name: value pairs to update

        Returns:
            Updated model instance or None if not found
        """
        instance = self.get_by_id(session, record_id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            session.add(instance)
            session.commit()
            session.refresh(instance)
        return instance

    def delete(self, session: Session, record_id: Any) -> bool:
        """
        Delete a record by its primary key.

        Args:
            session: Database session
            record_id: Value of the primary key

        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(session, record_id)
        if instance:
            session.delete(instance)
            session.commit()
            return True
        return False

    def count(self, session: Session, filters: Dict[str, Any] = None) -> int:
        """
        Count records with optional filters.

        Args:
            session: Database session
            filters: Optional dictionary of field_name: value pairs

        Returns:
            Count of matching records
        """
        statement = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    column = getattr(self.model, field)
                    statement = statement.where(column == value)

        result = session.exec(statement).first()
        return result if result else 0

    def exists(self, session: Session, record_id: Any) -> bool:
        """
        Check if a record exists by its primary key.

        Args:
            session: Database session
            record_id: Value of the primary key

        Returns:
            True if exists, False otherwise
        """
        return self.get_by_id(session, record_id) is not None

    def execute_custom_query(self, session: Session, statement) -> Any:
        """
        Execute a custom SQLModel query for exceptional cases.

        Args:
            session: Database session
            statement: Custom SQLModel select statement

        Returns:
            Query results
        """
        return session.exec(statement).all()

    def execute_custom_scalar_query(self, session: Session, statement) -> Any:
        """
        Execute a custom query that returns a single scalar value.

        Args:
            session: Database session
            statement: Custom SQLModel select statement

        Returns:
            Scalar result
        """
        return session.exec(statement).first()


# ==================== PRE-CONFIGURED CRUD INSTANCES ====================

# Initialize CRUD instances for each model
customer_crud = UniversalCRUD(Customer, primary_key="customer_id")
product_crud = UniversalCRUD(Product, primary_key="product_id")
store_crud = UniversalCRUD(Store, primary_key="store_id")
order_history_crud = UniversalCRUD(OrderHistory, primary_key="transaction_id")
store_keeper_transaction_crud = UniversalCRUD(
    StoreKeeperTransaction, primary_key="id")
admin_dashboard_data_crud = UniversalCRUD(AdminDashboardData, primary_key="id")
cart_crud = UniversalCRUD(Cart, primary_key="order_id")


# ==================== LEGACY CLASSES (for backward compatibility) ====================
# These classes wrap UniversalCRUD for backward compatibility with existing code

class CustomerCRUD:
    """Legacy wrapper for Customer operations"""
    _crud = customer_crud

    @staticmethod
    def create(session: Session, customer: Customer) -> Customer:
        return customer_crud.create(session, customer)

    @staticmethod
    def get_by_id(session: Session, customer_id: str) -> Optional[Customer]:
        return customer_crud.get_by_id(session, customer_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        return customer_crud.get_all(session, skip, limit)

    @staticmethod
    def filter(
        session: Session,
        customer_name: Optional[str] = None,
        gender: Optional[str] = None,
        min_loyalty_points: Optional[int] = None,
        phone: Optional[str] = None
    ) -> List[Customer]:
        filters = {}
        operators = {}

        if customer_name:
            filters['customer_name'] = customer_name
            operators['customer_name'] = 'contains'
        if gender:
            filters['gender'] = gender
        if min_loyalty_points is not None:
            filters['loyalty_points'] = min_loyalty_points
            operators['loyalty_points'] = '>='
        if phone:
            filters['phone'] = phone

        return customer_crud.filter(session, filters, operators)

    @staticmethod
    def update(session: Session, customer_id: str, data: Dict[str, Any]) -> Optional[Customer]:
        return customer_crud.update(session, customer_id, data)

    @staticmethod
    def delete(session: Session, customer_id: str) -> bool:
        return customer_crud.delete(session, customer_id)


class ProductCRUD:
    """Legacy wrapper for Product operations"""
    _crud = product_crud

    @staticmethod
    def create(session: Session, product: Product) -> Product:
        return product_crud.create(session, product)

    @staticmethod
    def get_by_id(session: Session, product_id: str) -> Optional[Product]:
        return product_crud.get_by_id(session, product_id)

    @staticmethod
    def get_by_id(session: Session, product_id: str) -> Optional[Product]:
        return product_crud.get_by_id(session, product_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        return product_crud.get_all(session, skip, limit)

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
        filters = {}
        operators = {}

        if product_name:
            filters['product_name'] = product_name
            operators['product_name'] = 'contains'
        if category:
            filters['category'] = category
        if gender:
            filters['gender'] = gender
        if min_price is not None:
            filters['price'] = min_price
            operators['price'] = '>='
        if max_price is not None:
            # For max_price, we need a custom approach
            pass  # Handle separately if needed
        if online_available:
            filters['online_available'] = online_available
        if season:
            filters['season'] = season

        results = product_crud.filter(session, filters, operators)

        # Apply max_price filter separately if needed
        if max_price is not None:
            results = [p for p in results if p.price <= max_price]

        return results

    @staticmethod
    def update(session: Session, product_id: str, data: Dict[str, Any]) -> Optional[Product]:
        return product_crud.update(session, product_id, data)

    @staticmethod
    def delete(session: Session, product_id: str) -> bool:
        return product_crud.delete(session, product_id)


class StoreCRUD:
    """Legacy wrapper for Store operations"""
    _crud = store_crud

    @staticmethod
    def create(session: Session, store: Store) -> Store:
        return store_crud.create(session, store)

    @staticmethod
    def get_by_id(session: Session, store_id: str) -> Optional[Store]:
        return store_crud.get_by_id(session, store_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Store]:
        return store_crud.get_all(session, skip, limit)

    @staticmethod
    def filter(
        session: Session,
        store_name: Optional[str] = None,
        manager_name: Optional[str] = None
    ) -> List[Store]:
        filters = {}
        operators = {}

        if store_name:
            filters['store_name'] = store_name
            operators['store_name'] = 'contains'
        if manager_name:
            filters['manager_name'] = manager_name
            operators['manager_name'] = 'contains'

        return store_crud.filter(session, filters, operators)

    @staticmethod
    def update(session: Session, store_id: str, data: Dict[str, Any]) -> Optional[Store]:
        return store_crud.update(session, store_id, data)

    @staticmethod
    def delete(session: Session, store_id: str) -> bool:
        return store_crud.delete(session, store_id)


class OrderHistoryCRUD:
    """Legacy wrapper for OrderHistory operations"""
    _crud = order_history_crud

    @staticmethod
    def create(session: Session, order: OrderHistory) -> OrderHistory:
        return order_history_crud.create(session, order)

    @staticmethod
    def get_by_id(session: Session, transaction_id: str) -> Optional[OrderHistory]:
        return order_history_crud.get_by_id(session, transaction_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[OrderHistory]:
        return order_history_crud.get_all(session, skip, limit)

    @staticmethod
    def filter(
        session: Session,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        min_quantity: Optional[int] = None
    ) -> List[OrderHistory]:
        filters = {}
        operators = {}

        if customer_id:
            filters['customer_id'] = customer_id
        if product_id:
            filters['product_id'] = product_id
        if customer_name:
            filters['customer_name'] = customer_name
            operators['customer_name'] = 'contains'
        if min_quantity is not None:
            filters['quantity'] = min_quantity
            operators['quantity'] = '>='

        return order_history_crud.filter(session, filters, operators)

    @staticmethod
    def get_by_customer(session: Session, customer_id: str) -> List[OrderHistory]:
        return order_history_crud.filter(session, {'customer_id': customer_id})

    @staticmethod
    def update(session: Session, transaction_id: str, data: Dict[str, Any]) -> Optional[OrderHistory]:
        return order_history_crud.update(session, transaction_id, data)

    @staticmethod
    def delete(session: Session, transaction_id: str) -> bool:
        return order_history_crud.delete(session, transaction_id)


class StoreKeeperTransactionCRUD:
    """Legacy wrapper for StoreKeeperTransaction operations"""
    _crud = store_keeper_transaction_crud

    @staticmethod
    def create(session: Session, transaction: StoreKeeperTransaction) -> StoreKeeperTransaction:
        return store_keeper_transaction_crud.create(session, transaction)

    @staticmethod
    def get_by_id(session: Session, transaction_id: int) -> Optional[StoreKeeperTransaction]:
        return store_keeper_transaction_crud.get_by_id(session, transaction_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[StoreKeeperTransaction]:
        return store_keeper_transaction_crud.get_all(session, skip, limit)

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
        filters = {}
        operators = {}

        if customer_id:
            filters['customer_id'] = customer_id
        if product_id:
            filters['product_id'] = product_id
        if store_name:
            filters['store_name'] = store_name
            operators['store_name'] = 'contains'
        if mode:
            filters['mode'] = mode
        if status:
            filters['status'] = status
        if min_amount is not None:
            filters['amount'] = min_amount
            operators['amount'] = '>='

        results = store_keeper_transaction_crud.filter(
            session, filters, operators)

        # Apply max_amount filter separately if needed
        if max_amount is not None:
            results = [t for t in results if t.amount <= max_amount]

        return results

    @staticmethod
    def update(session: Session, transaction_id: int, data: Dict[str, Any]) -> Optional[StoreKeeperTransaction]:
        return store_keeper_transaction_crud.update(session, transaction_id, data)

    @staticmethod
    def delete(session: Session, transaction_id: int) -> bool:
        return store_keeper_transaction_crud.delete(session, transaction_id)


class AdminDashboardDataCRUD:
    """Legacy wrapper for AdminDashboardData operations"""
    _crud = admin_dashboard_data_crud

    @staticmethod
    def create(session: Session, data: AdminDashboardData) -> AdminDashboardData:
        return admin_dashboard_data_crud.create(session, data)

    @staticmethod
    def get_by_id(session: Session, data_id: int) -> Optional[AdminDashboardData]:
        return admin_dashboard_data_crud.get_by_id(session, data_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[AdminDashboardData]:
        return admin_dashboard_data_crud.get_all(session, skip, limit)

    @staticmethod
    def filter(
        session: Session,
        user_name: Optional[str] = None,
        product: Optional[str] = None,
        mode: Optional[str] = None,
        store_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[AdminDashboardData]:
        filters = {}
        operators = {}

        if user_name:
            filters['user_name'] = user_name
            operators['user_name'] = 'contains'
        if product:
            filters['product'] = product
            operators['product'] = 'contains'
        if mode:
            filters['mode'] = mode
        if store_name:
            filters['store_name'] = store_name
            operators['store_name'] = 'contains'
        if status:
            filters['status'] = status

        return admin_dashboard_data_crud.filter(session, filters, operators)

    @staticmethod
    def update(session: Session, data_id: int, data: Dict[str, Any]) -> Optional[AdminDashboardData]:
        return admin_dashboard_data_crud.update(session, data_id, data)

    @staticmethod
    def delete(session: Session, data_id: int) -> bool:
        return admin_dashboard_data_crud.delete(session, data_id)


class CartCRUD:
    """Legacy wrapper for Cart operations"""
    _crud = cart_crud

    @staticmethod
    def create(session: Session, cart: Cart) -> Cart:
        return cart_crud.create(session, cart)

    @staticmethod
    def get_by_id(session: Session, cart_id: int) -> Optional[Cart]:
        return cart_crud.get_by_id(session, cart_id)

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> List[Cart]:
        return cart_crud.get_all(session, skip, limit)

    @staticmethod
    def filter(
        session: Session,
        customer_id: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> List[Cart]:
        filters = {}
        if customer_id:
            filters["customer_id"] = customer_id
        if product_id:
            filters["product_id"] = product_id
        return cart_crud.filter(session, filters=filters)

    @staticmethod
    def get_by_customer(session: Session, customer_id: str) -> List[Cart]:
        return cart_crud.filter(session, filters={"customer_id": customer_id})

    @staticmethod
    def update(session: Session, cart_id: int, data: Dict[str, Any]) -> Optional[Cart]:
        return cart_crud.update(session, cart_id, data)

    @staticmethod
    def delete(session: Session, cart_id: int) -> bool:
        return cart_crud.delete(session, cart_id)


# ==================== ANALYTICS & AGGREGATIONS ====================

class AnalyticsCRUD:
    """Analytics and aggregation queries using custom queries"""

    @staticmethod
    def get_customer_total_spending(session: Session, customer_id: str) -> float:
        """Get total spending for a customer"""
        statement = select(func.sum(StoreKeeperTransaction.amount)).where(
            StoreKeeperTransaction.customer_id == customer_id
        )
        result = store_keeper_transaction_crud.execute_custom_scalar_query(
            session, statement)
        return result if result else 0.0

    @staticmethod
    def get_product_sales_count(session: Session, product_id: str) -> int:
        """Get total sales count for a product"""
        statement = select(func.count(OrderHistory.transaction_id)).where(
            OrderHistory.product_id == product_id
        )
        result = order_history_crud.execute_custom_scalar_query(
            session, statement)
        return result if result else 0

    @staticmethod
    def get_top_customers(session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by loyalty points"""
        customers = customer_crud.filter(
            session,
            filters={},
            order_by='loyalty_points',
            order_desc=True,
            limit=limit
        )
        return [{"customer_id": c.customer_id, "name": c.customer_name, "loyalty_points": c.loyalty_points}
                for c in customers]

    @staticmethod
    def get_store_revenue(session: Session, store_name: str) -> float:
        """Get total revenue for a store"""
        statement = select(func.sum(StoreKeeperTransaction.amount)).where(
            StoreKeeperTransaction.store_name == store_name
        )
        result = store_keeper_transaction_crud.execute_custom_scalar_query(
            session, statement)
        return result if result else 0.0
