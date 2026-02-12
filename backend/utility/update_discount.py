import sqlite3
import random

conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()

# Get all product IDs
cursor.execute("SELECT product_id FROM products")
products = cursor.fetchall()

# Update each product with a random discount between 0 and 50
for product in products:
    product_id = product[0]
    discount = random.randint(0, 50)
    cursor.execute(
        "UPDATE products SET discount = ? WHERE product_id = ?", (discount, product_id))

conn.commit()
print(f'✅ Updated {len(products)} products with random discounts (0-50%)')
conn.close()