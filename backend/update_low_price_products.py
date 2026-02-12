import sqlite3
import random

conn = sqlite3.connect('retail_agent.db')
cursor = conn.cursor()

# Get products with price less than 6000 (to avoid premium products)
cursor.execute("SELECT product_id FROM products WHERE price < 6000")
products = [p[0] for p in cursor.fetchall()]

# Select 15-20 products to reduce price to below 1000
num_products = random.randint(15, 20)
selected_products = random.sample(products, min(num_products, len(products)))

# Update prices to below 1000 and discount to 55-60
for product_id in selected_products:
    new_price = random.randint(200, 999)  # Price below 1000
    new_discount = random.randint(55, 60)  # High discount 55-60%
    cursor.execute("UPDATE products SET price = ?, discount = ? WHERE product_id = ?",
                   (new_price, new_discount, product_id))

conn.commit()
print(
    f'✅ Updated {len(selected_products)} products with prices below 1000 and discount 55-60%')
print(f'   Updated products: {", ".join(selected_products)}')
print(f'   This should help create 8-9 tier_3 customers')
conn.close()