# Quick Reference - UniversalCRUD

## Import
```python
from crud import (
    UniversalCRUD,
    customer_crud, product_crud, store_crud,
    order_history_crud, store_keeper_transaction_crud, 
    admin_dashboard_data_crud
)
from database import get_session
```

## Basic Operations

### Create
```python
session = next(get_session())
customer = customer_crud.create(session, {
    "customer_id": "CUST999",
    "customer_name": "John Doe",
    "gender": "Male",
    "phone": "9999999999",
    "address": "123 Street",
    "loyalty_points": 100
})
```

### Read
```python
# Get by ID
customer = customer_crud.get_by_id(session, "CUST001")

# Get all (with pagination)
customers = customer_crud.get_all(session, skip=0, limit=50)

# Check if exists
exists = customer_crud.exists(session, "CUST001")

# Count records
total = customer_crud.count(session)
```

### Update
```python
updated = customer_crud.update(session, "CUST001", {
    "loyalty_points": 500,
    "address": "New Address"
})
```

### Delete
```python
deleted = customer_crud.delete(session, "CUST001")
```

## Filtering Examples

### Simple Filter (Exact Match)
```python
products = product_crud.filter(
    session=session,
    filters={"category": "Shirt", "gender": "Male"}
)
```

### Greater Than / Less Than
```python
products = product_crud.filter(
    session=session,
    filters={"price": 1500},
    operators={"price": ">="}  # >= 1500
)
```

### String Contains
```python
customers = customer_crud.filter(
    session=session,
    filters={"customer_name": "Arjun"},
    operators={"customer_name": "contains"}
)
```

### IN Operator (Multiple Values)
```python
products = product_crud.filter(
    session=session,
    filters={"category": ["Shirt", "Jeans", "Jacket"]},
    operators={"category": "in"}
)
```

### LIKE Operator
```python
products = product_crud.filter(
    session=session,
    filters={"product_name": "%Nike%"},
    operators={"product_name": "like"}
)
```

### Multiple Conditions with Ordering
```python
products = product_crud.filter(
    session=session,
    filters={
        "category": "Shirt",
        "price": 1000,
        "gender": "Male"
    },
    operators={
        "price": ">="
    },
    order_by="price",
    order_desc=True,
    limit=10
)
```

## Bulk Operations
```python
# Bulk create
customers_data = [
    {"customer_id": "C001", "customer_name": "Alice", ...},
    {"customer_id": "C002", "customer_name": "Bob", ...},
]
created = customer_crud.bulk_create(session, customers_data)
```

## Custom Queries

### Simple Custom Query
```python
from sqlmodel import select
from models import Product

statement = select(Product).where(
    (Product.price >= 1000) & (Product.price <= 3000)
)
results = product_crud.execute_custom_query(session, statement)
```

### Aggregation Query
```python
from sqlmodel import select, func
from models import Customer

# Average loyalty points
avg_query = select(func.avg(Customer.loyalty_points))
avg_value = customer_crud.execute_custom_scalar_query(session, avg_query)
```

### JOIN Query
```python
from sqlmodel import select
from models import Customer, OrderHistory

statement = select(Customer, OrderHistory).join(
    OrderHistory,
    Customer.customer_id == OrderHistory.customer_id
)
results = customer_crud.execute_custom_query(session, statement)
```

## Operators Reference

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal (default) | `{"gender": "Male"}` |
| `!=` | Not equal | `{"status": "Pending"}` with `{"status": "!="}` |
| `>` | Greater than | `{"price": 1000}` with `{"price": ">"}` |
| `<` | Less than | `{"price": 5000}` with `{"price": "<"}` |
| `>=` | Greater or equal | `{"loyalty_points": 500}` with `{"loyalty_points": ">="}` |
| `<=` | Less or equal | `{"quantity": 10}` with `{"quantity": "<="}` |
| `contains` | String contains | `{"name": "John"}` with `{"name": "contains"}` |
| `in` | Value in list | `{"category": ["A", "B"]}` with `{"category": "in"}` |
| `like` | SQL LIKE | `{"name": "%test%"}` with `{"name": "like"}` |

## Creating Custom CRUD Instance

```python
from crud import UniversalCRUD
from models import YourModel

# Create CRUD instance for any model
your_crud = UniversalCRUD(YourModel, primary_key="your_primary_key")

# Use it like any other CRUD instance
records = your_crud.get_all(session)
```

## Common Patterns

### Search and Update
```python
# Find customer by phone
customers = customer_crud.filter(session, {"phone": "9876543210"})
if customers:
    customer_crud.update(session, customers[0].customer_id, {
        "loyalty_points": customers[0].loyalty_points + 100
    })
```

### Conditional Delete
```python
# Delete low-value inactive customers
inactive = customer_crud.filter(
    session=session,
    filters={"loyalty_points": 50},
    operators={"loyalty_points": "<"}
)
for customer in inactive:
    customer_crud.delete(session, customer.customer_id)
```

### Pagination Loop
```python
page_size = 50
page = 0
while True:
    customers = customer_crud.get_all(session, skip=page * page_size, limit=page_size)
    if not customers:
        break
    
    # Process customers
    for customer in customers:
        print(customer.customer_name)
    
    page += 1
```

## Error Handling

```python
try:
    customer = customer_crud.get_by_id(session, "CUST999")
    if customer is None:
        print("Customer not found")
    else:
        # Process customer
        pass
except Exception as e:
    print(f"Database error: {e}")
    session.rollback()
```

## Tips

1. **Always use sessions properly** - Get from `get_session()` and close when done
2. **Use pre-configured instances** - `customer_crud`, `product_crud`, etc.
3. **Leverage filters over custom queries** - Simpler and more maintainable
4. **Use bulk operations** - Much faster for multiple records
5. **Add indexes on filter columns** - Improves query performance
