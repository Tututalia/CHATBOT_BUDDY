How to apply the `quantity` column migration

Options for teammates to get the `quantity` column in their local database:

1) Run the migration script (recommended)

   - From the repository root, with the project's virtualenv active (Windows PowerShell example):

```powershell
cd backend
& "C:\path\to\your\venv\Scripts\python.exe" migrations\add_quantity_column.py
```

   - If you use the project's venv in `backend/myenv`, run:

```powershell
cd backend
& "C:\Users\sayan\EY_Techathon_Retail_agent\backend\myenv\Scripts\python.exe" migrations\add_quantity_column.py
```

   The script will detect if the `quantity` column already exists and do nothing in that case.

2) Pull the updated SQLite file

   - If you prefer to share the full DB file, commit and push `backend/retail_agent.db` to the repo (note: binary file). Then your teammate can `git pull` to receive the updated DB.

3) Run the SQL manually

   - Using sqlite3 CLI or DB Browser for SQLite, run:

```sql
ALTER TABLE products ADD COLUMN quantity INTEGER DEFAULT 0;
```

Notes & recommendations

- Using a migration script or a proper migration tool (Alembic) is preferable to committing DB binaries.
- If teammates are running different branches or have local DB files, they must either run the script or replace their DB file to see the schema change.

4) Populate non-zero random quantities (optional)

   If you want non-zero random sample quantities similar to what Sayan used, run the population script after applying the migration:

```powershell
cd backend
& "C:\Users\sayan\EY_Techathon_Retail_agent\backend\myenv\Scripts\python.exe" migrations\populate_random_quantities.py --min 1 --max 200 --seed 42 --sample 5
```

   - `--seed` makes values reproducible across machines when teammates use the same seed.
   - Omit `--seed` to get different random values.

Note: the population script now sorts `product_id`s before assigning random quantities, so if all teammates run the script with the same `--seed`, `--min` and `--max` values, they will get identical `quantity` values regardless of their local DB row ordering. However the product set (which product_ids exist) must be the same for identical output.
