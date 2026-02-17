from fpdf import FPDF
import textwrap

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'EY Techathon Retail Agent - Complete Documentation', 0, 1, 'C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.ln(6)
        self.cell(0, 10, title, 0, 1, 'L')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(0, 80, 130)
        self.ln(4)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

    def sub_section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.ln(3)
        self.cell(0, 7, title, 0, 1, 'L')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def code_block(self, code):
        self.set_font('Courier', '', 8.5)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        lines = code.split('\n')
        for line in lines:
            # Wrap long lines
            wrapped = textwrap.wrap(line, width=95) or ['']
            for wl in wrapped:
                self.cell(0, 4.8, '  ' + wl, 0, 1, 'L', fill=True)
        self.ln(3)

    def bullet_point(self, text, indent=10):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(4, 5.5, chr(149), 0, 0)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def table_header(self, cols, widths):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, 1, 0, 'C', fill=True)
        self.ln()

    def table_row(self, cols, widths):
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(248, 248, 248)
        max_lines = 1
        cell_texts = []
        for i, col in enumerate(cols):
            wrapped = textwrap.wrap(str(col), width=int(widths[i] / 2.2)) or ['']
            cell_texts.append(wrapped)
            max_lines = max(max_lines, len(wrapped))

        row_height = 5.5 * max_lines
        y_start = self.get_y()
        x_start = self.get_x()

        for i, texts in enumerate(cell_texts):
            self.set_xy(x_start + sum(widths[:i]), y_start)
            for j, t in enumerate(texts):
                self.set_xy(x_start + sum(widths[:i]), y_start + j * 5.5)
                self.cell(widths[i], 5.5, t, 0, 0, 'L')

        self.set_xy(x_start, y_start)
        for w in widths:
            self.cell(w, row_height, '', 1, 0)
        self.ln()


def create_pdf():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ======================== COVER PAGE ========================
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, 'EY Techathon Retail Agent', 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, 'Complete Technical Documentation', 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Helvetica', 'I', 12)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 10, 'Multi-Agent AI Retail Assistant', 0, 1, 'C')
    pdf.cell(0, 10, 'Semi-Finals Presentation Guide', 0, 1, 'C')
    pdf.ln(30)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, 'Tech Stack: Python FastAPI | LangGraph | OpenAI GPT-4o-mini | SQLite | React', 0, 1, 'C')
    pdf.cell(0, 8, 'February 2026', 0, 1, 'C')

    # ======================== TABLE OF CONTENTS ========================
    pdf.add_page()
    pdf.chapter_title('Table of Contents')
    toc_items = [
        '1. Architecture Overview',
        '2. Database Layer',
        '3. Models (Data Schema)',
        '4. CRUD Operations (Universal Pattern)',
        '5. Agent Tools (All 12 Tools - Detailed)',
        '6. Agent Graph & Orchestration (LangGraph)',
        '7. All API Endpoints (Detailed)',
        '8. WebSocket Real-time Communication',
        '9. Chat Database & History',
        '10. Store Kiosk Flow',
        '11. WhatsApp Integration',
        '12. Security',
        '13. Data Import Pipeline',
        '14. Migration Scripts',
        '15. Configuration',
        '16. Key Design Patterns Summary',
    ]
    for item in toc_items:
        pdf.bullet_point(item, indent=15)

    # ======================== 1. ARCHITECTURE OVERVIEW ========================
    pdf.add_page()
    pdf.chapter_title('1. Architecture Overview')

    pdf.body_text(
        'This is a multi-agent AI retail assistant built for an omnichannel shopping experience. '
        'The system uses an LLM (GPT-4o-mini) as a Master Orchestrator that decides which specialized '
        'agent tools to call based on user conversation. The architecture follows a reactive agentic loop '
        'powered by LangGraph.'
    )

    pdf.section_title('Technology Stack')
    pdf.bullet_point('Backend: Python FastAPI + LangGraph + OpenAI GPT-4o-mini')
    pdf.bullet_point('Frontend: React + Vite')
    pdf.bullet_point('Database: SQLite via SQLModel/SQLAlchemy')
    pdf.bullet_point('Agent Framework: LangGraph (StateGraph with tool calling)')
    pdf.bullet_point('Real-time: WebSocket for timeline updates')
    pdf.bullet_point('Channels: Web Chat, Store Kiosk, WhatsApp')

    pdf.section_title('Core Agent Loop')
    pdf.code_block(
        'START\n'
        '  |\n'
        '  v\n'
        '[Agent Node (LLM)] --> decides --> [Tool Node (executes tools)]\n'
        '  ^                                      |\n'
        '  |______________________________________|   (loop)\n'
        '  |\n'
        '  v\n'
        ' END (when LLM has no more tool calls)'
    )

    pdf.body_text(
        'The LLM receives the user message plus all 12 tool definitions. It decides which tool(s) to call, '
        'the Tool Node executes them, results go back to the LLM, and the LLM either calls more tools or '
        'generates a final text response to the user.'
    )

    # ======================== 2. DATABASE LAYER ========================
    pdf.add_page()
    pdf.chapter_title('2. Database Layer')
    pdf.body_text('File: backend/database.py')

    pdf.section_title('Database Configuration')
    pdf.code_block(
        'DATABASE_URL = "sqlite:///./retail_agent.db"\n'
        'engine = create_engine(\n'
        '    DATABASE_URL,\n'
        '    echo=True,\n'
        '    connect_args={"check_same_thread": False}\n'
        ')'
    )

    pdf.section_title('Key Functions')
    widths = [45, 145]
    pdf.table_header(['Function', 'Purpose'], widths)
    pdf.table_row(['init_db()', 'Creates all tables from SQLModel metadata'], widths)
    pdf.table_row(['get_session()', 'Yields a session (FastAPI dependency injection)'], widths)
    pdf.table_row(['get_db_session()', 'Returns a session directly (for agent tools)'], widths)

    pdf.ln(4)
    pdf.body_text(
        'SQLite Pragma: On every connection, PRAGMA foreign_keys=ON is enforced via SQLAlchemy event '
        'listener _set_sqlite_pragma to ensure foreign key constraints are respected.'
    )

    pdf.section_title('Dual Database Architecture')
    pdf.body_text(
        'The project uses TWO separate SQLite databases:\n'
        '1. retail_agent.db - Main business database (products, customers, orders, cart)\n'
        '2. chat_history.db - Conversation persistence database (chat messages, sessions)\n\n'
        'This separation keeps business data clean from transient chat data.'
    )

    # ======================== 3. MODELS ========================
    pdf.add_page()
    pdf.chapter_title('3. Models (Data Schema)')
    pdf.body_text(
        'File: backend/models.py\n\n'
        'All models use SQLModel (which combines SQLAlchemy + Pydantic). '
        'Each model maps to a database table.'
    )

    widths = [35, 35, 120]
    pdf.table_header(['Model', 'Primary Key', 'Description'], widths)
    pdf.table_row(['Customer', 'customer_id', 'Customer profiles (name, email, address, loyalty_points, customer_type, tier)'], widths)
    pdf.table_row(['Product', 'product_id', 'Product catalog (name, category, gender, price, quantity, availability, store_ids, season, festival, image, loyalty_points)'], widths)
    pdf.table_row(['Store', 'store_id', 'Physical store locations (name, address, latitude, longitude)'], widths)
    pdf.table_row(['OrderHistory', 'transaction_id', 'Past orders (customer_id, product_id, dates, amount, mode, payment_method)'], widths)
    pdf.table_row(['StoreKeeperTransaction', 'id', 'Store keeper transaction logs'], widths)
    pdf.table_row(['AdminDashboardData', 'id', 'Pre-computed admin analytics data'], widths)
    pdf.table_row(['Cart', 'order_id', 'Shopping cart items (customer_id, product_id, name, price, quantity, size, status)'], widths)
    pdf.table_row(['Payload', 'id', 'Stores JSON payloads per customer'], widths)
    pdf.table_row(['Distance', 'id', 'Customer-to-store distance mappings'], widths)
    pdf.table_row(['Feedback', 'id', 'Customer feedback after purchase'], widths)

    pdf.ln(4)
    pdf.section_title('Key Model Relationships')
    pdf.bullet_point('Cart.customer_id -> Customer.customer_id (Foreign Key)')
    pdf.bullet_point('Cart.product_id -> Product.product_id (Foreign Key)')
    pdf.bullet_point('OrderHistory.customer_id -> Customer.customer_id')
    pdf.bullet_point('OrderHistory.product_id -> Product.product_id')
    pdf.bullet_point('Product.store_ids -> Comma-separated Store.store_id values')

    # ======================== 4. CRUD OPERATIONS ========================
    pdf.add_page()
    pdf.chapter_title('4. CRUD Operations (Universal Pattern)')
    pdf.body_text(
        'File: backend/crud.py\n\n'
        'The project uses a Universal CRUD pattern - one generic class UniversalCRUD that works with '
        'ANY SQLModel table, reducing boilerplate massively.'
    )

    pdf.section_title('UniversalCRUD Class')
    pdf.code_block(
        'class UniversalCRUD:\n'
        '    def __init__(self, model: Type[SQLModel], primary_key: str = "id"):\n'
        '        self.model = model\n'
        '        self.primary_key = primary_key'
    )

    pdf.section_title('All Methods')
    widths = [30, 65, 95]
    pdf.table_header(['Method', 'Signature', 'What It Does'], widths)
    pdf.table_row(['create', '(session, data: dict) -> SQLModel', 'Insert one record into table'], widths)
    pdf.table_row(['bulk_create', '(session, data_list) -> List', 'Insert multiple records at once'], widths)
    pdf.table_row(['get_by_id', '(session, record_id) -> Optional', 'Fetch single record by primary key'], widths)
    pdf.table_row(['get_all', '(session, skip, limit) -> List', 'Paginated fetch of all records'], widths)
    pdf.table_row(['filter', '(session, filters, operators, ...)', 'Dynamic filtering with operators (=, >, <, like, in)'], widths)
    pdf.table_row(['update', '(session, record_id, data)', 'Update specific fields by primary key'], widths)
    pdf.table_row(['delete', '(session, record_id) -> bool', 'Delete record by primary key'], widths)
    pdf.table_row(['count', '(session, filters) -> int', 'Count records matching filters'], widths)
    pdf.table_row(['exists', '(session, filters) -> bool', 'Check if any records match filters'], widths)
    pdf.table_row(['search', '(session, fields, term) -> List', 'Full-text search across multiple fields'], widths)

    pdf.section_title('Pre-configured CRUD Instances')
    pdf.code_block(
        'customer_crud = UniversalCRUD(Customer, primary_key="customer_id")\n'
        'product_crud = UniversalCRUD(Product, primary_key="product_id")\n'
        'store_crud = UniversalCRUD(Store, primary_key="store_id")\n'
        'order_history_crud = UniversalCRUD(OrderHistory, primary_key="transaction_id")\n'
        'cart_crud = UniversalCRUD(Cart, primary_key="order_id")\n'
        'payload_crud = UniversalCRUD(Payload, primary_key="id")'
    )

    pdf.section_title('Specialized CRUD Classes')
    pdf.body_text('These extend UniversalCRUD with model-specific methods:')
    pdf.bullet_point('ProductCRUD: adds search_products(session, query) - searches by name, category, gender, season')
    pdf.bullet_point('CustomerCRUD: adds search_customers(session, query) - searches by name, email, customer_id')
    pdf.bullet_point('CartCRUD: adds get_customer_cart(session, customer_id) - gets active cart items')

    # ======================== 5. AGENT TOOLS ========================
    pdf.add_page()
    pdf.chapter_title('5. Agent Tools (All 12 Tools - Detailed)')
    pdf.body_text(
        'File: backend/intelligent_agent_graph.py\n\n'
        'All tools are decorated with @tool from LangChain. The LLM sees their docstrings and decides '
        'when to call them. Each tool performs specific DB operations and returns JSON responses.'
    )

    # Tool 1
    pdf.section_title('Tool 1: customer_info_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Fetches customer profile information and order history from the database.')

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('customer_id: str - The customer ID to look up')
    pdf.bullet_point('info_type: str = "profile" - Either "profile" or "orders"')

    pdf.sub_section_title('DB Operations')
    pdf.code_block(
        '# For profile:\n'
        'customer = customer_crud.get_by_id(session, customer_id)\n'
        '# Returns: name, email, loyalty_points, tier, address, customer_type\n\n'
        '# For orders:\n'
        'orders = order_history_crud.filter(session, {"customer_id": customer_id})\n'
        '# Returns: list of past orders with dates, amounts, payment methods'
    )

    pdf.sub_section_title('When LLM Calls It')
    pdf.body_text('User says: "Who am I?", "Show my profile", "What are my loyalty points?", "Show my orders"')

    pdf.sub_section_title('Return Format')
    pdf.code_block(
        '{\n'
        '  "customer_name": "John Doe",\n'
        '  "email": "john@example.com",\n'
        '  "loyalty_points": 1500,\n'
        '  "tier": "Gold",\n'
        '  "address": "123 Main St",\n'
        '  "customer_type": "Premium"\n'
        '}'
    )

    # Tool 2
    pdf.add_page()
    pdf.section_title('Tool 2: inventory_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text(
        'The most complex tool. Searches product inventory using multi-criteria filtering, '
        'OR checks store availability for a specific product (offline flow).'
    )

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('search_query: str = "" - Free-text search like "hoodies", "red dress", "products between 1500-2000"')
    pdf.bullet_point('product_id: str = "" - Specific product ID for store availability check (offline flow)')
    pdf.bullet_point('customer_id: str = "" - Used to filter out already-purchased and already-shown products')

    pdf.sub_section_title('DB Operations - Search Mode')
    pdf.code_block(
        '# Load all products\n'
        'all_products = product_crud.get_all(session)\n\n'
        '# Filter by category, gender, season using fuzzy matching\n'
        '# Parse price range from query via _parse_price_band_from_query()\n'
        '# Filter out already purchased products\n'
        'purchased = get_customer_purchased_product_ids(session, customer_id)\n\n'
        '# Filter out already shown products (in-memory dedup)\n'
        '_SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY[(customer_id, query)].add(pid)'
    )

    pdf.sub_section_title('DB Operations - Store Availability Mode')
    pdf.code_block(
        '# Get product details\n'
        'product = product_crud.get_by_id(session, product_id)\n\n'
        '# Parse store_ids (comma-separated)\n'
        'store_ids = product.store_ids.split(",")\n\n'
        '# Fetch each store\n'
        'for sid in store_ids:\n'
        '    store = store_crud.get_by_id(session, sid)\n'
        '    # Build store list with name, address, lat/long'
    )

    pdf.sub_section_title('Price Band Parsing Logic')
    pdf.code_block(
        'def _parse_price_band_from_query(query):\n'
        '    # "between 1500 and 2000" -> min=1500, max=2000\n'
        '    # "above 5000"            -> min=5000\n'
        '    # "under 1000"            -> max=1000\n'
        '    # "1500-2000"             -> min=1500, max=2000'
    )

    pdf.sub_section_title('"Show More" Deduplication Feature')
    pdf.code_block(
        '# In-memory tracking per (customer_id, query) pair\n'
        '_SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY: dict[tuple, set] = {}\n\n'
        '# When user says "show me more hoodies":\n'
        '# Previously shown product IDs are excluded from results\n'
        '# New products are added to the tracking set'
    )

    # Tool 3
    pdf.add_page()
    pdf.section_title('Tool 3: recommendation_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text(
        'Formats raw inventory results into beautiful product recommendation cards for the frontend. '
        'This is a presentation/formatting layer - no direct DB operations.'
    )

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('inventory_data: str - JSON string from inventory_agent output')

    pdf.sub_section_title('DB Operations')
    pdf.body_text('None directly. Works on data passed from inventory_agent.')

    pdf.sub_section_title('Returns')
    pdf.code_block(
        '{\n'
        '  "products": [\n'
        '    {\n'
        '      "product_id": "P001",\n'
        '      "product_name": "Blue Hoodie",\n'
        '      "price": 1500,\n'
        '      "category": "Hoodies",\n'
        '      "image_reference": "hoodie.jpg",\n'
        '      "online_available": true,\n'
        '      "offline_available": true,\n'
        '      "add_to_cart_button": true\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    pdf.sub_section_title('Tool Chaining Rule')
    pdf.body_text('The LLM is instructed to ALWAYS chain: inventory_agent -> recommendation_agent')

    # Tool 4
    pdf.section_title('Tool 4: upsell_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text(
        'Autonomous upselling - suggests accessory products after the user views their cart. '
        'Randomly picks from accessory categories and generates a search query.'
    )

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('customer_id: str')

    pdf.sub_section_title('Logic')
    pdf.code_block(
        'accessory_categories = ["belts", "shoes", "watches", "wallets"]\n'
        'selected = random.choice(accessory_categories)\n'
        'search_query = f"show me {selected}"\n'
        '# LLM then calls inventory_agent with this query'
    )

    pdf.sub_section_title('When Called')
    pdf.body_text('Automatically triggered after view_cart_agent completes. This is an intelligent upselling mechanism.')

    # Tool 5
    pdf.add_page()
    pdf.section_title('Tool 5: add_to_cart_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Adds a product to the customer shopping cart with stock validation and duplicate detection.')

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('product_id: str - Product to add')
    pdf.bullet_point('quantity: int = 1 - How many units')
    pdf.bullet_point('customer_id: str - Which customer')
    pdf.bullet_point('size: str = "M" - Size selection')

    pdf.sub_section_title('DB Operations (Step by Step)')
    pdf.code_block(
        '# Step 1: Validate product exists and check stock\n'
        'product = product_crud.get_by_id(session, product_id)\n'
        'if product.quantity < requested_quantity:\n'
        '    return "Insufficient stock"\n\n'
        '# Step 2: Check if item already in cart (duplicate detection)\n'
        'existing = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "product_id": product_id\n'
        '})\n\n'
        '# Step 3a: If exists -> increment quantity\n'
        'if existing:\n'
        '    cart_crud.update(session, existing.order_id, {\n'
        '        "quantity": existing.quantity + new_quantity\n'
        '    })\n\n'
        '# Step 3b: If new -> create new cart entry\n'
        'else:\n'
        '    order_id = f"ORD-{timestamp}-{random_hex}"\n'
        '    cart_crud.create(session, {\n'
        '        "order_id": order_id,\n'
        '        "customer_id": customer_id,\n'
        '        "product_id": product_id,\n'
        '        "product_name": product.product_name,\n'
        '        "price": product.price,\n'
        '        "quantity": quantity,\n'
        '        "size": size,\n'
        '        "status": "active"\n'
        '    })'
    )

    pdf.sub_section_title('Validation Logic')
    pdf.bullet_point('Checks stock availability before adding')
    pdf.bullet_point('Prevents adding more than available quantity')
    pdf.bullet_point('Handles duplicate detection (same product -> quantity increment)')

    # Tool 6
    pdf.add_page()
    pdf.section_title('Tool 6: view_cart_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Shows all items currently in the customer cart with totals and loyalty points info.')

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('customer_id: str')

    pdf.sub_section_title('DB Operations')
    pdf.code_block(
        '# Get all active cart items\n'
        'cart_items = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "status": "active"\n'
        '})\n\n'
        '# For each item, fetch full product details\n'
        'for item in cart_items:\n'
        '    product = product_crud.get_by_id(session, item.product_id)\n\n'
        '# Get customer loyalty points\n'
        'customer = customer_crud.get_by_id(session, customer_id)'
    )

    pdf.sub_section_title('Returns')
    pdf.code_block(
        '{\n'
        '  "cart_items": [...],\n'
        '  "cart_total": 3500,\n'
        '  "available_loyalty_points": 1500,\n'
        '  "item_count": 3\n'
        '}'
    )

    # Tool 7
    pdf.section_title('Tool 7: remove_from_cart_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Removes a specific item from the customer cart.')

    pdf.sub_section_title('DB Operations')
    pdf.code_block(
        '# Find the cart item\n'
        'cart_item = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "product_id": product_id\n'
        '})\n\n'
        '# Delete it\n'
        'cart_crud.delete(session, cart_item.order_id)'
    )

    # Tool 8
    pdf.add_page()
    pdf.section_title('Tool 8: choose_channel_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Handles online vs offline purchase channel selection at checkout time.')

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('customer_id: str')
    pdf.bullet_point('channel: str = "" - "online" or "offline"')

    pdf.sub_section_title('DB Operations')
    pdf.code_block(
        '# Verify cart has items\n'
        'cart_items = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "status": "active"\n'
        '})'
    )

    pdf.sub_section_title('Flow Routing')
    pdf.bullet_point('If "online" -> proceeds to payment_agent flow')
    pdf.bullet_point('If "offline" -> triggers inventory_agent for store availability')
    pdf.bullet_point('If empty -> asks user to choose between online/offline')

    # Tool 9
    pdf.section_title('Tool 9: payment_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Two-phase payment processing. Phase 1 shows payment options, Phase 2 processes the payment.')

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('customer_id: str')
    pdf.bullet_point('payment_method: str = "" - Empty for Phase 1, or "upi"/"credit card"/"debit card"/"net banking"')

    pdf.sub_section_title('Phase 1: Show Payment Options (no payment_method)')
    pdf.code_block(
        '# Get cart for total calculation\n'
        'cart_items = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "status": "active"\n'
        '})\n'
        '# Returns available payment methods with cart total'
    )

    pdf.sub_section_title('Phase 2: Process Payment (with payment_method)')
    pdf.code_block(
        '# Get cart items\n'
        'cart_items = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "status": "active"\n'
        '})\n\n'
        '# For EACH cart item:\n'
        'for item in cart_items:\n'
        '    # 1. Deduct product stock\n'
        '    deduct_product_quantity(product_id, quantity)\n'
        '    # -> product_crud.get_by_id() then\n'
        '    # -> product_crud.update(session, pid, {"quantity": new_qty})\n\n'
        '    # 2. Create order history record\n'
        '    order_history_crud.create(session, {\n'
        '        "transaction_id": f"ORD-{timestamp}-{random}",\n'
        '        "customer_id": customer_id,\n'
        '        "product_id": product_id,\n'
        '        "amount": price * quantity,\n'
        '        "mode": "online",\n'
        '        "payment_method": payment_method\n'
        '    })\n\n'
        '    # 3. Mark cart item as completed\n'
        '    cart_crud.update(session, item.order_id, {"status": "completed"})'
    )

    pdf.sub_section_title('Critical Flow Rule (from System Prompt)')
    pdf.body_text(
        'Call payment_agent FIRST TIME with only customer_id -> shows options\n'
        'Call payment_agent SECOND TIME with payment_method -> processes payment\n'
        'After SECOND call returns "Payment Successful", IMMEDIATELY call fulfillment_agent'
    )

    # Tool 10
    pdf.add_page()
    pdf.section_title('Tool 10: fulfillment_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text(
        'Handles order fulfillment for both online delivery and offline store pickup. '
        'Different DB operations for each mode.'
    )

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('purchase_type: str = "online" - "online" or "offline"')
    pdf.bullet_point('store_name: str = "" - For offline, which store for pickup')
    pdf.bullet_point('customer_id: str | None')
    pdf.bullet_point('order_id: str | None')

    pdf.sub_section_title('Online Flow DB Operations')
    pdf.code_block(
        '# Get customer address for delivery\n'
        'customer = customer_crud.get_by_id(session, customer_id)\n\n'
        '# Get completed order items\n'
        'cart_items = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "status": "completed"\n'
        '})\n'
        '# Returns delivery confirmation with estimated date'
    )

    pdf.sub_section_title('Offline Flow DB Operations')
    pdf.code_block(
        '# Get active cart items\n'
        'cart_items = cart_crud.filter(session, {\n'
        '    "customer_id": customer_id,\n'
        '    "status": "active"\n'
        '})\n\n'
        '# For each item:\n'
        'for item in cart_items:\n'
        '    # 1. Deduct stock\n'
        '    deduct_product_quantity(product_id, quantity)\n\n'
        '    # 2. Create order with mode="offline"\n'
        '    order_history_crud.create(session, {\n'
        '        ..., "mode": "offline"\n'
        '    })\n\n'
        '    # 3. Mark completed\n'
        '    cart_crud.update(session, item.order_id, {"status": "completed"})'
    )

    pdf.sub_section_title('Flow Differences')
    pdf.bullet_point('Online: payment_agent -> fulfillment_agent -> loyalty_agent -> post_purchase_agent')
    pdf.bullet_point('Offline: inventory_agent (stores) -> fulfillment_agent -> END (no loyalty/post-purchase)')

    # Tool 11
    pdf.section_title('Tool 11: loyalty_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Awards loyalty points to the customer after a successful online purchase.')

    pdf.sub_section_title('DB Operations')
    pdf.code_block(
        '# Step 1: Get current loyalty points\n'
        'customer = customer_crud.get_by_id(session, customer_id)\n\n'
        '# Step 2: Get order items to calculate points earned\n'
        'cart_items = cart_crud.filter(session, {"customer_id": customer_id})\n\n'
        '# Step 3: Each product has a loyalty_points field -> sum them\n'
        'points_earned = sum(product.loyalty_points for product in order_products)\n\n'
        '# Step 4: Update customer loyalty balance\n'
        'customer_crud.update(session, customer_id, {\n'
        '    "loyalty_points": current_points + points_earned\n'
        '})'
    )

    pdf.sub_section_title('When Called')
    pdf.body_text('Automatically after fulfillment_agent in online flow ONLY. Not called for offline purchases.')

    # Tool 12
    pdf.add_page()
    pdf.section_title('Tool 12: post_purchase_agent')
    pdf.sub_section_title('Purpose')
    pdf.body_text('Provides post-purchase services including tracking, feedback, and customer support information.')

    pdf.sub_section_title('Parameters')
    pdf.bullet_point('order_id: str')
    pdf.bullet_point('customer_id: str')

    pdf.sub_section_title('Returns')
    pdf.code_block(
        '{\n'
        '  "order_tracking_link": "...",\n'
        '  "feedback_form_link": "...",\n'
        '  "customer_support_contact": "...",\n'
        '  "return_exchange_policy": "7 days return/exchange"\n'
        '}'
    )

    pdf.sub_section_title('When Called')
    pdf.body_text('Final step in online flow, after loyalty_agent. Not called for offline purchases.')

    # Tools Registration
    pdf.section_title('Tools List Registration')
    pdf.code_block(
        'tools = [\n'
        '    customer_info_agent,      # Tool 1\n'
        '    inventory_agent,          # Tool 2\n'
        '    recommendation_agent,     # Tool 3\n'
        '    upsell_agent,             # Tool 4\n'
        '    add_to_cart_agent,        # Tool 5\n'
        '    view_cart_agent,          # Tool 6\n'
        '    remove_from_cart_agent,   # Tool 7\n'
        '    choose_channel_agent,     # Tool 8\n'
        '    payment_agent,            # Tool 9\n'
        '    fulfillment_agent,        # Tool 10\n'
        '    loyalty_agent,            # Tool 11\n'
        '    post_purchase_agent       # Tool 12\n'
        ']'
    )

    # ======================== 6. AGENT GRAPH ========================
    pdf.add_page()
    pdf.chapter_title('6. Agent Graph & Orchestration (LangGraph)')
    pdf.body_text('File: backend/intelligent_agent_graph.py')

    pdf.section_title('State Definition (AgentState)')
    pdf.code_block(
        'class AgentState(TypedDict):\n'
        '    messages: Annotated[List[BaseMessage], add_messages]  # Conversation\n'
        '    customer_id: str\n'
        '    selected_product: Dict[str, Any] | None\n'
        '    inventory_status: str | None\n'
        '    purchase_channel: str | None       # "online" or "offline"\n'
        '    order_id: str | None\n'
        '    payment_completed: bool\n'
        '    loyalty_points: int\n'
        '    cart_items: List[Dict[str, Any]]    # Products in cart'
    )

    pdf.section_title('Graph Structure')
    pdf.code_block(
        'StateGraph(AgentState)\n'
        '    |-- add_node("agent", agent_node)     # LLM brain\n'
        '    |-- add_node("tools", tool_node)       # Tool executor\n'
        '    |-- set_entry_point("agent")           # Start here\n'
        '    |-- add_conditional_edges("agent",\n'
        '    |       should_continue,               # Route decision\n'
        '    |       {"tools": "tools", "__end__": END})\n'
        '    |-- add_edge("tools", "agent")         # Back to LLM\n'
        '    compile()'
    )

    pdf.section_title('Agent Node (The Brain)')
    pdf.body_text(
        'This is the central decision-maker. It:\n'
        '1. Creates the LLM: ChatOpenAI(model="gpt-4o-mini", temperature=0.1, streaming=True)\n'
        '2. Binds all 12 tools: llm.bind_tools(tools)\n'
        '3. Injects a massive system prompt containing:\n'
        '   - Role definition ("helpful AI shopping assistant")\n'
        '   - Conversation history awareness rules\n'
        '   - Offline flow state tracking rules\n'
        '   - Payment flow rules (two-phase)\n'
        '   - Tool chaining rules (inventory -> recommendation)\n'
        '   - The customer ID injected dynamically'
    )

    pdf.section_title('Routing Logic (should_continue)')
    pdf.code_block(
        'def should_continue(state: AgentState) -> Literal["tools", "__end__"]:\n'
        '    last_message = state["messages"][-1]\n'
        '    if hasattr(last_message, "tool_calls") and last_message.tool_calls:\n'
        '        return "tools"     # LLM wants to call tools\n'
        '    return "__end__"       # LLM is done, return response'
    )

    pdf.section_title('Tool Executor (tool_node)')
    pdf.code_block(
        'def tool_node(state: AgentState):\n'
        '    outputs = []\n'
        '    for tool_call in state["messages"][-1].tool_calls:\n'
        '        tool_result = _execute_tool(tool_call)\n'
        '        outputs.append(ToolMessage(\n'
        '            content=tool_result,\n'
        '            tool_call_id=tool_call["id"]\n'
        '        ))\n'
        '    return {"messages": outputs}'
    )

    pdf.section_title('Run Agent Entry Point')
    pdf.code_block(
        'async def run_agent(customer_id: str, query: str):\n'
        '    graph = create_agent_graph()\n'
        '    initial_state = {\n'
        '        "messages": [HumanMessage(content=query)],\n'
        '        "customer_id": customer_id,\n'
        '        "selected_product": None,\n'
        '        "purchase_channel": None,\n'
        '        "order_id": None,\n'
        '        "payment_completed": False,\n'
        '        "loyalty_points": 0,\n'
        '        "cart_items": [],\n'
        '    }\n'
        '    result = await graph.ainvoke(initial_state)\n'
        '    return result'
    )

    # Complete flows
    pdf.add_page()
    pdf.section_title('Complete Purchase Flows')

    pdf.sub_section_title('Online Purchase Flow')
    pdf.code_block(
        'User: "Show me hoodies"\n'
        '  -> inventory_agent(search_query="hoodies")\n'
        '  -> recommendation_agent(inventory_data)\n'
        '  -> Display products\n\n'
        'User: "Add P123, qty 2"\n'
        '  -> add_to_cart_agent(product_id="P123", quantity=2)\n\n'
        'User: "View cart"\n'
        '  -> view_cart_agent(customer_id="C001")\n'
        '  -> upsell_agent(customer_id="C001")  [automatic]\n\n'
        'User: "Proceed to checkout"\n'
        '  -> choose_channel_agent -> asks online/offline\n\n'
        'User: "Online"\n'
        '  -> payment_agent(customer_id)  [Phase 1: show methods]\n\n'
        'User: "UPI"\n'
        '  -> payment_agent(customer_id, payment_method="upi")  [Phase 2]\n'
        '  -> fulfillment_agent(purchase_type="online")\n'
        '  -> loyalty_agent(order_id, customer_id)\n'
        '  -> post_purchase_agent(order_id, customer_id)'
    )

    pdf.sub_section_title('Offline Purchase Flow')
    pdf.code_block(
        'User: "Show me hoodies"\n'
        '  -> inventory_agent(search_query="hoodies")\n'
        '  -> recommendation_agent(inventory_data)\n\n'
        'User: "Add P123"\n'
        '  -> add_to_cart_agent(...)\n\n'
        'User: "Proceed offline"\n'
        '  -> inventory_agent(product_id="P123")  [shows store list]\n\n'
        'User: "Store ABC"\n'
        '  -> fulfillment_agent(purchase_type="offline", store_name="ABC")\n'
        '  -> END (no loyalty/post-purchase for offline)'
    )

    # ======================== 7. ALL API ENDPOINTS ========================
    pdf.add_page()
    pdf.chapter_title('7. All API Endpoints (Detailed)')
    pdf.body_text('File: backend/main.py')

    pdf.section_title('7.1 Root / Health Check')
    widths = [25, 40, 125]
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/', 'Returns {"message": "Hello world"} - Health check'], widths)

    pdf.section_title('7.2 Product Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/productdatabase/', 'Lists all products with full details, total count'], widths)
    pdf.table_row(['GET', '/productdatabase/{id}', 'Single product by product_id'], widths)

    pdf.section_title('7.3 Customer Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/api/customer/{id}', 'Get customer profile'], widths)
    pdf.table_row(['GET', '/api/customer/{id}/orders', 'Get customer order history'], widths)
    pdf.table_row(['PUT', '/api/customer/{id}', 'Update customer data'], widths)

    pdf.section_title('7.4 Store Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/api/stores', 'List all stores'], widths)
    pdf.table_row(['GET', '/api/stores/{id}', 'Single store details'], widths)

    pdf.section_title('7.5 Cart Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/api/cart/{customer_id}', 'Get customer active cart'], widths)
    pdf.table_row(['POST', '/api/cart', 'Add item to cart'], widths)
    pdf.table_row(['PUT', '/api/cart/update-quantity', 'Update item quantity in cart'], widths)
    pdf.table_row(['PUT', '/api/cart/update-size', 'Update item size in cart'], widths)
    pdf.table_row(['DELETE', '/api/cart/{order_id}', 'Remove item from cart'], widths)
    pdf.table_row(['POST', '/api/cart/apply-loyalty', 'Apply loyalty points discount'], widths)
    pdf.table_row(['POST', '/api/cart/unapply-loyalty', 'Restore loyalty points (undo discount)'], widths)

    pdf.add_page()
    pdf.section_title('7.6 Loyalty Points Logic (Cart Endpoints)')
    pdf.sub_section_title('Apply Loyalty (/api/cart/apply-loyalty)')
    pdf.code_block(
        '# Deducts loyalty points from customer balance\n'
        '# Points used = min(cart_total, customer.loyalty_points)\n'
        '# 1 point = Rs.1 discount\n'
        '# Updates customer.loyalty_points in DB'
    )

    pdf.sub_section_title('Unapply Loyalty (/api/cart/unapply-loyalty)')
    pdf.code_block(
        '# Restores points back to customer\n'
        'new_points = current_points + points_to_restore\n'
        '# Updates customer.loyalty_points in DB'
    )

    pdf.section_title('7.7 Chat Endpoints')
    widths = [25, 40, 125]
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['POST', '/api/chat', 'Main chat endpoint (REST) - sends message to agent'], widths)
    pdf.table_row(['WS', '/ws/chat', 'Real-time WebSocket chat with timeline updates'], widths)
    pdf.table_row(['POST', '/api/kiosk/chat', 'Store kiosk chat endpoint'], widths)

    pdf.sub_section_title('POST /api/chat - Deep Dive')
    pdf.code_block(
        'Request: {"customer_id": "C001", "message": "Show me hoodies"}\n\n'
        'Flow:\n'
        '1. Save user message to chat DB\n'
        '2. Get recent conversation history (limit=1)\n'
        '3. Check price band fast-path\n'
        '   - If "products between 1500-2000" -> bypass LLM\n'
        '   - Directly call inventory_agent + recommendation_agent\n'
        '4. Normal path: result = await run_agent(customer_id, query)\n'
        '5. Parse result messages for tool JSON responses\n'
        '6. Extract timeline messages\n'
        '7. Save assistant response to chat DB\n'
        '8. Return response with agent_calls and timeline'
    )

    pdf.sub_section_title('Price Band Fast-Path')
    pdf.code_block(
        'def _looks_like_price_band_query(text: str) -> bool:\n'
        '    t = text.lower()\n'
        '    # Skip cart/checkout keywords\n'
        '    if re.search(r"\\b(add|buy|purchase|checkout)\\b", t):\n'
        '        return False\n'
        '    # Must mention price keyword + number\n'
        '    if re.search(r"\\b(between|above|under)\\b", t) and re.search(r"\\d", t):\n'
        '        return True\n'
        '    # Direct range: "1500-2000"\n'
        '    if re.search(r"\\b\\d[\\d,]*\\s*-\\s*\\d[\\d,]*\\b", t):\n'
        '        return True\n'
        '    return False'
    )

    pdf.section_title('7.8 Order History Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/api/orders/{customer_id}', 'Get all orders for customer'], widths)
    pdf.table_row(['POST', '/api/orders', 'Create new order'], widths)

    pdf.section_title('7.9 Admin Dashboard Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/api/admin/dashboard', 'Get admin analytics data'], widths)
    pdf.table_row(['GET', '/api/admin/transactions', 'Store keeper transactions'], widths)
    pdf.table_row(['GET', '/api/admin/stores', 'Store management data'], widths)

    pdf.section_title('7.10 Other Endpoints')
    pdf.table_header(['Method', 'Path', 'Description'], widths)
    pdf.table_row(['GET', '/api/distance/{id}', 'Get distances from customer to all stores'], widths)
    pdf.table_row(['POST', '/api/feedback', 'Submit customer feedback'], widths)
    pdf.table_row(['GET', '/api/feedback/{id}', 'Get customer feedback'], widths)
    pdf.table_row(['GET', '/api/chat/history/{id}', 'Get conversation history'], widths)
    pdf.table_row(['DELETE', '/api/chat/history/{id}', 'Clear conversation history'], widths)
    pdf.table_row(['GET', '/api/payload/{id}', 'Get stored payload'], widths)
    pdf.table_row(['POST', '/api/payload', 'Save payload'], widths)
    pdf.table_row(['GET', '/webhook', 'WhatsApp webhook verification'], widths)
    pdf.table_row(['POST', '/webhook', 'Receive WhatsApp messages'], widths)

    # ======================== 8. WEBSOCKET ========================
    pdf.add_page()
    pdf.chapter_title('8. WebSocket Real-time Communication')
    pdf.body_text('Endpoint: ws/chat (backend/main.py)')

    pdf.section_title('Message Types Sent to Client')
    widths = [45, 145]
    pdf.table_header(['Type', 'Purpose'], widths)
    pdf.table_row(['timeline_start', 'An agent tool started executing'], widths)
    pdf.table_row(['timeline_log', 'Log message from agent execution'], widths)
    pdf.table_row(['timeline_complete', 'Agent tool finished successfully'], widths)
    pdf.table_row(['timeline_error', 'Agent tool errored'], widths)
    pdf.table_row(['text_delta', 'Streaming text chunk from AI response'], widths)
    pdf.table_row(['final_response', 'Complete parsed response data (JSON)'], widths)
    pdf.table_row(['run_end', 'All processing complete'], widths)

    pdf.section_title('Client Message Format')
    pdf.code_block(
        '{\n'
        '  "type": "chat",\n'
        '  "request_id": "unique-id",\n'
        '  "customer_id": "C001",\n'
        '  "message": "Show me hoodies"\n'
        '}'
    )

    pdf.section_title('Server Streaming Sequence (Example)')
    pdf.code_block(
        '{"type": "timeline_start", "agent": "Inventory Agent", "status": "in_progress"}\n'
        '{"type": "timeline_log", "tool": "inventory_agent", "text": "Searching..."}\n'
        '{"type": "timeline_complete", "tool": "inventory_agent", "status": "completed"}\n'
        '{"type": "timeline_start", "agent": "Recommendation Agent"}\n'
        '{"type": "timeline_complete", "tool": "recommendation_agent"}\n'
        '{"type": "text_delta", "delta": "Here are some "}\n'
        '{"type": "text_delta", "delta": "hoodie recommendations..."}\n'
        '{"type": "final_response", "data": {...}}\n'
        '{"type": "run_end"}'
    )

    pdf.section_title('Helper Functions')
    pdf.bullet_point('_ws_stream_text() - Sends text in small chunks (24 chars) for typewriter streaming effect')
    pdf.bullet_point('_summarize_tool_start() - Human-readable description of tool call start')
    pdf.bullet_point('_summarize_tool_result() - Human-readable description of tool result')
    pdf.bullet_point('_extract_selected_store_name() - Parses store name from user message')

    # ======================== 9. CHAT DATABASE ========================
    pdf.add_page()
    pdf.chapter_title('9. Chat Database & History')
    pdf.body_text(
        'File: backend/chat_database.py\n\n'
        'This is a SEPARATE SQLite database (chat_history.db) for conversation persistence, '
        'isolated from the main business database.'
    )

    pdf.section_title('Schema')
    pdf.code_block(
        'CREATE TABLE conversations (\n'
        '    id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
        '    customer_id TEXT NOT NULL,\n'
        '    session_id TEXT NOT NULL,\n'
        '    role TEXT NOT NULL,          -- "user" or "assistant"\n'
        '    content TEXT NOT NULL,\n'
        '    agent_calls TEXT,            -- JSON array of tools called\n'
        '    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP\n'
        ')'
    )

    pdf.section_title('Functions')
    widths = [55, 135]
    pdf.table_header(['Function', 'Purpose'], widths)
    pdf.table_row(['init_database()', 'Creates conversations and payload tables'], widths)
    pdf.table_row(['save_message()', 'Stores a message with timestamp and agent_calls'], widths)
    pdf.table_row(['get_conversation_history()', 'Retrieves recent messages chronologically'], widths)
    pdf.table_row(['clear_conversation_history()', 'Deletes all messages for a customer'], widths)
    pdf.table_row(['get_conversation_stats()', 'Returns message counts and session info'], widths)

    # ======================== 10. STORE KIOSK ========================
    pdf.section_title(' ')
    pdf.chapter_title('10. Store Kiosk Flow')
    pdf.body_text(
        'File: backend/store_kiosk_graph.py\n\n'
        'A separate LangGraph for in-store kiosk interactions. More structured and linear '
        'compared to the main chatbot. Used when customers interact at physical store kiosks.'
    )

    pdf.section_title('Kiosk Nodes')
    widths = [50, 140]
    pdf.table_header(['Node', 'Purpose'], widths)
    pdf.table_row(['welcome_node', 'Greets customer, identifies them'], widths)
    pdf.table_row(['kiosk_add_to_cart_agent', 'Adds products to cart in-store'], widths)
    pdf.table_row(['payment_prompt_node', 'Asks for payment'], widths)
    pdf.table_row(['payment_method_node', 'Processes payment'], widths)
    pdf.table_row(['fulfillment_node', 'Completes in-store purchase'], widths)
    pdf.table_row(['loyalty_node', 'Awards loyalty points'], widths)
    pdf.table_row(['post_purchase_node', 'Post-purchase feedback'], widths)

    pdf.body_text('Endpoint: POST /api/kiosk/chat -> chat_with_kiosk()')

    # ======================== 11. WHATSAPP ========================
    pdf.add_page()
    pdf.chapter_title('11. WhatsApp Integration')
    pdf.body_text('File: backend/whatsapp.py')

    pdf.section_title('Functions')
    widths = [50, 140]
    pdf.table_header(['Function', 'Purpose'], widths)
    pdf.table_row(['send_message()', 'Sends a WhatsApp message via Meta API'], widths)
    pdf.table_row(['get_text_message_input()', 'Formats text for WhatsApp API payload'], widths)

    pdf.section_title('Webhook Endpoints')
    pdf.bullet_point('GET /webhook - Meta verification handshake (challenge-response)')
    pdf.bullet_point('POST /webhook - Receives incoming WhatsApp messages, processes via agent, responds')

    # ======================== 12. SECURITY ========================
    pdf.chapter_title('12. Security')
    pdf.body_text('File: backend/security.py')
    pdf.bullet_point('signature_required - Decorator that validates WhatsApp webhook signatures using HMAC-SHA256')
    pdf.bullet_point('Ensures incoming webhook requests are genuinely from Meta/WhatsApp')

    # ======================== 13. DATA IMPORT ========================
    pdf.chapter_title('13. Data Import Pipeline')
    pdf.body_text('File: backend/utility/import_data.py')
    pdf.body_text('Imports CSV data from backend/data/ directory into SQLite tables:')

    widths = [55, 55, 80]
    pdf.table_header(['Function', 'Source CSV', 'Target Table'], widths)
    pdf.table_row(['import_customers()', 'customer_data.csv', 'customers'], widths)
    pdf.table_row(['import_products()', 'product_data.csv', 'products'], widths)
    pdf.table_row(['import_stores()', 'outlate_data.csv', 'stores'], widths)
    pdf.table_row(['import_order_history()', 'order_history.csv', 'orderhistory'], widths)
    pdf.table_row(['import_store_keeper()', 'store keeper data.csv', 'storekeeprtxn'], widths)
    pdf.table_row(['import_admin_dashboard()', 'admin_dashboard.csv', 'admindashboard'], widths)

    pdf.ln(4)
    pdf.body_text('Execution order matters - foreign key relationships require customers & products first, then orders.')

    # ======================== 14. MIGRATIONS ========================
    pdf.add_page()
    pdf.chapter_title('14. Migration Scripts')
    pdf.body_text('Folder: backend/migrations/')

    widths = [65, 125]
    pdf.table_header(['Script', 'Purpose'], widths)
    pdf.table_row(['add_quantity_column.py', 'Adds quantity column to products table'], widths)
    pdf.table_row(['add_customer_type_columns.py', 'Adds customer_type and type_justification to customers'], widths)
    pdf.table_row(['add_discount_column.py', 'Adds discount column'], widths)
    pdf.table_row(['add_quantity_to_cart.py', 'Adds quantity to cart table'], widths)
    pdf.table_row(['migrate_cart_schema.py', 'Schema migration for cart restructuring'], widths)
    pdf.table_row(['populate_random_quantities.py', 'Fills random stock quantities (--seed for reproducibility)'], widths)
    pdf.table_row(['fix_store_keeper_fk.py', 'Fixes foreign key in store keeper transactions'], widths)

    # ======================== 15. CONFIGURATION ========================
    pdf.chapter_title('15. Configuration')
    pdf.body_text('File: backend/config.py - Loads configuration from environment variables')

    pdf.section_title('Environment Variables (.env.example)')
    pdf.code_block(
        'OPENAI_API_KEY=your_openai_api_key_here\n'
        'HOST=0.0.0.0\n'
        'PORT=8000\n'
        'ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000\n'
        'LLM_TEMPERATURE=0.1\n'
        'LLM_MODEL=gpt-4o-mini'
    )

    # ======================== 16. DESIGN PATTERNS ========================
    pdf.add_page()
    pdf.chapter_title('16. Key Design Patterns Summary')

    patterns = [
        ('1. Universal CRUD', 'One generic class for all DB operations, reducing boilerplate code across all models.'),
        ('2. Tool-calling LLM', 'GPT-4o-mini decides which agent tools to invoke via OpenAI function calling. The LLM sees tool docstrings and schemas.'),
        ('3. StateGraph (LangGraph)', 'Reactive loop: Agent -> Tools -> Agent -> Tools -> End. State is passed between nodes.'),
        ('4. Two-phase Payment', 'Phase 1 shows payment options (no processing). Phase 2 actually processes the payment. Prevents accidental charges.'),
        ('5. Dual Purchase Flow', 'Online flow (full pipeline with loyalty points) vs Offline flow (abbreviated, no loyalty/post-purchase).'),
        ('6. In-memory Deduplication', 'Prevents showing same products twice using _SHOWN_PRODUCT_IDS_BY_CUSTOMER_AND_QUERY dictionary.'),
        ('7. Price Band Fast-path', 'Bypasses LLM for simple price range queries, directly calling inventory + recommendation tools.'),
        ('8. Real-time WebSocket Timeline', 'Shows which agents are working in real-time with streaming text deltas.'),
        ('9. Separate Chat DB', 'Conversation persistence isolated from business data in a separate SQLite database.'),
        ('10. Automatic Upselling', 'Random accessory suggestion triggered after cart view - intelligent cross-selling.'),
    ]

    for title, desc in patterns:
        pdf.sub_section_title(title)
        pdf.body_text(desc)

    # ======================== FINAL PAGE ========================
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, 'End of Documentation', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, 'EY Techathon Retail Agent', 0, 1, 'C')
    pdf.cell(0, 10, 'Multi-Agent AI Retail Assistant', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, 'Total Tools: 12 | Total Endpoints: 25+ | Database Tables: 10', 0, 1, 'C')
    pdf.cell(0, 8, 'Architecture: LangGraph StateGraph with GPT-4o-mini Orchestrator', 0, 1, 'C')

    # Save
    output_path = 'EY_Techathon_Retail_Agent_Documentation.pdf'
    pdf.output(output_path)
    print(f"\nPDF generated successfully: {output_path}")
    print(f"Total pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    create_pdf()