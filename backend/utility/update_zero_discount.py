import sqlite3
import random

conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()

# Get all product IDs
cursor.execute("SELECT product_id FROM products")
products = [p[0] for p in cursor.fetchall()]

# Randomly select 14 products
selected_products = random.sample(products, 14)

# Update discount to 0 for selected products
for product_id in selected_products:
    cursor.execute(
        "UPDATE products SET discount = 0 WHERE product_id = ?", (product_id,))

conn.commit()
print(f'✅ Updated discount to 0 for 14 products:')
print(f'   {", ".join(selected_products)}')
conn.close()