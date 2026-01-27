# Universal CRUD System Documentation

## Overview

The `crud.py` file has been refactored to use a single **UniversalCRUD** class that handles all database operations dynamically. This eliminates code duplication and provides a flexible, maintainable approach to database operations.

## Key Features

✅ **Single Class for All Models** - One `UniversalCRUD` class handles all CRUD operations  
✅ **Dynamic Filtering** - Support for multiple operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `in`, `like`  
✅ **Flexible Operations** - Create, Read, Update, Delete, Count, Exists, Bulk Create  
✅ **Custom Queries** - Execute custom SQLModel queries for exceptional cases  
✅ **Backward Compatible** - Legacy class wrappers maintain existing API  
✅ **Type-Safe** - Full type hints and SQLModel integration

---

## Quick Start

### 1. Using Pre-configured Instances

Pre-configured CRUD instances are available for immediate use:

```python
from crud import customer_crud, product_crud, store_crud
from database import get_session

session = next(get_session())

# Get a customer
customer = customer_crud.get_by_id(session, "CUST001")

# Update customer
customer_crud.update(session, "CUST001", {
    "loyalty_points": 500,
    "address": "New Address"
})

# Filter products
products = product_crud.filter(
    session=session,
    filters={"category": "Shirt", "price": 1500},
    operators={"price": ">="}
)
```

### 2. Creating Custom CRUD Instance

Create a CRUD instance for any SQLModel:

```python
from crud import UniversalCRUD
from models import Product

# Create CRUD instance
product_ops = UniversalCRUD(Product, primary_key="product_id")

# Use it
all_products = product_ops.get_all(session, limit=10)
```

---

## Available CRUD Instances

```python
customer_crud                 # Customer operations (primary_key: customer_id)
product_crud                  # Product operations (primary_key: product_id)
store_crud                    # Store operations (primary_key: store_id)
order_history_crud            # Order History operations (primary_key: transaction_id)
store_keeper_transaction_crud # StoreKeeper Transaction operations (primary_key: id)
admin_dashboard_data_crud     # Admin Dashboard operations (primary_key: id)
```

---

## UniversalCRUD Methods

### 1. **create(session, data)**
Create a new record

```python
# Using dict
new_customer = customer_crud.create(session, {
    "customer_id": "CUST999",
    "customer_name": "John Doe",
    "gender": "Male",
    "phone": "9999999999",
    "address": "123 Street",
    "loyalty_points": 100
})

# Using model instance
customer = Customer(customer_id="CUST999", customer_name="John Doe", ...)
created = customer_crud.create(session, customer)
```

### 2. **bulk_create(session, data_list)**
Create multiple records at once

```python
customers_data = [
    {"customer_id": "CUST001", "customer_name": "Alice", ...},
    {"customer_id": "CUST002", "customer_name": "Bob", ...},
]
created_list = customer_crud.bulk_create(session, customers_data)
```

### 3. **get_by_id(session, record_id)**
Get a single record by primary key

```python
customer = customer_crud.get_by_id(session, "CUST001")
product = product_crud.get_by_id(session, "PRD001")
```

### 4. **get_all(session, skip=0, limit=100)**
Get all records with pagination

```python
customers = customer_crud.get_all(session, skip=0, limit=50)
```

### 5. **filter(session, filters, operators, order_by, order_desc, skip, limit)**
Dynamic filtering with multiple operators

```python
# Simple filter
products = product_crud.filter(
    session=session,
    filters={"category": "Shirt", "gender": "Male"}
)

# Advanced filter with operators
products = product_crud.filter(
    session=session,
    filters={
        "price": 1500,
        "category": "Shirt"
    },
    operators={
        "price": ">="  # Price >= 1500
    },
    order_by="price",
    order_desc=True,
    limit=10
)

# Contains operator
customers = customer_crud.filter(
    session=session,
    filters={"customer_name": "Arjun"},
    operators={"customer_name": "contains"}
)

# IN operator (multiple values)
products = product_crud.filter(
    session=session,
    filters={"category": ["Shirt", "Jeans", "Jacket"]},
    operators={"category": "in"}
)

# LIKE operator (SQL pattern)
products = product_crud.filter(
    session=session,
    filters={"product_name": "%Nike%"},
    operators={"product_name": "like"}
)
```

**Supported Operators:**
- `==` - Equal (default)
- `!=` - Not equal
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `contains` - String contains (case-insensitive)
- `in` - Value in list
- `like` - SQL LIKE pattern matching

### 6. **update(session, record_id, data)**
Update a record by primary key

```python
updated = customer_crud.update(session, "CUST001", {
    "loyalty_points": 500,
    "address": "New Address",
    "phone": "9999999999"
})
```

### 7. **delete(session, record_id)**
Delete a record by primary key

```python
deleted = customer_crud.delete(session, "CUST001")  # Returns True/False
```

### 8. **count(session, filters=None)**
Count records with optional filters

```python
# Count all customers
total = customer_crud.count(session)

# Count with filters
male_count = customer_crud.count(session, filters={"gender": "Male"})
```

### 9. **exists(session, record_id)**
Check if a record exists

```python
if customer_crud.exists(session, "CUST001"):
    print("Customer exists!")
```

### 10. **execute_custom_query(session, statement)**
Execute custom SQLModel query for complex cases

```python
from sqlmodel import select
from models import Product

# Custom query
statement = select(Product).where(
    (Product.price >= 1000) & (Product.price <= 3000)
).order_by(Product.price.desc())

results = product_crud.execute_custom_query(session, statement)
```

### 11. **execute_custom_scalar_query(session, statement)**
Execute custom query that returns a single value

```python
from sqlmodel import select, func
from models import Customer

# Get average loyalty points
avg_query = select(func.avg(Customer.loyalty_points))
avg_value = customer_crud.execute_custom_scalar_query(session, avg_query)
```

---

## Advanced Examples

### Example 1: Complex Filtering

```python
# Get high-value male customers from Kolkata
customers = customer_crud.filter(
    session=session,
    filters={
        "gender": "Male",
        "loyalty_points": 500,
        "address": "Kolkata"
    },
    operators={
        "loyalty_points": ">=",
        "address": "contains"
    },
    order_by="loyalty_points",
    order_desc=True,
    limit=20
)
```

### Example 2: Multi-Step Operation

```python
# 1. Check if customer exists
if customer_crud.exists(session, "CUST001"):
    
    # 2. Get customer details
    customer = customer_crud.get_by_id(session, "CUST001")
    
    # 3. Update loyalty points
    new_points = customer.loyalty_points + 100
    customer_crud.update(session, "CUST001", {
        "loyalty_points": new_points
    })
```

### Example 3: Custom Analytics Query

```python
from sqlmodel import select, func
from models import StoreKeeperTransaction

# Get total revenue by store
statement = select(
    StoreKeeperTransaction.store_name,
    func.sum(StoreKeeperTransaction.amount).label("total_revenue")
).group_by(
    StoreKeeperTransaction.store_name
).order_by(
    func.sum(StoreKeeperTransaction.amount).desc()
)

results = store_keeper_transaction_crud.execute_custom_query(session, statement)

for row in results:
    print(f"{row.store_name}: ₹{row.total_revenue}")
```

### Example 4: Bulk Operations

```python
# Bulk create products
products_data = [
    {
        "product_id": f"PRD{i}",
        "product_name": f"Product {i}",
        "category": "Test",
        "gender": "Unisex",
        "price": 999 + i,
        "online_available": "Yes",
        "offline_available": "No",
        "season": "All Season",
        "image_reference": f"/images/PRD{i}.jpg",
        "loyalty_points": 10
    }
    for i in range(1, 11)
]

created_products = product_crud.bulk_create(session, products_data)
print(f"Created {len(created_products)} products")
```

---

## Legacy Classes (Backward Compatibility)

The legacy CRUD classes (`CustomerCRUD`, `ProductCRUD`, etc.) are still available and work exactly as before. They now use `UniversalCRUD` internally:

```python
from crud import CustomerCRUD

# Old API still works
customer = CustomerCRUD.get_by_id(session, "CUST001")
CustomerCRUD.update(session, "CUST001", {"loyalty_points": 500})
```

---

## When to Use Custom Queries

Use `execute_custom_query()` for:
- Complex JOINs across multiple tables
- Advanced aggregations (GROUP BY, HAVING)
- Subqueries
- Raw SQL operations
- Performance-critical queries

```python
# Example: Complex JOIN query
from sqlmodel import select
from models import Customer, OrderHistory

statement = select(Customer, OrderHistory).join(
    OrderHistory, Customer.customer_id == OrderHistory.customer_id
).where(
    OrderHistory.quantity > 2
)

results = customer_crud.execute_custom_query(session, statement)
```

---

## Best Practices

1. **Use Pre-configured Instances** - Use `customer_crud`, `product_crud`, etc. for common operations
2. **Leverage Filters** - Use the `filter()` method with operators instead of custom queries when possible
3. **Bulk Operations** - Use `bulk_create()` for inserting multiple records
4. **Custom Queries for Complex Cases** - Use `execute_custom_query()` only when the built-in methods can't handle your use case
5. **Always Use Sessions Properly** - Get sessions from `get_session()` and ensure they're closed

---

## Migration Guide

If you have existing code using the old CRUD classes:

**Before:**
```python
from crud import ProductCRUD

products = ProductCRUD.filter(
    session,
    category="Shirt",
    min_price=1500
)
```

**After (Recommended):**
```python
from crud import product_crud

products = product_crud.filter(
    session=session,
    filters={"category": "Shirt", "price": 1500},
    operators={"price": ">="}
)
```

**Note:** The old API still works, so no immediate changes are required!

---

## Summary

The new `UniversalCRUD` class provides:
- ✅ Less code duplication
- ✅ More flexibility
- ✅ Dynamic filtering with multiple operators
- ✅ Better maintainability
- ✅ Full backward compatibility
- ✅ Support for custom queries

You can now handle most database operations with a single class while keeping custom query support for exceptional cases!
