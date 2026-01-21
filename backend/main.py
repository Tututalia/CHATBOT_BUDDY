from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from typing import Dict, Any, List

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000",
                   "http://127.0.0.1:5173"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CSV data using pandas


def load_csv_data():
    """Load product data from CSV using pandas"""
    try:
        csv_file_path = os.path.join(os.path.dirname(
            __file__), "data", "product_data.csv")
        df = pd.read_csv(csv_file_path)
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


def load_customer_data():
    """Load customer data from CSV using pandas"""
    try:
        csv_file_path = os.path.join(os.path.dirname(
            __file__), "data", "customer_data.csv")
        # Using tab separator as shown in the CSV
        df = pd.read_csv(csv_file_path, sep='\t')
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        return None


@app.get("/")
def greet():
    return {"message": "Hello world"}


@app.get("/productdatabase/")
def get_products_from_database():
    """Get all products from CSV database using pandas"""
    df = load_csv_data()

    if df is None:
        return {"error": "Failed to load CSV data"}

    # Convert DataFrame to list of dictionaries
    products = df.to_dict('records')

    return {
        "total_products": len(products),
        "products": products
    }


@app.get("/productdatabase/{product_id}")
def get_product_by_id_from_database(product_id: str):
    """Get a specific product by ID from CSV database using pandas"""
    df = load_csv_data()

    if df is None:
        return {"error": "Failed to load CSV data"}

    # Filter DataFrame by product_id
    product_row = df[df['product_id'] == product_id]

    if product_row.empty:
        return {"error": f"Product with ID {product_id} not found"}

    # Convert to dictionary
    product = product_row.iloc[0].to_dict()
    return product


@app.get("/productdatabase/category/{category}")
def get_products_by_category(category: str):
    """Get products by category using pandas"""
    df = load_csv_data()

    if df is None:
        return {"error": "Failed to load CSV data"}

    # Filter DataFrame by category (case insensitive)
    category_products = df[df['category'].str.lower() == category.lower()]

    if category_products.empty:
        return {"error": f"No products found in category: {category}"}

    products = category_products.to_dict('records')

    return {
        "category": category,
        "total_products": len(products),
        "products": products
    }


@app.get("/productdatabase/price-range/")
def get_products_by_price_range(min_price: float = 0, max_price: float = 10000):
    """Get products within a price range using pandas"""
    df = load_csv_data()

    if df is None:
        return {"error": "Failed to load CSV data"}

    # Filter DataFrame by price range
    price_filtered = df[(df['price'] >= min_price) &
                        (df['price'] <= max_price)]

    if price_filtered.empty:
        return {"error": f"No products found in price range {min_price} - {max_price}"}

    products = price_filtered.to_dict('records')

    return {
        "price_range": f"{min_price} - {max_price}",
        "total_products": len(products),
        "products": products
    }


@app.get("/api/customer/{customer_id}")
def get_customer_profile(customer_id: str):
    """Get customer profile by customer ID"""
    df = load_customer_data()

    if df is None:
        return {"error": "Failed to load customer data"}

    # Filter DataFrame by customer_id
    customer_row = df[df['customer_id'] == customer_id]

    if customer_row.empty:
        return {"error": f"Customer with ID {customer_id} not found"}

    # Convert to dictionary
    customer = customer_row.iloc[0].to_dict()

    # Parse order history (comma-separated product IDs)
    order_history = []
    if pd.notna(customer.get('order_history')):
        product_ids = customer['order_history'].split(',')
        order_history = [pid.strip() for pid in product_ids]

    # Parse pending orders
    pending_orders = []
    if pd.notna(customer.get('pending_orders')):
        product_ids = customer['pending_orders'].split(',')
        pending_orders = [pid.strip() for pid in product_ids]

    return {
        "customer_id": customer['customer_id'],
        "customer_name": customer['customer_name'],
        "loyalty_points": customer['loyalty_points'],
        "order_history": order_history,
        "pending_orders": pending_orders
    }


@app.get("/api/customer/{customer_id}/orders")
def get_customer_orders(customer_id: str):
    """Get customer's order history with product details"""
    # First get customer data
    customer_df = load_customer_data()
    product_df = load_csv_data()

    if customer_df is None or product_df is None:
        return {"error": "Failed to load data"}

    # Find customer
    customer_row = customer_df[customer_df['customer_id'] == customer_id]

    if customer_row.empty:
        return {"error": f"Customer with ID {customer_id} not found"}

    customer = customer_row.iloc[0].to_dict()

    # Get order history product IDs
    order_products = []
    if pd.notna(customer.get('order_history')):
        product_ids = customer['order_history'].split(',')
        product_ids = [pid.strip() for pid in product_ids]

        # Get product details for each product ID
        for pid in product_ids:
            product_row = product_df[product_df['product_id'] == pid]
            if not product_row.empty:
                product = product_row.iloc[0].to_dict()
                order_products.append(product)

    return {
        "customer_id": customer_id,
        "order_history": order_products
    }


@app.get("/api/products/multiple/{product_ids}")
def get_multiple_products(product_ids: str):
    """Get multiple products by comma-separated product IDs"""
    df = load_csv_data()

    if df is None:
        return {"error": "Failed to load product data"}

    # Split product IDs and clean them
    ids_list = [pid.strip() for pid in product_ids.split(',')]

    # Filter products by the list of IDs
    products = df[df['product_id'].isin(ids_list)].to_dict('records')

    return {
        "products": products,
        "total_count": len(products)
    }
