from fastapi import FastAPI
import pandas as pd
import os
from typing import Dict, Any, List

app = FastAPI()

# Load CSV data using pandas


def load_csv_data():
    """Load product data from CSV using pandas"""
    try:
        csv_file_path = os.path.join(os.path.dirname(
            __file__), "Data", "product_data.csv")
        df = pd.read_csv(csv_file_path)
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
