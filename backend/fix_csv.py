import pandas as pd

# Read CSV, skipping the first blank line
df = pd.read_csv('data/product_data.csv', skiprows=[0])

# Save back without the blank line
df.to_csv('data/product_data.csv', index=False)

print("Fixed! Removed blank line from product_data.csv")
