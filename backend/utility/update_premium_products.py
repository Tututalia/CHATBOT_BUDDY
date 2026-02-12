import sqlite3
import random

conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()

# Get all product IDs
cursor.execute("SELECT product_id FROM products")
products = [p[0] for p in cursor.fetchall()]

# Randomly select 14 products
selected_products = random.sample(products, 14)

# Update each selected product
for product_id in selected_products:
    price = random.randint(6501, 15000)  # Price more than 6500
    discount = random.randint(0, 3)  # Very low discount (0-3%)
    loyalty_points = random.randint(30, 50)  # Low loyalty points (30-50)

    cursor.execute("""
        UPDATE products 
        SET price = ?, discount = ?, loyalty_points = ? 
        WHERE product_id = ?
    """, (price, discount, loyalty_points, product_id))

conn.commit()
print(f'✅ Updated 14 premium products:')
print(f'   - Price: >6500')
print(f'   - Discount: 0-3%')
print(f'   - Loyalty Points: 30-50')
print(f'\nUpdated products: {", ".join(selected_products)}')
conn.close()