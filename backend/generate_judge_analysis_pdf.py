"""
Generate a comprehensive Judge Analysis PDF for the EY Techathon Retail Agent project.
"""

from fpdf import FPDF
import os


class AnalysisPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "EY Techathon 5.0 | Retail [ABFRL] - Judge Analysis Report", align="C")
        self.ln(4)
        self.set_draw_color(200, 50, 50)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title, emoji=""):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(180, 40, 40)
        self.ln(4)
        self.cell(0, 10, f"{emoji}  {title}", ln=True)
        self.set_draw_color(180, 40, 40)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 120, self.get_y())
        self.ln(4)

    def sub_title(self, title, emoji=""):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(50, 50, 50)
        self.ln(2)
        text = f"{emoji}  {title}" if emoji else title
        self.cell(0, 8, text, ln=True)
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text, indent=15):
        x = self.get_x()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(indent, 5.5, "  ->")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def table_header(self, cols, widths):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(180, 40, 40)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align="C")
        self.ln()

    def table_row(self, cols, widths, fill=False):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        if fill:
            self.set_fill_color(245, 245, 245)
        else:
            self.set_fill_color(255, 255, 255)

        max_lines = 1
        col_texts = []
        for i, col in enumerate(cols):
            lines = self.multi_cell(widths[i], 5, col, split_only=True)
            col_texts.append(lines)
            if len(lines) > max_lines:
                max_lines = len(lines)

        row_height = max_lines * 5.5
        y_start = self.get_y()
        x_start = self.get_x()

        for i, lines in enumerate(col_texts):
            x = x_start + sum(widths[:i])
            self.set_xy(x, y_start)
            self.cell(widths[i], row_height, "", border=1, fill=fill)
            for j, line in enumerate(lines):
                self.set_xy(x + 1, y_start + j * 5.5 + 1)
                self.cell(widths[i] - 2, 5, line)

        self.set_xy(x_start, y_start + row_height)


def generate_pdf():
    pdf = AnalysisPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ============ COVER PAGE ============
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 15, "EY Techathon 5.0", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 12, "Retail [ABFRL] - AI Sales Agent", ln=True, align="C")
    pdf.ln(8)
    pdf.set_draw_color(180, 40, 40)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Judge Evaluation Analysis & Preparation Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, "Comprehensive project assessment against problem statement,", ln=True, align="C")
    pdf.cell(0, 8, "anticipated jury questions, and readiness evaluation", ln=True, align="C")
    pdf.ln(30)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Project: RetailBuddy - AI-Driven Conversational Sales Agent", ln=True, align="C")
    pdf.cell(0, 6, "Technology Stack: LangGraph + GPT-4o-mini + FastAPI + React + Twilio", ln=True, align="C")
    pdf.cell(0, 6, "Channels: Web Chat | WhatsApp | In-Store Kiosk", ln=True, align="C")

    # ============ PAGE 2: PROJECT STRENGTHS ============
    pdf.add_page()
    pdf.section_title("PROJECT STRENGTHS", "1.")

    pdf.sub_title("Evaluation Summary Table")
    w = [55, 75, 60]
    pdf.table_header(["Evaluation Parameter", "Your Coverage", "Verdict"], w)
    rows = [
        ["Scope of Problem Covered", "Covers ~85% of the problem statement", "Strong"],
        ["Solution Design & Tech", "LangGraph ReAct agent + 12 tool agents + WhatsApp + Kiosk + Admin", "Very Strong"],
        ["Uniqueness & Innovation", "Real-time WS streaming timeline, autonomous upsell, tier-based ranking", "Strong"],
        ["End-user Benefit & Impact", "Multi-persona dashboards (Customer, StoreKeeper, Admin), omnichannel", "Good"],
    ]
    for i, row in enumerate(rows):
        pdf.table_row(row, w, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.sub_title("Key Differentiators (What Sets You Apart)")
    differentiators = [
        "12 specialized @tool agents orchestrated by GPT-4o-mini via LangGraph ReAct loop - this is genuinely agentic AI, not just prompt chaining.",
        "Real-time Agent Timeline streamed via WebSocket - judges can visually see the orchestration happening live with timeline_start, timeline_log, timeline_end events.",
        "3 channels working: Web Chat (WebSocket), WhatsApp (Twilio), In-Store Kiosk - true omnichannel.",
        "Omnichannel cart transfer: switch_to_online tool lets kiosk items move to online checkout and vice versa.",
        "Autonomous upsell_agent - auto-triggers cross-sell recommendations after viewing cart without user asking.",
        "Customer tier-based product ranking: tier_1 (premium) customers see expensive items first, tier_3 (budget) customers see affordable options first.",
        "Admin AI Insights: GPT-4o-mini analyzes actual store metrics and generates strategic business recommendations.",
        "Google Maps integration for nearest store locator with pre-computed distance table.",
    ]
    for d in differentiators:
        pdf.bullet(d)

    # ============ PAGE 3: ARCHITECTURE ============
    pdf.add_page()
    pdf.section_title("SOLUTION ARCHITECTURE", "2.")

    pdf.sub_title("Agent Tools (12 Specialized Worker Agents)")
    w2 = [8, 42, 140]
    pdf.table_header(["#", "Tool Name", "Purpose"], w2)
    tools = [
        ["1", "customer_info_agent", "Fetches customer profile (name, phone, address, loyalty) or order history"],
        ["2", "inventory_agent", "Primary product search with keyword scoring, gender/price filtering, tier-based sorting, dedup"],
        ["3", "recommendation_agent", "Display layer - formats raw inventory results into UI-friendly product cards with images"],
        ["4", "add_to_cart_agent", "Adds product to cart table with stock validation, discount calc, unique order ID generation"],
        ["5", "view_cart_agent", "Lists all pending cart items with prices, discounts, savings, and total amount"],
        ["6", "remove_from_cart_agent", "Deletes a specific cart item by order_id, verifying customer ownership"],
        ["7", "choose_channel_agent", "Presents online vs offline purchase channel choice with cart summary"],
        ["8", "payment_agent", "Two-stage: (1) show 4 payment options, (2) process payment, update cart status to paid"],
        ["9", "fulfillment_agent", "Online: confirms home delivery. Offline: assigns store, sends WhatsApp pickup confirmation"],
        ["10", "loyalty_agent", "Awards loyalty points based on product loyalty_points x quantity, generates coupon codes"],
        ["11", "post_purchase_agent", "DB finalizer: creates OrderHistory + StoreKeeperTransaction records, deducts inventory"],
        ["12", "upsell_agent", "Autonomous cross-sell: maps cart categories to complementary items (Shirt->Belt/Shoes)"],
    ]
    for i, t in enumerate(tools):
        pdf.table_row(t, w2, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.sub_title("LangGraph Architecture")
    pdf.body_text(
        "Main Agent Graph (intelligent_agent_graph.py): Uses a ReAct (Reasoning + Acting) loop pattern with 2 nodes:\n"
        "  START -> [agent] -> (should_continue?) -> [tools] -> [agent] -> ... -> END\n\n"
        "The 'agent' node invokes GPT-4o-mini with all 12 tools bound. A ~3000-word system prompt encodes the entire "
        "shopping workflow. The 'tools' node executes requested tools and returns results. Routing: if last AI message "
        "has tool_calls -> route to tools, else -> END.\n\n"
        "Store Kiosk Graph (store_kiosk_graph.py): Deterministic linear pipeline (no LLM decision-making):\n"
        "  START -> welcome -> payment_prompt -> payment_method -> fulfillment -> loyalty -> post_purchase -> END\n\n"
        "WhatsApp Graph (intelligent_whatsapp_graph.py): Full clone of main agent graph with Twilio I/O layer. "
        "Responses formatted as WhatsApp text cards + product images sent as separate media messages."
    )

    # ============ PAGE 4: GAPS ============
    pdf.add_page()
    pdf.section_title("GAPS & WEAKNESSES", "3.")

    pdf.sub_title("Gap Analysis vs Problem Statement")
    w3 = [45, 75, 70]
    pdf.table_header(["Gap", "Requirement", "Your Status"], w3)
    gaps = [
        ["Voice Assistant", "'voice assistant' channel mentioned in PS", "MISSING entirely"],
        ["Session Continuity", "'customer switches from mobile to kiosk'", "PARTIAL - cart transfers, but chat history doesn't transfer across channels"],
        ["Payment Gateway Stub", "'Dummy API for authorizations, captures, declined transactions'", "BASIC - payment is just status update, no simulated failure/retry"],
        ["10+ Customer Profiles", ">=10 customers with demographics, history, loyalty tier", "Need to verify data completeness"],
        ["Reserve-in-Store", "'reserve in-store for try-on'", "PARTIAL - offline booking exists but no explicit try-on reservation"],
        ["Shipment Tracking", "Post-Purchase Agent should 'track shipments'", "MISSING - no tracking simulation"],
        ["Returns/Exchanges", "'Handles returns/exchanges'", "COVERED - Return initiation with 24h cooling + monitoring agent"],
        ["POS Integration", "'barcode scan and payment'", "COVERED - Barcode panel in kiosk"],
    ]
    for i, g in enumerate(gaps):
        pdf.table_row(g, w3, fill=(i % 2 == 0))

    # ============ PAGE 5-7: JURY QUESTIONS ============
    pdf.add_page()
    pdf.section_title("ANTICIPATED JURY QUESTIONS", "4.")

    # Critical Questions
    pdf.sub_title("CRITICAL Questions (Very Likely to Be Asked)", "RED CIRCLE")
    pdf.ln(2)

    questions = [
        {
            "q": "Q1: How does session continuity work when a customer moves from web chat to the in-store kiosk?",
            "a": "Cart items persist in the DB with a 'channel' field. When the customer logs into the kiosk, welcome_node fetches all their pending offline cart items. The switch_to_online tool reverses the direction. However, conversation context (chat history) does NOT transfer between channels - be honest about this limitation. In production, we'd add a session service that shares summarized context."
        },
        {
            "q": "Q2: Walk us through what happens when a payment fails. How does the agent recover?",
            "a": "We validate inputs and handle edge cases, but a full retry flow with exponential backoff was deprioritized in favor of other features. Our architecture supports adding it as another @tool function. The payment_agent currently handles method selection and processing, but doesn't simulate declined transactions."
        },
        {
            "q": "Q3: How are the Worker Agents actually 'loosely coupled'? Can you add a new agent easily?",
            "a": "Each agent is a @tool decorated Python function. Adding a new agent (e.g., Gift Wrapping Agent) requires: (1) write one new function, (2) decorate with @tool, (3) add to the tools list. The LLM automatically decides when to invoke it based on the system prompt. No graph rewiring needed. This is the power of the ReAct pattern."
        },
        {
            "q": "Q4: What LLM are you using, and why? What's the latency like?",
            "a": "GPT-4o-mini, temperature 0.1. Chosen for cost-efficiency (10x cheaper than GPT-4o) and speed (~1-2s per tool call). WebSocket streaming with chunked delta delivery (24 chars/chunk) reduces perceived latency. The streaming agent timeline gives visual feedback during processing."
        },
        {
            "q": "Q5: How does the Recommendation Agent personalize recommendations?",
            "a": "Three personalization layers: (1) Customer tier ranking - premium customers see premium products first, budget customers see affordable options. (2) Gender-aware filtering - inferred from customer profile or explicit query. (3) Purchase history exclusion - already-bought products filtered out. (4) Relevance scoring across product name, category, season, festival."
        },
    ]

    for item in questions:
        pdf.bold_text(item["q"])
        pdf.body_text(f"Suggested Answer: {item['a']}")
        pdf.ln(2)

    pdf.add_page()
    pdf.sub_title("PROBABLE Questions (Likely to Be Asked)", "YELLOW CIRCLE")
    pdf.ln(2)

    probable = [
        {
            "q": "Q6: How do you prevent hallucinations? The LLM could recommend non-existent products.",
            "a": "The LLM never generates product data. It only decides WHICH tool to call. The inventory_agent tool queries the SQLite database directly - all product data comes from our database, not from the LLM's knowledge. This is a key architectural decision: the LLM is an orchestrator, not a data source."
        },
        {
            "q": "Q7: What's the upsell/cross-sell strategy? How much AOV lift would you expect?",
            "a": "The upsell_agent automatically triggers after cart view. It maps categories to complementary items (Shirt->Belt/Shoes/Watches for men, Kurti->Footwear/Jewellery for women). Combined with tier-based pricing and loyalty discounts, this drives AOV. The agent uses gender-aware complementary category mappings."
        },
        {
            "q": "Q8: How does the Admin dashboard help business stakeholders?",
            "a": "Real-time analytics with: online/offline transaction split, store-level performance, monthly trends, per-customer analysis, AND AI-powered strategic insights generated by GPT-4o-mini analyzing the actual store metrics. Store keepers also get their own per-store dashboard with AI insights and benchmarking."
        },
        {
            "q": "Q9: Can you demonstrate the WhatsApp flow live?",
            "a": "If Twilio is configured with ngrok tunnel, demo it live. If not: 'We have the full integration built with Twilio - message parsing, product card formatting with emojis, image delivery. The WhatsApp agent reuses the same LangGraph as web chat. Due to demo environment constraints, I'll show the code + architecture.'"
        },
        {
            "q": "Q10: What about data privacy? You're sending customer data to OpenAI.",
            "a": "In production, we'd use Azure OpenAI with data residency guarantees. The current prototype uses OpenAI API for rapid development. Customer PII in prompts can be masked. The system prompt instructs the LLM on behavior - actual customer data flows through tool calls which are local DB queries."
        },
    ]

    for item in probable:
        pdf.bold_text(item["q"])
        pdf.body_text(f"Suggested Answer: {item['a']}")
        pdf.ln(2)

    pdf.add_page()
    pdf.sub_title("BONUS Questions (If They Dig Deep)", "GREEN CIRCLE")
    pdf.ln(2)

    bonus = [
        {
            "q": "Q11: Why LangGraph instead of LangChain agents or AutoGen?",
            "a": "LangGraph gives us explicit state management and deterministic tool execution order. Unlike vanilla LangChain agents, we can control the conversation flow, persist state across turns, and build hybrid architectures (ReAct for web, linear for kiosk). The StateGraph with typed state (AgentState) ensures type safety and predictable behavior."
        },
        {
            "q": "Q12: What happens if two kiosk users try to buy the same last-in-stock item?",
            "a": "We check stock at add-to-cart time via product.quantity validation. However, there's no database-level pessimistic locking - a race condition is theoretically possible. For production: we'd add row-level locking or a reservation system with TTL. SQLite's write serialization partially mitigates this in the prototype."
        },
        {
            "q": "Q13: How scalable is this? You're using SQLite and in-memory state.",
            "a": "SQLite is for prototyping. The SQLModel/SQLAlchemy ORM makes swapping to PostgreSQL a config change. In-memory session state (_WHATSAPP_SESSIONS, _SHOWN_PRODUCT_IDS) would move to Redis. FastAPI supports horizontal scaling with Uvicorn workers. The stateless REST endpoints are already horizontally scalable."
        },
    ]

    for item in bonus:
        pdf.bold_text(item["q"])
        pdf.body_text(f"Suggested Answer: {item['a']}")
        pdf.ln(2)

    # ============ PAGE: API ENDPOINTS ============
    pdf.add_page()
    pdf.section_title("API ENDPOINTS OVERVIEW", "5.")

    pdf.sub_title("Key REST Endpoints")
    w4 = [25, 70, 95]
    pdf.table_header(["Method", "Path", "Purpose"], w4)
    endpoints = [
        ["POST", "/api/chat", "Primary chat endpoint (HTTP, non-streaming)"],
        ["WS", "ws://localhost:8000/ws/chat", "Real-time agentic chat with streaming timeline"],
        ["POST", "/api/kiosk/chat", "Kiosk chat endpoint (linear flow)"],
        ["POST", "/webhook", "Twilio WhatsApp webhook"],
        ["GET", "/api/admin/dashboard", "Comprehensive admin analytics"],
        ["GET", "/api/admin/ai-insights", "LLM-powered business insights"],
        ["GET", "/api/store/{id}/transactions", "Store-specific transaction history"],
        ["GET", "/api/store/{id}/ai-insights", "LLM-powered per-store insights"],
        ["POST", "/api/orders/initiate-return", "Return with 24h cooling period"],
        ["POST", "/api/orders/return-monitoring", "Batch agent - auto-completes returns"],
        ["GET", "/api/locate-us/{cust}", "Nearby stores with distance/map URL"],
        ["POST", "/api/cart/apply-loyalty", "Apply loyalty points (1 pt = Rs.1)"],
        ["POST", "/api/wishlist/toggle", "Toggle product in wishlist"],
        ["POST", "/api/cart/switch-to-online", "Switch offline cart to online"],
        ["GET", "/api/customer/{id}/{role}", "Customer/storekeeper profile by role"],
        ["POST", "/api/feedback/{pid}/{cid}", "Submit 1-5 star rating"],
    ]
    for i, e in enumerate(endpoints):
        pdf.table_row(e, w4, fill=(i % 2 == 0))

    # ============ PAGE: FINAL VERDICT ============
    pdf.add_page()
    pdf.section_title("FINAL VERDICT & READINESS", "6.")

    pdf.sub_title("Score Estimate (Per Evaluation Parameter)")
    w5 = [55, 25, 110]
    pdf.table_header(["Parameter", "Score", "Notes"], w5)
    scores = [
        ["Scope of problem covered", "8 / 10", "Missing voice channel, partial session continuity across channels"],
        ["Solution design & technology", "9 / 10", "Excellent LangGraph architecture, clean separation, real DB, 12 tools"],
        ["Uniqueness & innovation", "8 / 10", "Streaming timeline, autonomous upsell, tier-based ranking are differentiators"],
        ["End-user benefit & impact", "7.5 / 10", "Multi-persona coverage great, demo polish matters for final impression"],
    ]
    for i, s in enumerate(scores):
        pdf.table_row(s, w5, fill=(i % 2 == 0))

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 130, 0)
    pdf.cell(0, 10, "OVERALL: 8.1 / 10 - STRONG FINALIST CANDIDATE", ln=True, align="C")
    pdf.ln(8)

    pdf.sub_title("Top 3 Action Items Before Semi-Final")
    pdf.ln(2)

    actions = [
        "1. POLISH THE DEMO FLOW: Practice a 5-minute scripted demo: Customer searches -> product cards appear -> add to cart -> upsell triggers -> payment -> kiosk pickup -> show WhatsApp message -> Admin dashboard. The streaming timeline is your WOW moment - make sure it works smoothly.",
        "2. PREPARE FOR SESSION CONTINUITY QUESTION: This is your biggest gap vs the problem statement. Have a clear answer: 'Cart data persists across channels. Conversation context is channel-specific by design - in production, we'd add a session service that shares summarized context.'",
        "3. HAVE EDGE-CASE DEMOS READY: Show an out-of-stock scenario (agent handles it gracefully), show a return initiation (24h cooling period), and show the upsell auto-triggering after viewing cart. These demonstrate robustness and thoughtful engineering.",
    ]
    for a in actions:
        pdf.body_text(a)
        pdf.ln(2)

    pdf.ln(6)
    pdf.sub_title("Presentation Sequence (10 minutes)")
    pdf.body_text(
        "Minute 0-1: Quick intro - team, problem summary, solution overview (1 slide)\n"
        "Minute 1-2: Architecture slide - show the multi-agent diagram with 12 tools + 3 channels\n"
        "Minute 2-7: LIVE DEMO (this is where you win or lose)\n"
        "  - Customer web chat: search -> recommend -> add to cart -> upsell triggers\n"
        "  - Show Agent Timeline streaming in real-time\n"
        "  - Cart -> Payment -> Fulfillment -> Loyalty -> Post-purchase\n"
        "  - Kiosk: customer logs in, sees offline cart, pays\n"
        "  - Admin dashboard with AI insights\n"
        "  - (Optional) WhatsApp if Twilio is live\n"
        "Minute 7-9: Value proposition slide - AOV impact, conversion rate improvement\n"
        "Minute 9-10: Summary + future roadmap (voice, session sync, production scaling)"
    )

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 8, "KEY TAKEAWAY: You have a genuinely strong project. The multi-agent architecture", ln=True, align="C")
    pdf.cell(0, 8, "with LangGraph, real database, 3 channels, and streaming timeline puts you", ln=True, align="C")
    pdf.cell(0, 8, "well above average. Focus your presentation on the LIVE DEMO - that's where you'll win.", ln=True, align="C")

    # Save
    output_path = os.path.join(os.path.dirname(__file__), "Judge_Analysis_Report.pdf")
    pdf.output(output_path)
    print(f"\nPDF generated successfully at: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_pdf()
