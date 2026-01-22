# Product Requirements Document (PRD)

## Project Title

Retail Deep Care – Multi‑Agent AI Chatbot

## Purpose & Vision

Build an intelligent, explainable, multi‑agent retail chatbot for a hackathon use case. The system assists logged‑in retail customers end‑to‑end: product discovery, inventory check, purchase (online/offline), fulfillment, loyalty rewards, and post‑purchase feedback. The chatbot exposes **live agent timelines** to improve transparency and trust.

The system uses **LangGraph** for agent orchestration, **FastAPI** for backend APIs, **CSV/SQLite** for data storage, **Google Gemini 2.5 Flash** as the LLM, and **React** for the frontend.

---

You are a Retail Deep Care AI Agent operating inside a multi-agent LangGraph system.

Rules:
- You NEVER fetch data directly.
- You NEVER modify databases or CSV files.
- You ONLY narrate results returned by backend tools.
- You MUST return structured JSON-compatible output.
- You MUST be concise, professional, and customer-friendly.
- You MUST describe what you are doing step-by-step for agent timeline visibility.
- You MUST assume all product, inventory, payment, and loyalty data is provided by tools.

Context:
- This is a retail shopping assistant.
- User is already logged in.
- Customer ID is available in state.
- Your output will be rendered by a UI, not plain text.

Always think: “Explain what I am doing, not how I do it.”


## Key Principles

* LLMs are used **only for reasoning, narration, and decision explanation**
* All business logic and data access is **deterministic** (Python tools)
* Each agent performs **one clearly defined responsibility**
* UI renders data based on **structured backend responses**, not raw LLM text
* Agent execution is **observable in real time** via a timeline panel

---

## Tech Stack

### Backend

* Language: Python 3.10+
* Framework: FastAPI
* AI Orchestration: LangGraph
* LLM: Google Gemini 2.5 Flash (`langchain-google-genai`)
* Storage:

  * CSV (products, customers, inventory)
  * SQLite (chat memory, agent timeline events)
* Realtime Communication: FastAPI WebSockets

### Frontend

* Framework: React
* Communication:

  * REST APIs (initial data)
  * WebSocket (agent timeline + chat streaming)
* UI Sections:

  * Chat Panel (main)
  * Agent Timeline Panel (left)
  * User Profile Panel (loyalty points)

---

## User Flow (High Level)

1. User logs in with `customer_id`
2. User opens chatbot
3. Recommendation Agent suggests products
4. Inventory Agent checks availability
5. Conditional flow:

   * Offline → Fulfillment (Kiosk Mode) → End
   * Online → Payment → Fulfillment → Loyalty → Post‑Purchase → End

---

## Data Sources (CSV)

### products.csv

* product_id
* name
* category
* price
* image_url

### customers.csv

* customer_id
* name
* loyalty_points

### inventory.csv

* product_id
* channel (online/offline)
* store_name (nullable)
* stock

---

## Backend Architecture

### Shared State (LangGraph)

```python
class ChatState(TypedDict):
    customer_id: str
    messages: list
    selected_product_id: str | None
    channel: str | None  # online | offline
```

---

## Agent Definitions & Responsibilities

### 1. Recommendation Agent

**Purpose:**
Introduce relevant products based on user intent.

**Inputs:**

* User message

**Tools Used:**

* CSV filter (category, price)

**LLM Role:**

* Narrate that products were found
* No confirmations, no decisions

**Outputs:**

* Chat message (breadcrumb style)
* Product list (IDs only)

**Timeline Events:**

* Analyzing user query
* Fetching products
* Product preview events
* Products ready

---

### 2. Inventory Agent

**Purpose:**
Check availability and expose online/offline choice.

**Inputs:**

* selected_product_id

**Tools Used:**

* inventory.csv lookup

**LLM Role:**

* Explain availability clearly

**Outputs:**

* Available channels: online / offline

**Timeline Events:**

* Checking online availability
* Checking nearby stores
* Availability confirmed

---

### 3. Payment Agent (Online Only)

**Purpose:**
Simulate payment workflow.

**Inputs:**

* channel = online

**Tools Used:**

* Mock payment processor

**LLM Role:**

* Guide payment selection
* Confirm success

**Outputs:**

* Payment status

**Timeline Events:**

* Waiting for user input
* Processing payment
* Payment successful

---

### 4. Fulfillment Agent

**Purpose:**
Handle delivery or kiosk mode.

**Modes:**

* Online: delivery scheduling
* Offline: kiosk/store pickup

**Tools Used:**

* Delivery ETA generator

**LLM Role:**

* Explain next steps

**Outputs:**

* Fulfillment message
* End conversation flag (offline)

**Timeline Events:**

* Scheduling delivery OR
* Switching to kiosk mode

---

### 5. Loyalty & Offers Agent (Online Only)

**Purpose:**
Reward the customer.

**Tools Used:**

* Random reward generator
* CSV loyalty updater

**LLM Role:**

* Celebrate rewards
* Explain benefits

**Outputs:**

* Points awarded
* Coupon code

**Timeline Events:**

* Applying loyalty rewards
* Loyalty updated

---

### 6. Post‑Purchase Agent

**Purpose:**
Close the journey and request feedback.

**LLM Role:**

* Thank user
* Request feedback

**Outputs:**

* feedback_required = true
* end_conversation = true

**Timeline Events:**

* Requesting feedback
* Conversation closed

---

## Agent Workflow (LangGraph)

```
START
 ↓
Recommendation Agent
 ↓
Inventory Agent
 ↓
[ channel == offline ] ──> Fulfillment Agent (Kiosk) → END
 ↓
Payment Agent
 ↓
Fulfillment Agent
 ↓
Loyalty & Offers Agent
 ↓
Post‑Purchase Agent
 ↓
END
```

---

## Realtime Agent Timeline System

### Event Schema

```json
{
  "agent": "recommendation_agent",
  "status": "fetching",
  "message": "Fetching products",
  "type": "product_preview",
  "product": { "product_id": "PRD101", "name": "Shirt", "price": 1999 }
}
```

### Transport

* FastAPI WebSocket `/ws/agents`
* Events pushed from agents to UI

---

## Frontend Responsibilities

### Chat Panel

* Render agent messages
* Render product cards using product_id
* Render payment / feedback UI

### Agent Timeline Panel

* Show live agent steps
* Show inline product previews
* Reflect agent status changes

### User Profile Panel

* Display loyalty points
* Update after loyalty agent runs

---

## Non‑Functional Requirements

* Hackathon‑ready (no external DB required)
* Deterministic behavior
* Explainable agent actions
* Easy to migrate from CSV → DB

---

## Out of Scope (Intentional)

* Real payments
* Authentication system
* Large‑scale concurrency
* Multi‑language support

---

## Success Criteria (Judging)

* Clear multi‑agent orchestration
* Visible agent reasoning
* Clean UI + backend separation
* Correct use of LLMs
* End‑to‑end retail flow demo

---

## Summary

This PRD defines a complete, realistic, and hackathon‑appropriate multi‑agent retail chatbot system. The design emphasizes explainability, correctness, and system architecture over raw AI generation, making it suitable for judging, mentoring, and real‑world extension.
