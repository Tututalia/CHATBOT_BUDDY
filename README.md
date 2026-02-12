# 🛒 EY Techathon — Intelligent Retail Agent

An AI-powered retail assistant platform built for the EY Techathon. The system leverages **LangGraph** and **OpenAI GPT** to deliver an intelligent, multi-agent shopping experience across online, in-store kiosk, and WhatsApp channels.

---

## 📌 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [Database](#database)

---

## ✨ Features

- **Intelligent Sales Agent** — AI-driven conversational agent that helps customers browse products, get recommendations, and complete purchases.
- **Store Kiosk Mode** — In-store kiosk workflow for offline customers with pending cart items, payment processing, and loyalty point management.
- **WhatsApp Integration** — Interact with the retail agent directly via WhatsApp using the Meta Cloud API.
- **Multi-Channel Support** — Seamless experience across online and offline (in-store) channels.
- **Upsell & Cross-Sell Agent** — Automatically suggests complementary products and upsell opportunities.
- **Loyalty Points System** — Earn and track loyalty points with every purchase; tiered customer classification (Tier 1/2/3).
- **Google Maps Integration** — Find nearest stores, get distance and directions via Google Maps API.
- **Admin Dashboard** — View sales analytics, transaction history, and monthly performance data.
- **Store Keeper Portal** — Manage store inventory, view transactions, and oversee order fulfillment.
- **Cart Management** — Full cart functionality with add/remove/update across online and offline channels.
- **Order History Tracking** — Complete order history with status tracking and feedback collection.
- **Webhook Security** — HMAC signature verification for WhatsApp webhook payloads.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)             │
│  ┌──────────┐  ┌────────────┐  ┌───────┐  ┌─────────┐  │
│  │   Home   │  │  Customer  │  │ Admin │  │  Store   │  │
│  │   Page   │  │  Journey   │  │ Panel │  │ Keeper  │  │
│  └──────────┘  └────────────┘  └───────┘  └─────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ REST / WebSocket
┌───────────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI + LangGraph)           │
│  ┌────────────────────┐  ┌───────────────────────────┐  │
│  │ Intelligent Agent  │  │   Store Kiosk Agent       │  │
│  │   Graph (Online)   │  │   Graph (Offline)         │  │
│  └────────┬───────────┘  └───────────┬───────────────┘  │
│           │   ┌───────────────┐      │                  │
│           ├──►│  OpenAI GPT   │◄─────┤                  │
│           │   └───────────────┘      │                  │
│  ┌────────▼──────────────────────────▼───────────────┐  │
│  │              SQLite Database (SQLModel)            │  │
│  │  Customers │ Products │ Orders │ Cart │ Stores     │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │  WhatsApp API   │  │      Google Maps API         │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer      | Technology                                       |
| ---------- | ------------------------------------------------ |
| Frontend   | React 18, Vite, React Router, Recharts, Axios    |
| Backend    | Python, FastAPI, Uvicorn, WebSockets             |
| AI/LLM     | LangGraph, LangChain, OpenAI GPT-4o-mini         |
| Database   | SQLite with SQLModel ORM                         |
| Maps       | Google Maps Directions API, @react-google-maps   |
| Messaging  | Meta WhatsApp Cloud API                          |
| Charts     | Recharts                                         |

---

## 📁 Project Structure

```
EY_Techathon_Retail_agent/
├── backend/
│   ├── main.py                    # FastAPI app, REST & WebSocket endpoints
│   ├── intelligent_agent_graph.py # LangGraph agent for online shopping
│   ├── store_kiosk_graph.py       # LangGraph agent for in-store kiosk
│   ├── models.py                  # SQLModel database models
│   ├── database.py                # Database engine & session management
│   ├── crud.py                    # Universal CRUD operations
│   ├── config.py                  # Environment config loader
│   ├── security.py                # Webhook HMAC signature validation
│   ├── whatsapp.py                # WhatsApp Cloud API integration
│   ├── google_map.py              # Google Maps distance & directions
│   ├── chat_database.py           # Chat history persistence
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variable template
│   ├── data/                      # CSV/JSON seed data files
│   ├── migrations/                # Database migration scripts
│   └── utility/                   # Helper scripts & testing utilities
│
├── frontend/
│   ├── App.jsx                    # Main chat UI component
│   ├── pages.jsx                  # Route definitions & login logic
│   ├── main.jsx                   # React entry point
│   ├── index.html                 # HTML template
│   ├── package.json               # Node.js dependencies
│   ├── agents.json                # Online agent workflow config
│   ├── storeAgent.json            # Store kiosk agent workflow config
│   ├── AdminDataContext.jsx       # Admin data context provider
│   ├── pages/
│   │   ├── Home.jsx               # Landing page
│   │   ├── UserJourney.jsx        # Customer shopping journey
│   │   ├── StoreKeeper.jsx        # Store keeper portal
│   │   └── Admin.jsx              # Admin dashboard
│   └── src/
│       └── components/            # Reusable UI components
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **npm** or **yarn**
- An **OpenAI API key**
- (Optional) **Google Maps API key** for store directions
- (Optional) **Meta WhatsApp Business** account for WhatsApp channel

### Backend Setup

```bash
# Navigate to the backend directory
cd EY_Techathon_Retail_agent/backend

# Create a virtual environment
python -m venv myenv

# Activate the virtual environment
# Windows
myenv\Scripts\activate
# macOS/Linux
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the example env file and fill in your keys
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section)

# Run database setup (first time only)
python utility/create_tables.py
python utility/import_data.py

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
# Navigate to the frontend directory
cd EY_Techathon_Retail_agent/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory using `.env.example` as a template:

| Variable              | Required | Description                                        |
| --------------------- | -------- | -------------------------------------------------- |
| `OPENAI_API_KEY`      | Yes      | OpenAI API key for GPT model access                |
| `OPENAI_ASSISTANT_ID` | Yes      | OpenAI Assistant ID for WhatsApp agent              |
| `GOOGLE_MAPS_API_KEY` | No       | Google Maps API key for store distance/directions   |
| `ACCESS_TOKEN`        | No       | Meta WhatsApp Cloud API access token                |
| `APP_ID`              | No       | Meta App ID for WhatsApp integration                |
| `APP_SECRET`          | No       | Meta App Secret for webhook signature verification  |
| `RECIPIENT_WAID`      | No       | Default WhatsApp recipient number (with country code) |
| `VERSION`             | No       | Meta Graph API version (default: `v18.0`)           |
| `PHONE_NUMBER_ID`     | No       | WhatsApp Business phone number ID                   |
| `VERIFY_TOKEN`        | No       | Webhook verification token                          |

---

## 📡 API Endpoints

### REST Endpoints

| Method | Endpoint                        | Description                          |
| ------ | ------------------------------- | ------------------------------------ |
| GET    | `/products`                     | List all products (with filters)     |
| GET    | `/products/{id}`                | Get product by ID                    |
| GET    | `/customers/{id}`               | Get customer details                 |
| GET    | `/orders/{customer_id}`         | Get order history for a customer     |
| POST   | `/cart/add`                     | Add item to cart                     |
| GET    | `/cart/{customer_id}`           | Get cart items                       |
| DELETE | `/cart/{customer_id}/{item_id}` | Remove item from cart                |
| GET    | `/stores`                       | List all stores                      |
| GET    | `/admin/dashboard`              | Admin dashboard data                 |
| POST   | `/webhook`                      | WhatsApp webhook (incoming messages) |
| GET    | `/webhook`                      | WhatsApp webhook verification        |

### WebSocket

| Endpoint        | Description                              |
| --------------- | ---------------------------------------- |
| `/ws/chat`      | Real-time chat with the AI sales agent   |
| `/ws/kiosk`     | Real-time chat for store kiosk mode      |

---

## 👥 User Roles

| Role             | Access                                                    |
| ---------------- | --------------------------------------------------------- |
| **Customer**     | Browse products, chat with AI agent, manage cart, checkout |
| **Store Keeper** | View store transactions, manage inventory                 |
| **Admin**        | Full dashboard access, analytics, transaction management  |
| **Kiosk User**   | In-store self-service checkout for pending offline orders  |

---

## 🗄️ Database

The project uses **SQLite** with **SQLModel** ORM. Key tables:

| Table                        | Description                            |
| ---------------------------- | -------------------------------------- |
| `customers`                  | Customer profiles, loyalty points, tier|
| `products`                   | Product catalog with availability      |
| `stores`                     | Store locations and details            |
| `order_history`              | Completed orders                       |
| `cart`                       | Active cart items (online & offline)   |
| `store_keeper_transactions`  | Store-level transaction records        |
| `admin_dashboard_data`       | Aggregated dashboard metrics           |
| `feedback`                   | Customer feedback on orders            |
| `role`                       | User role definitions                  |
| `distance`                   | Precomputed store distances            |

Seed data is located in `backend/data/` and can be imported using the utility scripts in `backend/utility/`.

---

## 📄 License

This project was built for the **EY Techathon** hackathon.
