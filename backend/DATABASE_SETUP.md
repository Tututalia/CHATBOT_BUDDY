# Database Setup Guide

## Overview
This project uses SQLite for local development. The database files (`.db`) are **NOT tracked in git** to avoid conflicts. Each team member needs to set up their own local database.

## Quick Setup for New Team Members

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Run Database Setup
```bash
python setup_database.py
```

This script will automatically:
- Create all required database tables
- Import data from CSV files in `data/` directory
- Verify the setup

### Step 3: Start the Backend
```bash
python main.py
```

## Manual Setup (Alternative)

If the automated setup doesn't work, run these commands in order:

```bash
# 1. Create tables
python create_tables.py

# 2. Import data (optional - may have some errors)
python import_data.py

# 3. Verify tables exist
python view_tables.py
```

## Available CSV Data Files

The following CSV files contain the initial data:
- `data/customer_data.csv` - Customer information
- `data/product_data.csv` - Product catalog
- `data/outlate_data.csv` - Store/outlet information
- `data/order_history.csv` - Historical orders
- `data/cart.csv` - Shopping cart data
- `data/admin_dashboard_data.csv` - Admin metrics
- `data/store keeper transaction data.csv` - Store transactions

## Database Files (Not in Git)

These files are in `.gitignore` and won't be pushed to the repository:
- `retail_agent.db` - Main application database
- `chat_history.db` - Chat conversation history
- Any other `*.db` or `*.sqlite3` files

## Sharing Database Changes

### Option 1: Export to CSV (Recommended)
If you make changes to the database structure or data that others need:

```bash
python backup_sqlite_to_csv.py
```

This exports all tables to CSV files in the `data/` directory. Commit these CSV files to git.

### Option 2: Migration Scripts
For schema changes, create a migration script in the `migrations/` folder:

```bash
# Example
python migrations/add_new_column.py
```

## Troubleshooting

### Problem: ModuleNotFoundError
**Solution:** Make sure you've activated the virtual environment and installed dependencies:
```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
source .venv/bin/activate
pip install -r requirements.txt
```

### Problem: CSV Import Errors
**Solution:** Some CSV files may have formatting issues. The database will still work with partial data. You can:
1. Fix the CSV file manually
2. Add data through the application
3. Use the CRUD operations in `crud.py`

### Problem: Tables Don't Exist
**Solution:** Run the table creation script:
```bash
python create_tables.py
```

### Problem: Database is Locked
**Solution:** Close any programs accessing the database (including DB browsers), then restart the backend.

## Database Schema

See `models.py` for the complete database schema including:
- Customers
- Products
- Stores
- OrderHistory
- Cart
- StoreKeeperTransactions
- AdminDashboardData
- Roles

## Need Help?

Check these files for more information:
- `CRUD_README.md` - Database operations guide
- `CRUD_QUICK_REFERENCE.md` - Quick reference for CRUD operations
- `models.py` - Database schema definitions
- `database.py` - Database connection setup
