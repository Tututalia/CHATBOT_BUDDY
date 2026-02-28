"""
Generate a Word document (.docx) containing detailed technical Q&A
about the data flow in the EY Techathon Retail Agent project.

Usage:
    cd backend
    python utility/generate_technical_qa_doc.py

Output:
    technical_qa_dataflow.docx  (saved in backend/)
"""

import os
import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

# ──────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────


def set_cell_shading(cell, color_hex: str):
    """Apply background shading to a table cell."""
    shading = cell._element.get_or_add_tcPr()
    shd = shading.makeelement(qn('w:shd'), {
        qn('w:fill'): color_hex,
        qn('w:color'): 'auto',
        qn('w:val'): 'clear',
    })
    shading.append(shd)


def add_code_block(doc: Document, code: str, language: str = "python"):
    """Add a formatted code block paragraph to the document."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)

    # Use a shaded box effect via paragraph shading
    pPr = p._element.get_or_add_pPr()
    shd = pPr.makeelement(qn('w:shd'), {
        qn('w:fill'): 'F5F5F5',
        qn('w:color'): 'auto',
        qn('w:val'): 'clear',
    })
    pPr.append(shd)

    run = p.add_run(code)
    run.font.name = 'Consolas'
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x1E, 0x1E, 0x1E)


def add_bullet(doc: Document, text: str, bold_prefix: str = None, level: int = 0):
    """Add a bullet point. Optionally bold the first part."""
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(1.5 + level * 0.7)
    if bold_prefix:
        run_b = p.add_run(bold_prefix)
        run_b.bold = True
        p.add_run(text)
    else:
        p.add_run(text)


def add_numbered(doc: Document, text: str, bold_prefix: str = None):
    """Add a numbered list item."""
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.left_indent = Cm(1.5)
    if bold_prefix:
        run_b = p.add_run(bold_prefix)
        run_b.bold = True
        p.add_run(text)
    else:
        p.add_run(text)


def heading(doc: Document, text: str, level: int = 2):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)


# ──────────────────────────────────────────────────────────────────
# Build the document
# ──────────────────────────────────────────────────────────────────

def build_document() -> Document:
    doc = Document()

    # ── Title page ────────────────────────────────────────────────
    title = doc.add_heading(
        'Technical Q&A — Data Flow & Agentic Architecture', level=0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(0x0D, 0x27, 0x50)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = subtitle.add_run('EY Techathon — Intelligent Retail Sales Agent')
    run_sub.font.size = Pt(14)
    run_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph()  # spacer
    doc.add_paragraph(
        'This document provides detailed, code-backed answers to the key technical '
        'question: "How does data flow from the frontend chatbot to the backend '
        'agentic system and back?" — covering the master/worker agent orchestration, '
        'dynamic database queries via the CRUD layer, and structured response rendering.'
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 1 — Frontend → Backend
    # ══════════════════════════════════════════════════════════════
    heading(doc, '1. Frontend → Backend: How the User Query Is Sent', level=1)

    heading(doc, '1.1 REST API Path (chatApi.js → /api/chat)', level=2)
    doc.add_paragraph(
        'The React chatbot component (frontend/src/components/ChatBot.jsx) collects the '
        'user\'s message and full conversation history. It uses the chatApi service to '
        'send the data to the FastAPI backend:'
    )

    add_code_block(doc, '''\
// frontend/src/services/chatApi.js

import axios from "axios";

export const chatWithAgent = async (
  customerId,
  message,
  conversationHistory = [],
) => {
  const response = await axios.post("http://localhost:8000/api/chat", {
    customer_id: customerId,
    message,
    conversation_history: conversationHistory,
  });
  return response.data;
};''', 'javascript')

    doc.add_paragraph(
        'This sends a POST request to the FastAPI endpoint /api/chat with three fields: '
        'customer_id, message, and conversation_history (an array of previous turns for continuity).'
    )

    heading(doc, '1.2 WebSocket Path (ChatBot.jsx → /ws/chat)', level=2)
    doc.add_paragraph(
        'For real-time streaming and the live "Agent Timeline" UI, the chatbot also '
        'opens a WebSocket connection to ws://localhost:8000/ws/chat. Each user message '
        'is wrapped as a JSON payload:'
    )
    add_code_block(doc, '''\
// WebSocket message format (sent from ChatBot.jsx)
{
  "request_id": "<uuid>",
  "customer_id": "CUST001",
  "message": "Show me hoodies"
}''', 'json')

    doc.add_paragraph(
        'The WebSocket handler streams back incremental timeline events '
        '(timeline_start, timeline_log, timeline_end) and a final_response, enabling '
        'the frontend to render the agent orchestration timeline in real time.'
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 2 — Backend entrypoint
    # ══════════════════════════════════════════════════════════════
    heading(
        doc, '2. Backend Entrypoint: Saving History & Routing to the Agent Graph', level=1)

    heading(doc, '2.1 Request Model', level=2)
    doc.add_paragraph(
        'The incoming JSON is validated against a Pydantic model defined in backend/main.py:'
    )
    add_code_block(doc, '''\
# backend/main.py

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    customer_id: str
    message: str
    conversation_history: List[Dict[str, str]] = []''')

    heading(doc, '2.2 Handler Flow (POST /api/chat)', level=2)
    doc.add_paragraph(
        'The chat_with_agent handler in backend/main.py performs the following steps:'
    )

    add_numbered(doc, 'Persists the user turn into the chat history database via '
                      'save_message(customer_id, session_id, "user", user_query) '
                      '— implemented in backend/chat_database.py.',
                 bold_prefix='Persist user turn: ')

    add_numbered(doc, 'Loads recent conversation history for context using '
                      'get_conversation_history(customer_id, session_id, limit=1).',
                 bold_prefix='Load history: ')

    add_numbered(doc, 'Checks if the query is a structured "price band" query '
                      '(e.g., "hoodies between 1500 and 2000"). If so, it directly '
                      'calls inventory_agent and recommendation_agent tools without '
                      'invoking the LLM — a fast path optimisation.',
                 bold_prefix='Price-band fast path: ')

    add_numbered(doc, 'For all other queries, creates the LangGraph agent graph via '
                      'create_agent_graph(), converts DB history rows into LangChain '
                      'messages (HumanMessage / AIMessage), builds the initial state, '
                      'and invokes the graph with await graph.ainvoke(initial_state).',
                 bold_prefix='LangGraph invocation: ')

    add_numbered(doc, 'Extracts the last ToolMessage from the final state, parses it '
                      'as JSON, attaches the timeline, saves the assistant turn, and '
                      'returns the structured response.',
                 bold_prefix='Response extraction: ')

    heading(doc, '2.3 Initial State Construction', level=2)
    doc.add_paragraph(
        'The initial state passed into the LangGraph contains the full context '
        'needed by any worker agent:'
    )
    add_code_block(doc, '''\
# backend/main.py  (inside chat_with_agent)

initial_state = {
    "messages": messages,          # LangChain HumanMessage/AIMessage list
    "customer_id": customer_id,
    "selected_product": None,
    "inventory_status": None,
    "purchase_channel": None,      # "online" or "offline"
    "order_id": None,
    "payment_completed": False,
    "loyalty_points": 0,
    "cart_items": [],
}''')

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 3 — Master agent orchestration
    # ══════════════════════════════════════════════════════════════
    heading(doc, '3. Master Agent Orchestration with LangGraph', level=1)

    heading(doc, '3.1 AgentState (Shared Graph State)', level=2)
    doc.add_paragraph(
        'The graph state is defined as a TypedDict in backend/intelligent_agent_graph.py. '
        'It is shared across all nodes and carries conversation messages, customer context, '
        'cart data, payment status, etc.:'
    )
    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py

class AgentState(TypedDict):
    """State for the agent workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    customer_id: str
    selected_product: Dict[str, Any] | None
    inventory_status: str | None
    purchase_channel: str | None       # "online" or "offline"
    order_id: str | None
    payment_completed: bool
    loyalty_points: int
    cart_items: List[Dict[str, Any]]   # products in cart''')

    heading(doc, '3.2 Worker Agents as LangChain @tool Functions', level=2)
    doc.add_paragraph(
        'Each worker agent is declared as a LangChain @tool function in '
        'backend/intelligent_agent_graph.py. The master LLM can call any of them '
        'by emitting structured tool_calls. The full list:'
    )

    # Tools table
    tools_data = [
        ('customer_info_agent', 'customer_id, info_type',
         'Fetches customer profile, order history, loyalty points from the customers table.'),
        ('inventory_agent', 'search_query, product_id, customer_id, sort_by_rating',
         'Searches products by category/keyword/price, or lists stores for a product. '
         'Builds dynamic queries against the products table.'),
        ('recommendation_agent', 'inventory_data',
         'Takes the raw JSON output of inventory_agent and formats it into '
         'product cards with discount prices, images, and metadata.'),
        ('upsell_agent', 'customer_id',
         'Recommends complementary accessories (belts, shoes, watches) based on '
         'current cart contents.'),
        ('add_to_cart_agent', 'product_id, quantity, customer_id, size',
         'Validates stock via get_product_by_id, then inserts a row into the cart '
         'table using cart_crud.create.'),
        ('view_cart_agent', 'customer_id',
         'Queries pending cart items via cart_crud.filter with '
         'filters={"customer_id": ..., "status": "pending"}. Returns items '
         'with per-item price, discount, and total.'),
        ('remove_from_cart_agent', 'order_id, customer_id',
         'Deletes a specific cart row by order_id using cart_crud.delete.'),
        ('choose_channel_agent', 'customer_id',
         'Presents ONLINE (home delivery with loyalty) vs OFFLINE (store pickup) options.'),
        ('payment_agent', 'customer_id, payment_method',
         'Called twice: (1) without payment_method → shows UPI/Credit/Debit/NetBanking options. '
         '(2) with payment_method → processes payment, deducts inventory, creates order_history rows, '
         'marks cart as completed, updates loyalty points.'),
        ('fulfillment_agent', 'purchase_type, store_name, customer_id, order_id',
         'Handles online delivery confirmation or offline store-pickup confirmation. '
         'Reads from stores and order_history tables.'),
        ('loyalty_agent', 'order_id, customer_id',
         'Awards loyalty points and tier-based coupons after purchase. '
         'Updates the customers table.'),
        ('post_purchase_agent', 'order_id, customer_id',
         'Sends feedback link and support information. Final step of the workflow.'),
    ]

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Tool / Worker Agent'
    hdr[1].text = 'Key Parameters'
    hdr[2].text = 'What It Does'
    for cell in hdr:
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)

    for name, params, desc in tools_data:
        row = table.add_row().cells
        row[0].text = name
        row[1].text = params
        row[2].text = desc
        for cell in row:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.5)

    doc.add_paragraph()

    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py

tools = [
    customer_info_agent,
    inventory_agent,
    recommendation_agent,
    upsell_agent,
    add_to_cart_agent,
    view_cart_agent,
    remove_from_cart_agent,
    choose_channel_agent,
    payment_agent,
    fulfillment_agent,
    loyalty_agent,
    post_purchase_agent,
]''')

    heading(doc, '3.3 The agent_node — LLM as the Master Orchestrator', level=2)
    doc.add_paragraph(
        'The agent_node function is the "brain" of the system. It binds all 12 tools '
        'to the LLM (GPT-4o-mini) and supplies a comprehensive system prompt that '
        'encodes the exact sales workflow:'
    )
    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py

def agent_node(state: AgentState):
    llm = create_llm()                      # GPT-4o-mini, temperature=0.1
    llm_with_tools = llm.bind_tools(tools)  # Bind all 12 worker agent tools

    system_message = SystemMessage(content=f"""
        You are a helpful AI shopping assistant...
        
        CRITICAL WORKFLOW:
        STEP 1: inventory_agent(search_query=...) → recommendation_agent(inventory_data=...)
        STEP 2: add_to_cart_agent(product_id=..., quantity=..., customer_id=...)
        STEP 3: view_cart_agent(customer_id=...)
        STEP 4: choose_channel_agent(customer_id=...)
        STEP 5A (offline): inventory_agent(product_id=...) → fulfillment_agent(offline)
        STEP 5B (online): payment_agent (twice) → fulfillment → loyalty → post_purchase
        ...
        customer_id = {customer_id}
    """)

    messages = [system_message] + state["messages"]
    response = llm_with_tools.invoke(messages)   # LLM emits tool_calls
    return {"messages": [response]}''')

    doc.add_paragraph(
        'The LLM\'s response is an AIMessage that contains a tool_calls list — each '
        'entry specifying a tool name and arguments. For example, if the user says '
        '"show me hoodies", the LLM emits:'
    )
    add_code_block(doc, '''\
# Example AIMessage.tool_calls (decided by LLM)
[
  {"name": "inventory_agent",
   "args": {"search_query": "hoodies", "customer_id": "CUST001"}},
]''', 'json')

    heading(doc, '3.4 The tool_node — Executing Worker Agents', level=2)
    doc.add_paragraph(
        'The tool_node function receives the LLM\'s tool_calls and executes each '
        'one against the actual database:'
    )
    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py

def tool_node(state: AgentState):
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = _execute_tool(tool_call)
        outputs.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"]
            )
        )
    return {"messages": outputs}

def _execute_tool(tool_call: dict) -> str:
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    for tool in tools:
        if tool.name == tool_name:
            return tool.invoke(tool_args)   # Calls the @tool function
    return f"Error: Tool {tool_name} not found"''')

    heading(doc, '3.5 Routing: should_continue', level=2)
    doc.add_paragraph(
        'After the agent_node runs, a conditional edge checks whether the LLM wants '
        'to call tools or end the conversation:'
    )
    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]

    # If LLM made tool calls, route to the tool executor
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise end the conversation turn
    return "__end__"''')

    heading(doc, '3.6 Graph Wiring: create_agent_graph', level=2)
    doc.add_paragraph(
        'The full LangGraph state machine is wired as a cycle:'
    )
    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py

def create_agent_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)   # LLM decides tools
    workflow.add_node("tools", tool_node)    # Executes tools

    # Edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "__end__": END},
    )
    workflow.add_edge("tools", "agent")      # Loop back after tool execution

    return workflow.compile()''')

    doc.add_paragraph(
        'The execution loop is: START → agent_node (LLM) → should_continue → '
        'tools (if tool_calls) → agent_node → … → END (when no more tool_calls).'
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 4 — Worker agents & database
    # ══════════════════════════════════════════════════════════════
    heading(
        doc, '4. Worker Agents → Database: Dynamic Queries via CRUD + SQLModel', level=1)

    heading(doc, '4.1 SQLModel Data Models (backend/models.py)', level=2)
    doc.add_paragraph(
        'All database tables are defined as SQLModel classes. Key models:'
    )
    add_code_block(doc, '''\
# backend/models.py

class Product(SQLModel, table=True):
    __tablename__ = "products"
    product_id: str = Field(primary_key=True, index=True)
    product_name: str = Field(index=True)
    category: str = Field(index=True)
    gender: str
    price: float
    quantity: int = Field(default=0)
    online_available: str       # Yes/No
    offline_available: str      # Yes/No
    offline_stores: Optional[str] = None
    store_ids: Optional[str] = None
    season: str
    image_reference: str
    loyalty_points: int = Field(default=0)
    discount: int = Field(default=0)

class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    customer_id: str = Field(primary_key=True, index=True)
    customer_name: str
    gender: str
    phone: str
    address: str
    loyalty_points: int = Field(default=0)
    customer_type: Optional[str] = None   # tier_1, tier_2, tier_3

class Cart(SQLModel, table=True):
    __tablename__ = "cart"
    order_id: str = Field(primary_key=True)
    customer_id: Optional[str] = Field(foreign_key="customers.customer_id")
    product_id: Optional[str] = Field(foreign_key="products.product_id")
    store_id: Optional[str] = Field(foreign_key="stores.store_id")
    channel: Optional[str] = Field(default="online")
    status: Optional[str] = Field(default="pending")
    quantity: int = Field(default=1)
    size: Optional[str] = Field(default=None)

class OrderHistory(SQLModel, table=True):
    __tablename__ = "order_history"
    transaction_id: str = Field(primary_key=True)
    customer_id: str = Field(foreign_key="customers.customer_id")
    product_id: str = Field(foreign_key="products.product_id")
    quantity: int
    loyalty_points: int
    loyalty_applied: Optional[float] = None
    discount_amount: Optional[float] = None
    final_price: Optional[float] = None''')

    heading(
        doc, '4.2 UniversalCRUD — The Generic Query Layer (backend/crud.py)', level=2)
    doc.add_paragraph(
        'All database operations go through a single generic CRUD class that supports '
        'dynamic filtering, ordering, pagination, and all standard operators:'
    )
    add_code_block(doc, '''\
# backend/crud.py

class UniversalCRUD:
    def __init__(self, model: Type[SQLModel], primary_key: str = "id"):
        self.model = model
        self.primary_key = primary_key

    def create(self, session, data) -> SQLModel: ...
    def get_by_id(self, session, record_id) -> Optional[SQLModel]: ...
    def get_all(self, session, skip=0, limit=100) -> List[SQLModel]: ...

    def filter(self, session, filters=None, operators=None,
               order_by=None, order_desc=False,
               skip=0, limit=100) -> List[SQLModel]:
        statement = select(self.model)
        if filters:
            for field, value in filters.items():
                column = getattr(self.model, field)
                operator = operators.get(field, \'==\') if operators else \'==\'
                if operator == \'==\':
                    statement = statement.where(column == value)
                elif operator == \'contains\':
                    statement = statement.where(column.contains(value))
                elif operator == \'>=\':
                    statement = statement.where(column >= value)
                elif operator == \'<=\':
                    statement = statement.where(column <= value)
                # ... more operators ...
        if order_by:
            ...
        statement = statement.offset(skip).limit(limit)
        return session.exec(statement).all()

    def update(self, session, record_id, data) -> Optional[SQLModel]: ...
    def delete(self, session, record_id) -> bool: ...''')

    heading(doc, '4.3 Pre-configured CRUD Instances', level=2)
    doc.add_paragraph(
        'Each table has a pre-instantiated CRUD object ready for use:'
    )
    add_code_block(doc, '''\
# backend/crud.py

customer_crud      = UniversalCRUD(Customer,      primary_key="customer_id")
product_crud       = UniversalCRUD(Product,        primary_key="product_id")
store_crud         = UniversalCRUD(Store,          primary_key="store_id")
order_history_crud = UniversalCRUD(OrderHistory,   primary_key="transaction_id")
cart_crud          = UniversalCRUD(Cart,           primary_key="order_id")''')

    heading(doc, '4.4 How Worker Agents Build Dynamic Queries', level=2)

    doc.add_paragraph(
        'Each @tool function opens a database session using get_db_session() '
        '(from backend/database.py) and calls the appropriate CRUD instance '
        'with dynamically constructed filters. Examples:'
    )

    # Example 1 — inventory search
    doc.add_paragraph().add_run('Example 1: inventory_agent — Product Search').bold = True
    add_code_block(doc, '''\
# backend/intelligent_agent_graph.py  (inside inventory_agent)

def load_products_from_db(category=None, gender=None,
                          season=None, max_price=None,
                          search_query=None) -> List[Product]:
    with get_db_session() as session:
        # Uses product_crud.filter() with dynamic filters built from
        # the user\'s natural-language query, parsed by:
        #   _parse_price_band_from_query(query)  → min_price, max_price
        #   _get_customer_gender(customer_id)    → gender filter
        #   _extract_explicit_gender_from_query() → explicit gender override
        products = product_crud.filter(session, filters={...}, operators={...})
        return products''')

    doc.add_paragraph(
        'The inventory_agent then applies tier-based personalization (Customer.customer_type), '
        'rating-based sorting (from the Feedback table), limits results to 4 products, '
        'and tracks previously shown products in _SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY '
        'to handle "show me more" without repeats.'
    )

    # Example 2 — cart operations
    doc.add_paragraph().add_run('Example 2: view_cart_agent — Cart Query').bold = True
    add_code_block(doc, '''\
# Inside view_cart_agent @tool function

with get_db_session() as session:
    cart_items = cart_crud.filter(
        session,
        filters={"customer_id": customer_id, "status": "pending"}
    )
    # For each cart item, fetch product details:
    for item in cart_items:
        product = product_crud.get_by_id(session, item.product_id)
        # Calculate: discount price, loyalty points, total
        ...''')

    # Example 3 — payment processing
    doc.add_paragraph().add_run('Example 3: payment_agent — Order Creation').bold = True
    add_code_block(doc, '''\
# Inside payment_agent @tool function (second call — processes payment)

with get_db_session() as session:
    pending_items = cart_crud.filter(
        session,
        filters={"customer_id": customer_id, "status": "pending"}
    )
    for item in pending_items:
        product = product_crud.get_by_id(session, item.product_id)
        # 1. Deduct inventory
        deduct_product_quantity(product.product_id, item.quantity)
        # 2. Create order history row
        order_history_crud.create(session, {
            "transaction_id": new_txn_id,
            "customer_id": customer_id,
            "product_id": product.product_id,
            "quantity": item.quantity,
            "final_price": calculated_price,
            "loyalty_points": earned_points,
            ...
        })
        # 3. Mark cart item as completed
        cart_crud.update(session, item.order_id, {"status": "completed"})
    # 4. Update customer loyalty points
    customer_crud.update(session, customer_id,
                         {"loyalty_points": new_balance})''')

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 5 — Backend → Frontend
    # ══════════════════════════════════════════════════════════════
    heading(doc, '5. Backend → Frontend: Structured Response & Rendering', level=1)

    heading(doc, '5.1 Response Structure from Backend', level=2)
    doc.add_paragraph(
        'The backend returns structured JSON (not plain text) so the frontend can '
        'render rich UI components. Key response shapes:'
    )

    resp_data = [
        ('recommendation_agent',
         'responses.default (text)\nresponses.recommendation (product card array)\nagent_calls (["inventory_agent", "recommendation_agent"])'),
        ('view_cart_agent', 'cart_items (array with product_name, quantity, price, discount, final_price)\ntotal_amount, total_savings'),
        ('choose_channel_agent',
         'response (markdown with channel metadata)\nagent_calls (["choose_channel_agent"])'),
        ('payment_agent (1st call)',
         'response (text with 4 payment options)\nagent_calls (["payment_agent"])'),
        ('payment_agent (2nd call)',
         'response ("Payment Successful!")\nstructured_data (order_id, totals)'),
        ('fulfillment_agent', 'response (delivery/pickup confirmation)\nstructured_data (delivery window, store details)'),
    ]

    table2 = doc.add_table(rows=1, cols=2)
    table2.style = 'Light Grid Accent 1'
    hdr2 = table2.rows[0].cells
    hdr2[0].text = 'Agent / Tool'
    hdr2[1].text = 'Response JSON Fields'
    for cell in hdr2:
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
    for agent_name, fields in resp_data:
        row = table2.add_row().cells
        row[0].text = agent_name
        row[1].text = fields
        for cell in row:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.5)

    doc.add_paragraph()

    heading(doc, '5.2 Timeline Generation', level=2)
    doc.add_paragraph(
        'Both the REST and WebSocket paths generate a timeline array for the '
        '"Agent Timeline" sidebar in the chatbot UI:'
    )
    add_code_block(doc, '''\
# backend/main.py

def _format_timeline_messages_from_langchain_messages(messages):
    timeline_messages = []
    seen_agents = set()
    tool_to_agent_map = _tool_to_agent_map()

    for message in messages:
        if isinstance(message, AIMessage):
            for tool_call in (message.tool_calls or []):
                tool_name = tool_call.get("name", "")
                agent_name = tool_to_agent_map.get(tool_name, tool_name)
                if agent_name not in seen_agents:
                    seen_agents.add(agent_name)
                    timeline_messages.append({
                        "agent": agent_name,
                        "timestamp": "now",
                    })
    return timeline_messages

# Maps tool function names to display-friendly labels
def _tool_to_agent_map():
    return {
        "customer_info_agent": "Customer Info Agent",
        "inventory_agent":     "Inventory Agent",
        "recommendation_agent":"Recommendation Agent",
        "payment_agent":       "Payment Agent",
        "fulfillment_agent":   "Fulfillment Agent",
        ...
    }''')

    heading(doc, '5.3 Frontend Rendering Logic (ChatBot.jsx)', level=2)
    doc.add_paragraph(
        'The React chatbot inspects the JSON payload and pushes typed messages '
        'into its state for rendering as distinct UI components:'
    )

    doc.add_paragraph().add_run('Product Recommendations:').bold = True
    add_code_block(doc, '''\
// frontend/src/components/ChatBot.jsx

if (response.responses?.recommendation
    && Array.isArray(response.responses.recommendation)) {
  setLastRecommendations(response.responses.recommendation);
  initialMessages.push({
    type: "productCards",
    text: response.responses.default,
    products: response.responses.recommendation,
    timestamp: new Date(),
  });
}''', 'javascript')

    doc.add_paragraph().add_run('Cart Summary:').bold = True
    add_code_block(doc, '''\
// frontend/src/components/ChatBot.jsx

if (response.cart_items && Array.isArray(response.cart_items)
    && response.cart_items.length > 0) {
  initialMessages.push({
    type: "cartSummary",
    cartItems: response.cart_items,
    total_amount: response.total_amount,
    total_savings: response.total_savings,
    available_loyalty_points: response.available_loyalty_points || 0,
    timestamp: new Date(),
  });
}''', 'javascript')

    doc.add_paragraph().add_run('Channel Selection & Payment:').bold = True
    add_code_block(doc, '''\
// frontend/src/components/ChatBot.jsx

if (response.agent_calls?.includes("choose_channel_agent")) {
  initialMessages.push({
    type: "purchaseMethods",
    text: response.response,
    timestamp: new Date(),
  });
} else if (response.agent_calls?.includes("payment_agent")
           && response.agent_calls.length === 1) {
  initialMessages.push({
    type: "paymentMethods",
    text: response.response,
    timestamp: new Date(),
  });
}''', 'javascript')

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 6 — End-to-end flow diagram (text)
    # ══════════════════════════════════════════════════════════════
    heading(doc, '6. End-to-End Flow Summary', level=1)

    doc.add_paragraph(
        'The complete data-flow can be summarised in the following steps:'
    )

    steps = [
        ('User → Frontend',
         'User types a message in the React chatbot (ChatBot.jsx). '
         'The component sends it (with recent history) to the FastAPI backend '
         '/api/chat via Axios POST, or via WebSocket /ws/chat for streaming.'),
        ('Frontend → Backend',
         'The chat_with_agent handler persists the turn into chat history, reloads '
         'the last messages, and either: (a) runs a fast path for structured price-band '
         'queries using only inventory_agent + recommendation_agent, or (b) hands the '
         'conversation to the LangGraph orchestration via create_agent_graph().'),
        ('Master Agent Decides Tools',
         'In agent_node, GPT-4o-mini is bound with all 12 worker tools. A large system '
         'prompt encodes the exact sales workflow. The LLM emits structured tool_calls '
         'with specific tool names and arguments.'),
        ('Worker Agents Hit the Database',
         'tool_node executes those calls. Each @tool function uses SQLModel models '
         '(models.py) and the generic UniversalCRUD layer (crud.py) plus get_db_session() '
         'to run dynamic queries against SQLite. They return JSON capturing products, '
         'cart, orders, stores, etc.'),
        ('Loop Until Done',
         'Tool outputs are fed back to the LLM as ToolMessages, which either calls more '
         'tools or stops, following strict rules (e.g., payment agent exactly twice). '
         'This continues until should_continue returns "__end__".'),
        ('Backend → Frontend',
         'The final tool response is converted into a unified JSON object '
         '(responses.recommendation, cart_items, agent_calls, timeline, etc.) and sent '
         'back to the frontend. The React chatbot renders product cards, cart views, '
         'payment channel UIs, and a live "Agent Timeline" showing the orchestration.'),
    ]

    for i, (title, desc) in enumerate(steps, 1):
        p = doc.add_paragraph()
        run_num = p.add_run(f'Step {i}: {title}')
        run_num.bold = True
        run_num.font.size = Pt(11)
        run_num.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)

        p2 = doc.add_paragraph(desc)
        p2.paragraph_format.left_indent = Cm(1)
        p2.paragraph_format.space_after = Pt(8)

    doc.add_paragraph()

    # ── ASCII flow diagram ────────────────────────────────────────
    heading(doc, '6.1 Visual Data-Flow Diagram', level=2)
    add_code_block(doc, '''\
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ChatBot.jsx  ──POST /api/chat──►  or  ──WS /ws/chat──►        │
│       ▲                                                         │
│       │  JSON: { responses.recommendation, cart_items,          │
│       │          agent_calls, timeline }                        │
│       │  renders: productCards | cartSummary | paymentMethods   │
└───────┼─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                                                                 │
│  main.py: chat_with_agent()                                     │
│    1. save_message() → chat_database                            │
│    2. get_conversation_history()                                │
│    3. Price-band fast path? → direct tool calls                 │
│    4. Otherwise → create_agent_graph().ainvoke(initial_state)   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           LangGraph State Machine                        │   │
│  │                                                          │   │
│  │  START ─► agent_node (GPT-4o-mini + 12 tools bound)     │   │
│  │               │                                          │   │
│  │         should_continue?                                 │   │
│  │          ╱           ╲                                   │   │
│  │     tool_calls     no calls                              │   │
│  │         │              │                                 │   │
│  │    tool_node        __end__                              │   │
│  │     (execute)                                            │   │
│  │         │                                                │   │
│  │    ┌────┴────┐                                           │   │
│  │    │ @tool   │ inventory_agent, recommendation_agent,    │   │
│  │    │ funcs   │ add_to_cart_agent, view_cart_agent,       │   │
│  │    │         │ payment_agent, fulfillment_agent,         │   │
│  │    │         │ loyalty_agent, post_purchase_agent ...    │   │
│  │    └────┬────┘                                           │   │
│  │         │   ToolMessage(JSON)                            │   │
│  │         ▼                                                │   │
│  │    agent_node ◄── loop back                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           DATABASE (SQLite via SQLModel + CRUD)          │   │
│  │                                                          │   │
│  │  models.py:  Product, Customer, Cart, OrderHistory,      │   │
│  │              Store, Feedback, Wishlist, ...               │   │
│  │                                                          │   │
│  │  crud.py:    UniversalCRUD.filter(session, filters={..}) │   │
│  │              .create()  .get_by_id()  .update()          │   │
│  │              .delete()  .count()                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘''')

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTION 7 — Key talking points for jury
    # ══════════════════════════════════════════════════════════════
    heading(doc, '7. Key Talking Points for the Jury Panel', level=1)

    talking_points = [
        ('No hard-coded responses',
         'Every single response (product search, cart, payment, fulfilment) is dynamically '
         'generated by worker agents querying the actual database in real time.'),
        ('LLM as orchestrator, not executor',
         'The LLM (GPT-4o-mini) never generates product data or prices. It only decides '
         'WHICH tools to call and with WHAT arguments. All data comes from the DB.'),
        ('Generic CRUD layer',
         'The UniversalCRUD class can work with ANY SQLModel table. Adding a new table '
         'only requires defining the model and instantiating UniversalCRUD — no new '
         'query code.'),
        ('Structured JSON, not free text',
         'Worker agents return structured JSON (product arrays, cart objects, order data) '
         'so the frontend can render rich UI components — product cards, cart summaries, '
         'payment UIs, timelines.'),
        ('Strict workflow enforcement',
         'The system prompt encodes a complete workflow (search → cart → channel → '
         'payment → fulfilment → loyalty → post-purchase) with exact rules like '
         '"payment_agent called exactly twice". This prevents the LLM from skipping steps.'),
        ('Real-time timeline',
         'The WebSocket path streams tool invocation events so the UI shows a live '
         '"Agent Timeline" — the jury can see which worker agents are being called '
         'and in what order.'),
        ('Multi-channel support',
         'The same agentic architecture powers web chatbot, WhatsApp (via Twilio), '
         'and in-store kiosk — each using the same @tool functions and CRUD layer.'),
        ('Idempotent & safe',
         'Cart operations use status flags (pending/completed), product deduction is '
         'atomic, and loyalty points are tracked per-session to prevent double-spending.'),
    ]

    for title, desc in talking_points:
        p = doc.add_paragraph()
        run_t = p.add_run(f'✓  {title}: ')
        run_t.bold = True
        run_t.font.color.rgb = RGBColor(0x0D, 0x6E, 0x3A)
        p.add_run(desc)

    # ── Footer ────────────────────────────────────────────────────
    doc.add_paragraph()
    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_f = footer.add_run('— End of Technical Q&A Document —')
    run_f.italic = True
    run_f.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    return doc


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    output_path = Path(__file__).resolve().parent.parent / \
        "technical_qa_dataflow.docx"
    doc = build_document()
    doc.save(str(output_path))
    print(f"✅  Document saved to: {output_path}")
    print(f"    File size: {output_path.stat().st_size / 1024:.1f} KB")
