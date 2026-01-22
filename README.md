# EY Techathon Retail Agent

Short instructions to run the project (backend + frontend), dependencies, and file layout.

## Overview

This repository contains a simple Retail Agent demo with a Python FastAPI backend and a React (Vite) frontend.

## Prerequisites

- Python 3.11+ (3.10 may work) for the backend
- Node.js 16+ and npm for the frontend

## Backend (Python / FastAPI)

1. Open a terminal and change into the backend folder:

```bash
cd backend
```

2. (Recommended) Create and activate a virtual environment:

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install fastapi uvicorn pandas
```

4. Start the backend API (development mode):

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000` and the OpenAPI docs at `http://127.0.0.1:8000/docs`.

Notes: the backend reads CSV files from `backend/data/` (for example `product_data.csv` and `customer_data.csv`).

## Frontend (React / Vite)

1. Open a terminal and change into the frontend folder:

```bash
cd frontend
```

2. Install node dependencies:

```bash
npm install
```

3. Start the frontend dev server:

```bash
npm run dev
```

The Vite dev server runs on port `5173` by default. The frontend expects the backend APIs at `http://127.0.0.1:8000`.

## Important Dependencies

- Backend: `fastapi`, `uvicorn`, `pandas`
- Frontend: dependencies are in `frontend/package.json` (React, react-router-dom, recharts, vite)

If you prefer pinning dependencies, create `backend/requirements.txt` with the packages above and run `pip install -r backend/requirements.txt`.

## File structure (top-level)

- `backend/` - Python API service
  - `main.py` - FastAPI application
  - `model.py` - (model helpers, if used)
  - `data/` - CSV and JSON data files used by the backend

- `frontend/` - React + Vite app
  - `package.json` - frontend dependencies and scripts
  - `pages/`, `pages.jsx`, `App.jsx` - React components and routes

- `myenv/` - optional local virtual environment (already present in this workspace)

## Useful API endpoints (examples)

- `GET /` — simple greeting
- `GET /productdatabase/` — list all products
- `GET /productdatabase/{product_id}` — product by id
- `GET /api/customer/{customer_id}` — customer profile

## Next steps / tips

- If you plan to deploy, add `backend/requirements.txt` with pinned versions and a `Procfile` or containerize the app.
- If CSV files are missing or corrupted, the backend endpoints will return an error. Confirm `backend/data/` contains the expected CSVs.

---

If you want, I can also create a `backend/requirements.txt` with pinned versions and add a short `Makefile` or start scripts. Would you like that?
