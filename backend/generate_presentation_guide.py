from fpdf import FPDF
import textwrap


class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'B', 9)
            self.set_text_color(100, 100, 100)
            self.cell(
                0, 8, 'EY Techathon - Semi Finals Presentation Guide', 0, 1, 'C')
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.ln(4)
        self.cell(0, 10, title, 0, 1, 'L')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(0, 80, 130)
        self.ln(3)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

    def sub_section(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.ln(2)
        self.cell(0, 7, title, 0, 1, 'L')
        self.ln(1)

    def body(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def speak_script(self, text):
        """What to actually SAY - highlighted differently"""
        self.set_font('Helvetica', 'I', 10)
        self.set_fill_color(255, 248, 230)
        self.set_text_color(80, 50, 0)
        x = self.get_x()
        self.set_x(x + 5)
        self.cell(3, 5.5, '', 0, 0)
        self.set_draw_color(255, 180, 0)
        self.set_line_width(0.8)
        x_line = self.get_x() - 2
        y_start = self.get_y()
        self.multi_cell(175, 5.5, '"' + text + '"', 0, 'L', fill=True)
        y_end = self.get_y()
        self.line(x_line, y_start, x_line, y_end)
        self.set_line_width(0.2)
        self.ln(2)

    def action_item(self, text):
        """Demo action - what to DO on screen"""
        self.set_font('Helvetica', 'B', 9.5)
        self.set_fill_color(230, 245, 255)
        self.set_text_color(0, 70, 130)
        self.cell(5, 5.5, '', 0, 0)
        self.cell(18, 5.5, 'ACTION:', 0, 0, 'L', fill=True)
        self.set_font('Helvetica', '', 9.5)
        self.multi_cell(0, 5.5, text, 0, 'L', fill=True)
        self.ln(2)

    def time_marker(self, time_range, section_name):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.cell(35, 8, ' ' + time_range, 0, 0, 'L', fill=True)
        self.set_fill_color(230, 238, 248)
        self.set_text_color(0, 51, 102)
        self.cell(155, 8, '  ' + section_name, 0, 1, 'L', fill=True)
        self.ln(3)

    def bullet(self, text, indent=10):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(4, 5.5, chr(149), 0, 0)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def key_point(self, text):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(180, 0, 0)
        self.cell(5, 5.5, '', 0, 0)
        self.cell(0, 5.5, '>> ' + text, 0, 1)
        self.set_text_color(30, 30, 30)
        self.ln(1)

    def tip_box(self, text):
        self.set_font('Helvetica', 'I', 9)
        self.set_fill_color(240, 255, 240)
        self.set_text_color(0, 100, 0)
        self.set_draw_color(0, 150, 0)
        self.cell(5, 5, '', 0, 0)
        self.multi_cell(180, 5, 'TIP: ' + text, 1, 'L', fill=True)
        self.ln(3)

    def code_block(self, code):
        self.set_font('Courier', '', 8)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        for line in code.split('\n'):
            wrapped = textwrap.wrap(line, width=100) or ['']
            for wl in wrapped:
                self.cell(0, 4.5, '  ' + wl, 0, 1, 'L', fill=True)
        self.ln(2)

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
        max_lines = 1
        cell_texts = []
        for i, col in enumerate(cols):
            wrapped = textwrap.wrap(
                str(col), width=int(widths[i] / 2.2)) or ['']
            cell_texts.append(wrapped)
            max_lines = max(max_lines, len(wrapped))
        row_height = 5.5 * max_lines
        y_start = self.get_y()
        x_start = self.get_x()
        for i, texts in enumerate(cell_texts):
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

    # ==================== COVER PAGE ====================
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 18, 'SEMI-FINALS', 0, 1, 'C')
    pdf.cell(0, 18, 'PRESENTATION GUIDE', 0, 1, 'C')
    pdf.ln(8)
    pdf.set_font('Helvetica', '', 18)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 12, 'EY Techathon - Retail [ABFRL]', 0, 1, 'C')
    pdf.cell(0, 12, 'AI-Driven Conversational Sales Agent', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 13)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 10, '30-Minute Presentation Flow', 0, 1, 'C')
    pdf.cell(0, 10, 'Complete Script + Demo Guide + Talking Points', 0, 1, 'C')
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, 'Legend:', 0, 1, 'C')
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(80, 50, 0)
    pdf.cell(0, 6, 'Yellow boxes = What to SAY (speaking script)', 0, 1, 'C')
    pdf.set_text_color(0, 70, 130)
    pdf.cell(0, 6, 'Blue boxes = What to DO (demo actions)', 0, 1, 'C')
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 6, 'Red text = Key points to emphasize', 0, 1, 'C')
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 6, 'Green boxes = Tips and notes', 0, 1, 'C')

    # ==================== TIMELINE OVERVIEW ====================
    pdf.add_page()
    pdf.chapter_title('30-Minute Presentation Timeline')

    widths = [30, 65, 50, 45]
    pdf.table_header(['Time', 'Section', 'Type', 'Duration'], widths)
    pdf.table_row(['0:00-2:00', 'Opening Hook & Team Intro',
                  'Speaking', '2 min'], widths)
    pdf.table_row(['2:00-5:00', 'Problem Statement & Market Context',
                  'Speaking + Slides', '3 min'], widths)
    pdf.table_row(['5:00-8:00', 'Solution Overview & Architecture',
                  'Speaking + Diagram', '3 min'], widths)
    pdf.table_row(['8:00-11:00', 'Agent Roles & How They Work',
                  'Speaking + Visual', '3 min'], widths)
    pdf.table_row(['11:00-22:00', 'LIVE DEMO (The Star of the Show)',
                  'Live Demo', '11 min'], widths)
    pdf.table_row(
        ['22:00-24:00', 'Technical Deep Dive Highlights', 'Speaking', '2 min'], widths)
    pdf.table_row(['24:00-26:00', 'Business Impact & Metrics',
                  'Speaking + Data', '2 min'], widths)
    pdf.table_row(['26:00-28:00', 'Edge Cases & Differentiators',
                  'Speaking', '2 min'], widths)
    pdf.table_row(['28:00-30:00', 'Closing & Future Roadmap',
                  'Speaking', '2 min'], widths)

    pdf.ln(5)
    pdf.tip_box(
        'The LIVE DEMO is 11 minutes - this is where you WIN or LOSE. Practice it 10+ times before the presentation.')

    pdf.section_title('Before You Start - Checklist')
    pdf.bullet('Backend server running (python main.py)')
    pdf.bullet('Frontend running (npm run dev)')
    pdf.bullet('Browser open with the app loaded')
    pdf.bullet('Test customer logged in (e.g., C001)')
    pdf.bullet('Cart cleared for clean demo')
    pdf.bullet('Internet stable (OpenAI API needs connectivity)')
    pdf.bullet('Backup: Screen recording of full demo flow in case of API failure')
    pdf.bullet('PPT slides open in presentation mode (5 slides)')

    # ==================== SECTION 1: OPENING ====================
    pdf.add_page()
    pdf.time_marker('0:00 - 2:00', 'OPENING HOOK & TEAM INTRODUCTION')

    pdf.section_title('The Hook (First 30 Seconds)')
    pdf.body('Start strong. Do NOT start with "Hi, we are team XYZ." Start with a PROBLEM that grabs attention.')

    pdf.speak_script(
        'Imagine this - you walk into an ABFRL store, try on a blazer, love it, but your size is not available. '
        'The sales associate says - check online. You go home, open the app, but now you cannot find that blazer. '
        'You give up. That sale is lost forever. This happens millions of times every year across retail. '
        'Today, we are going to show you how we solve this with an AI Sales Agent that never forgets, '
        'never loses context, and works across EVERY channel.'
    )

    pdf.ln(2)
    pdf.section_title('Team Introduction (30 seconds)')
    pdf.speak_script(
        'We are Team [YOUR TEAM NAME]. I am [Name], and with me are [Name, Name, Name]. '
        'We have built a fully functional AI-driven Conversational Sales Agent for ABFRL '
        'that operates across web chat, store kiosk, and WhatsApp - and we are going to demo it live today.'
    )

    pdf.tip_box(
        'Keep intro under 30 seconds. Judges care about the solution, not your bios. Be confident, make eye contact.')

    pdf.section_title('Set the Stage (30 seconds)')
    pdf.speak_script(
        'In the next 28 minutes, I will walk you through: '
        'First, the problem and why existing solutions fail. '
        'Second, our architecture - 12 specialized AI agents orchestrated by a master Sales Agent. '
        'Third, a LIVE demo showing a complete customer journey from browsing to purchase. '
        'And finally, the business impact this creates for ABFRL.'
    )

    pdf.key_point('Judges now know the roadmap. They can follow along.')

    # ==================== SECTION 2: PROBLEM STATEMENT ====================
    pdf.add_page()
    pdf.time_marker('2:00 - 5:00', 'PROBLEM STATEMENT & MARKET CONTEXT')

    pdf.section_title('Slide 1 of PPT: The Problem')
    pdf.speak_script(
        'Let me paint the picture of retail today. ABFRL operates across 3,800+ stores, '
        'multiple e-commerce platforms, and mobile apps. But the customer experience is FRAGMENTED. '
        'Let me highlight three critical pain points.'
    )

    pdf.sub_section('Pain Point 1: Channel Disconnection')
    pdf.speak_script(
        'When a customer browses on the mobile app, adds items to wishlist, and then walks into a store - '
        'the store associate has ZERO context. The customer starts from scratch. '
        'That is like calling customer support and explaining your problem again to every new agent.'
    )

    pdf.sub_section('Pain Point 2: Missed Revenue Opportunities')
    pdf.speak_script(
        'Sales associates in stores handle 15-20 customers at peak hours. They physically cannot '
        'do personalized recommendations, check inventory across locations, apply the right promotions, '
        'AND process payments - all while being consultative. '
        'Industry data shows 30-40 percent of up-sell and cross-sell opportunities are missed because of this bandwidth limitation.'
    )

    pdf.sub_section('Pain Point 3: Cart Abandonment')
    pdf.speak_script(
        'Online cart abandonment in Indian fashion retail is around 75 percent. '
        'Why? Complex checkout, no personalized guidance, and no one to answer - does this shirt come in blue? '
        'In a physical store, a good sales associate reduces abandonment to under 20 percent. '
        'We need that sales associate - available 24/7, on every channel.'
    )

    pdf.key_point(
        'Frame it as a REVENUE problem, not just a tech problem. Judges love business impact.')

    pdf.sub_section('The Opportunity')
    pdf.speak_script(
        'The goal from the problem statement is clear: Increase Average Order Value and conversion rates '
        'by offering a unified, human-like conversational journey. '
        'That is exactly what we have built.'
    )

    # ==================== SECTION 3: SOLUTION OVERVIEW ====================
    pdf.add_page()
    pdf.time_marker('5:00 - 8:00', 'SOLUTION OVERVIEW & ARCHITECTURE')

    pdf.section_title('Slide 2 of PPT: Architecture Diagram')

    pdf.speak_script(
        'Our solution is an Agentic AI system with a Master Sales Agent that orchestrates 12 specialized Worker Agents. '
        'Let me explain the architecture at a high level before we dive into the demo.'
    )

    pdf.sub_section('The Master Orchestrator')
    pdf.speak_script(
        'At the center is our Sales Agent - powered by GPT-4o-mini through LangGraph. '
        'Think of it as the brain. When a customer says something, the Sales Agent does NOT have '
        'hardcoded if-else logic. Instead, it UNDERSTANDS the intent, decides which worker agents to invoke, '
        'and chains them together automatically. '
        'For example, if a customer says - show me hoodies under 2000 - the Sales Agent automatically calls '
        'the Inventory Agent, filters by price, then calls the Recommendation Agent to format beautiful product cards. '
        'No rules engine. No decision trees. Pure AI orchestration.'
    )

    pdf.key_point(
        'Emphasize: "No hardcoded rules. The AI decides the flow dynamically."')

    pdf.sub_section('The 12 Worker Agents')
    pdf.speak_script(
        'We have 12 specialized agents, each responsible for one domain. '
        'Customer Info Agent for profiles and history. '
        'Inventory Agent for product search with multi-criteria filtering. '
        'Recommendation Agent for personalized product cards. '
        'Upsell Agent that automatically suggests accessories after cart view. '
        'Add to Cart, View Cart, Remove from Cart for cart management. '
        'Channel Selection Agent for online versus offline routing. '
        'Payment Agent with a two-phase flow for secure processing. '
        'Fulfillment Agent for delivery or store pickup. '
        'Loyalty Agent that awards points after purchase. '
        'And Post-Purchase Agent for tracking and feedback. '
        'Each agent has its own database operations, validation logic, and error handling.'
    )

    pdf.sub_section('The Reactive Loop')
    pdf.speak_script(
        'The magic is in the LangGraph StateGraph. It works as a loop: '
        'User message goes to the Agent Node - the LLM brain. '
        'The LLM decides which tools to call. '
        'The Tool Node executes those tools. '
        'Results go back to the Agent Node. '
        'The LLM either calls more tools or generates a final response. '
        'This means the agent can chain multiple operations in a single turn. '
        'For example: search products, format recommendations, AND suggest related items - all in one response.'
    )

    pdf.sub_section('Omnichannel Architecture')
    pdf.speak_script(
        'The same agent backend serves three channels: '
        'Web chat through REST API and WebSocket for real-time streaming. '
        'Store kiosk with a specialized linear flow graph. '
        'And WhatsApp integration via Meta webhooks. '
        'All channels share the same database, same agent logic, same customer context. '
        'A customer can start on WhatsApp, continue on web, and finish in-store - seamlessly.'
    )

    pdf.tip_box(
        'Point to the architecture diagram on your slide while explaining. Visual + verbal = better retention.')

    # ==================== SECTION 4: AGENT ROLES ====================
    pdf.add_page()
    pdf.time_marker('8:00 - 11:00', 'AGENT ROLES & HOW THEY WORK TOGETHER')

    pdf.section_title('Slide 3 of PPT: Agent Ecosystem')

    pdf.speak_script(
        'Before the demo, let me quickly map our agents to the problem statement requirements. '
        'This is important because every agent we built directly addresses a requirement from the brief.'
    )

    widths = [45, 50, 95]
    pdf.table_header(['Required Role', 'Our Agent(s)',
                     'How We Implemented It'], widths)
    pdf.table_row(['Recommendation Agent', 'inventory_agent + recommendation_agent',
                  'Multi-criteria search with price bands, gender, season, category + formatted product cards'], widths)
    pdf.table_row(['Inventory Agent', 'inventory_agent (store mode)',
                  'Real-time stock check across multiple stores with store_ids mapping'], widths)
    pdf.table_row(['Payment Agent', 'payment_agent (2-phase)',
                  'Phase 1: show options. Phase 2: process payment, deduct stock, create order history'], widths)
    pdf.table_row(['Fulfillment Agent', 'fulfillment_agent',
                  'Online delivery with address lookup OR offline store pickup with store selection'], widths)
    pdf.table_row(['Loyalty & Offers', 'loyalty_agent',
                  'Points calculation per product, balance updates, apply/unapply loyalty discount on cart'], widths)
    pdf.table_row(['Post-Purchase', 'post_purchase_agent',
                  'Order tracking, feedback collection, return/exchange policy (7 days)'], widths)

    pdf.ln(3)
    pdf.sub_section('Bonus Agents (Beyond Requirements)')
    pdf.speak_script(
        'We also built agents that go BEYOND what was asked: '
        'The Upsell Agent automatically suggests accessories like belts, watches, or shoes after viewing cart. '
        'This directly targets the AOV increase goal from the problem statement. '
        'The Channel Selection Agent handles the online-versus-offline routing, '
        'enabling the omnichannel experience the brief specifically asks for.'
    )

    pdf.key_point(
        'Show judges you EXCEEDED the requirements, not just met them.')

    pdf.sub_section('Tool Chaining Intelligence')
    pdf.speak_script(
        'The real innovation is how agents chain together. The LLM does not just call one tool. '
        'It chains them intelligently: '
        'Search products, then format recommendations. '
        'Process payment, then trigger fulfillment, then award loyalty, then show post-purchase options. '
        'All automatically. All in one conversational turn. '
        'This is the power of agentic AI versus traditional chatbots.'
    )

    # ==================== SECTION 5: LIVE DEMO ====================
    pdf.add_page()
    pdf.time_marker('11:00 - 22:00', 'LIVE DEMO (11 Minutes - THE MAIN EVENT)')

    pdf.section_title('Slide 4 of PPT: Live Demo Title Slide')

    pdf.body(
        'This is the most important section. You will demonstrate a COMPLETE customer journey '
        'from product discovery to post-purchase. Practice this section until you can do it in your sleep.'
    )

    pdf.tip_box(
        'Before starting demo, say: "Now let me show you everything I just described, working live. '
        'No slides, no mockups - this is a real system processing real AI agent calls in real-time."'
    )

    # Demo Part 1
    pdf.sub_section('Demo Part 1: Customer Login & Profile (1 min)')
    pdf.action_item('Open the app in browser. Login as customer C001.')

    pdf.speak_script(
        'Here is our retail app. I am logging in as Rahul, a Gold-tier customer with 1500 loyalty points. '
        'Notice the clean, modern interface. Let me first ask the agent about my profile.'
    )

    pdf.action_item('Type in chat: "Who am I?" or "Show my profile"')

    pdf.speak_script(
        'The agent immediately calls the Customer Info Agent, which queries the customer database '
        'and returns Rahul profile - name, email, loyalty tier, points balance, and address. '
        'Notice the timeline on the left showing which agent was called in real-time. '
        'This is powered by our WebSocket connection that streams agent activity live.'
    )

    pdf.key_point(
        'Point out the REAL-TIME TIMELINE. This shows agent orchestration visually.')

    # Demo Part 2
    pdf.ln(2)
    pdf.sub_section('Demo Part 2: Product Discovery & Recommendations (2 min)')
    pdf.action_item('Type: "Show me hoodies"')

    pdf.speak_script(
        'Now I ask for hoodies. Watch the timeline - the Inventory Agent activates first, '
        'searching our product catalog. It filters by category, checks availability, '
        'and excludes products Rahul has already purchased. '
        'Then the Recommendation Agent automatically formats these into beautiful product cards '
        'with images, prices, sizes, and Add to Cart buttons. '
        'This chaining - inventory then recommendation - happens automatically. The LLM decided this flow.'
    )

    pdf.action_item('Type: "Show me products between 1500 and 2500"')

    pdf.speak_script(
        'Now watch this - I am asking for products in a specific price range. '
        'Our system has a smart price-band parser that understands natural language like '
        'between 1500 and 2500, above 3000, or under 1000. '
        'It extracts the price range and filters accordingly. '
        'And here is something clever - our system has a fast-path optimization. '
        'For simple price queries, we bypass the LLM entirely and call the tools directly. '
        'This reduces latency significantly.'
    )

    pdf.key_point(
        'Mention the FAST-PATH OPTIMIZATION. Shows you thought about performance.')

    pdf.add_page()
    pdf.action_item('Type: "Show me more" (for the same category)')

    pdf.speak_script(
        'I say show me more - and notice, it shows DIFFERENT products. '
        'We maintain an in-memory deduplication system that tracks which products have been shown '
        'per customer per query. So show me more never repeats products. '
        'This mimics how a real sales associate would say - let me show you some other options.'
    )

    pdf.key_point(
        'Deduplication = "show more" feature. Simple but impressive to judges.')

    # Demo Part 3
    pdf.sub_section('Demo Part 3: Add to Cart & Smart Upselling (2 min)')
    pdf.action_item(
        'Click "Add to Cart" on a product, or type: "Add P045 quantity 2 size L"')

    pdf.speak_script(
        'I am adding this hoodie to cart - quantity 2, size Large. '
        'The Add to Cart Agent validates three things: '
        'First, does this product exist? '
        'Second, is the requested quantity available in stock? '
        'Third, is this item already in the cart? If yes, it increments the quantity instead of creating a duplicate. '
        'All of this happens with real database operations - stock validation, cart management, everything.'
    )

    pdf.action_item('Type: "Show my cart"')

    pdf.speak_script(
        'Now I view my cart. The View Cart Agent fetches all active items, calculates subtotals, '
        'shows the total, and displays my available loyalty points. '
        'But watch what happens AUTOMATICALLY after the cart is shown...'
    )

    pdf.speak_script(
        'The Upsell Agent kicks in! Without me asking, the agent suggests - '
        'Hey, how about checking out some belts or watches to go with your purchase? '
        'This is our autonomous upselling mechanism. It randomly selects from accessory categories '
        'and proactively suggests complementary products. '
        'This directly addresses the problem statement goal of increasing Average Order Value.'
    )

    pdf.key_point(
        'AUTONOMOUS UPSELLING is a huge differentiator. Emphasize it targets AOV increase.')

    # Demo Part 4
    pdf.add_page()
    pdf.sub_section('Demo Part 4: Loyalty Points Application (1 min)')
    pdf.action_item(
        'Show the cart page. Toggle the "Apply Loyalty Points" checkbox.')

    pdf.speak_script(
        'Rahul has 1500 loyalty points. I can apply them as a discount - '
        'one point equals one rupee. Watch the cart total update in real-time. '
        'And if I change my mind, I can unapply them - the points are restored to the customer balance. '
        'This is handled by dedicated API endpoints with proper database transactions.'
    )

    # Demo Part 5
    pdf.sub_section('Demo Part 5: ONLINE Purchase Flow (3 min)')
    pdf.action_item('Type: "Proceed to checkout" or "Buy now"')

    pdf.speak_script(
        'Now the Channel Selection Agent activates. It asks - would you like to buy online or offline? '
        'Let me show the ONLINE flow first.'
    )

    pdf.action_item('Type: "Online"')

    pdf.speak_script(
        'I choose online. Now the Payment Agent activates - but here is something important. '
        'We have a TWO-PHASE payment flow. '
        'Phase 1: The agent shows available payment methods - UPI, Credit Card, Debit Card, Net Banking. '
        'No payment is processed yet. The customer chooses their method.'
    )

    pdf.action_item('Type: "UPI"')

    pdf.speak_script(
        'Phase 2: Now the actual payment is processed. Watch what happens in the timeline - '
        'Payment Agent processes the payment. '
        'For each cart item, it deducts stock from the product inventory, '
        'creates an order history record, and marks the cart item as completed. '
        'Then AUTOMATICALLY, the Fulfillment Agent activates - it looks up the customer address '
        'and confirms delivery details with an estimated delivery date. '
        'Then the Loyalty Agent awards points based on the purchase. '
        'And finally, the Post-Purchase Agent provides tracking information, '
        'feedback links, and return policy details. '
        'Four agents chained together - payment, fulfillment, loyalty, post-purchase - '
        'all in a single conversational turn. This is agentic orchestration in action.'
    )

    pdf.key_point(
        '4-AGENT CHAIN in one turn: Payment -> Fulfillment -> Loyalty -> Post-Purchase. This is the WOW moment.')

    # Demo Part 6
    pdf.add_page()
    pdf.sub_section('Demo Part 6: OFFLINE Purchase Flow (2 min)')

    pdf.speak_script(
        'Now let me show the OFFLINE flow - this is where omnichannel comes alive.'
    )

    pdf.action_item(
        'Add a new product to cart. Type: "I want to buy this offline"')

    pdf.speak_script(
        'When the customer chooses offline, the system does something different. '
        'The Inventory Agent switches to STORE AVAILABILITY mode. '
        'It looks up which physical stores stock this product using the store_ids mapping. '
        'For each store, it shows the name, address, and distance from the customer. '
        'The customer selects a store, and the Fulfillment Agent creates an offline order - '
        'the product is reserved for in-store pickup. '
        'Notice - in offline mode, there is NO payment processing through our system '
        'because that happens at the physical POS. And no loyalty points are awarded online. '
        'The flow is deliberately different because the purchase channel is different. '
        'This is TRUE omnichannel - not just showing the same page on different devices.'
    )

    pdf.key_point(
        'Online vs Offline flows are GENUINELY DIFFERENT. Not just cosmetic. Show this clearly.')

    # Demo Part 7
    pdf.sub_section('Demo Part 7: Real-time Timeline (30 sec)')

    pdf.speak_script(
        'Throughout this demo, you have seen the real-time timeline showing which agents are working. '
        'This is powered by WebSocket streaming. As each tool starts, executes, and completes, '
        'the frontend receives live updates. The customer sees exactly what is happening - '
        'Searching inventory, Processing payment, Calculating loyalty points. '
        'This transparency builds trust. The customer knows the AI is actually DOING things, not just typing.'
    )

    # ==================== SECTION 6: TECHNICAL DEEP DIVE ====================
    pdf.add_page()
    pdf.time_marker('22:00 - 24:00', 'TECHNICAL DEEP DIVE HIGHLIGHTS')

    pdf.section_title('Key Technical Decisions to Highlight')

    pdf.speak_script(
        'Let me quickly highlight some key technical decisions that make this system robust.'
    )

    pdf.sub_section('1. Universal CRUD Pattern')
    pdf.speak_script(
        'Instead of writing separate database operations for each model, we built a Universal CRUD class '
        'that works with ANY SQLModel table. One class handles create, read, update, delete, filter, '
        'search, count, and exists for all 10 database tables. This reduced our codebase significantly '
        'and made it easy to add new models.'
    )

    pdf.sub_section('2. LangGraph StateGraph vs Simple Chains')
    pdf.speak_script(
        'We chose LangGraph over simple LangChain chains because we needed a REACTIVE loop. '
        'Simple chains are linear - A then B then C. Our agent needs to dynamically decide '
        'what to do next based on results. The StateGraph allows the LLM to call tools, '
        'see results, and decide whether to call more tools or respond. '
        'This is the difference between a scripted chatbot and an agentic system.'
    )

    pdf.sub_section('3. Two-Phase Payment for Safety')
    pdf.speak_script(
        'Our payment flow is deliberately two-phase. Phase 1 shows options without processing anything. '
        'Phase 2 processes the actual payment only after explicit user confirmation. '
        'This prevents accidental charges and gives the customer control. '
        'Each phase is a separate tool call - the LLM manages the state transition.'
    )

    pdf.sub_section('4. Stock Management with Atomic Operations')
    pdf.speak_script(
        'When a payment is processed, we do three atomic operations for each cart item: '
        'Deduct product stock, create order history, mark cart item completed. '
        'If any step fails, the transaction integrity is maintained. '
        'This is production-grade inventory management, not a prototype hack.'
    )

    pdf.sub_section('5. Separate Chat Database')
    pdf.speak_script(
        'We use two separate SQLite databases - one for business data like products, customers, and orders, '
        'and another for conversation history. This keeps the main database clean, '
        'allows independent scaling, and lets us clear chat history without affecting business data.'
    )

    pdf.tip_box(
        'Do NOT over-explain technical details. Judges want to see it WORKS, not hear a lecture. Keep this section fast.')

    # ==================== SECTION 7: BUSINESS IMPACT ====================
    pdf.add_page()
    pdf.time_marker('24:00 - 26:00', 'BUSINESS IMPACT & METRICS')

    pdf.section_title('Slide 5 of PPT: Impact & Metrics')

    pdf.speak_script(
        'Now let me talk about why this matters for ABFRL business.'
    )

    pdf.sub_section('Impact 1: Average Order Value (AOV) Increase')
    pdf.speak_script(
        'Our Upsell Agent automatically suggests complementary products after every cart view. '
        'In traditional retail, this depends on the sales associate remembering to suggest accessories. '
        'Our AI never forgets. Industry benchmarks show that effective cross-selling '
        'increases AOV by 10 to 30 percent. With our autonomous upselling, '
        'every single customer interaction includes a cross-sell opportunity.'
    )

    pdf.sub_section('Impact 2: Conversion Rate Improvement')
    pdf.speak_script(
        'Online cart abandonment is 75 percent in fashion retail. '
        'Our conversational agent reduces friction by: '
        'Answering product questions instantly. '
        'Showing real-time stock availability. '
        'Applying loyalty discounts seamlessly. '
        'Guiding through checkout step by step. '
        'Conservative estimates suggest a 15 to 25 percent reduction in cart abandonment.'
    )

    pdf.sub_section('Impact 3: Operational Efficiency')
    pdf.speak_script(
        'One AI agent can handle unlimited concurrent conversations. '
        'In a store, one associate handles 15-20 customers per day. '
        'Our kiosk agent can handle all walk-in customers simultaneously, '
        'freeing associates for high-touch interactions. '
        'This is not about replacing people - it is about augmenting their capacity.'
    )

    pdf.sub_section('Impact 4: Omnichannel Revenue Capture')
    pdf.speak_script(
        'Remember the blazer story from the beginning? With our system, '
        'the customer finds the blazer in-store, the agent remembers it, '
        'and when they go home, the web chat agent already knows what they were looking at. '
        'No lost context. No lost sale. This is true omnichannel - and it directly captures revenue '
        'that would otherwise be lost in channel transitions.'
    )

    pdf.key_point(
        'Always tie technical features back to BUSINESS VALUE. Judges are evaluating solutions, not code.')

    # ==================== SECTION 8: EDGE CASES ====================
    pdf.add_page()
    pdf.time_marker('26:00 - 28:00', 'EDGE CASES & DIFFERENTIATORS')

    pdf.section_title('Edge Cases We Handle')

    pdf.speak_script(
        'The problem statement specifically asks us to demonstrate edge case handling. '
        'Let me highlight the key ones.'
    )

    pdf.sub_section('Edge Case 1: Out of Stock')
    pdf.speak_script(
        'If a customer tries to add a product with insufficient stock, '
        'the Add to Cart Agent checks the product quantity in real-time '
        'and returns a clear message: Sorry, only 3 units available. '
        'It does not silently fail or add zero items.'
    )

    pdf.sub_section('Edge Case 2: Duplicate Cart Items')
    pdf.speak_script(
        'If a customer adds the same product twice, instead of creating duplicate entries, '
        'the agent detects the existing cart item and increments the quantity. '
        'This prevents cart confusion and ensures accurate totals.'
    )

    pdf.sub_section('Edge Case 3: Show More Products')
    pdf.speak_script(
        'When a customer says show me more, the system tracks which products '
        'have already been displayed using an in-memory deduplication mechanism. '
        'It never shows the same product twice in a session.'
    )

    pdf.sub_section('Edge Case 4: Already Purchased Products')
    pdf.speak_script(
        'The Inventory Agent checks the customer order history and excludes '
        'products they have already bought. We do not recommend the same shirt '
        'you purchased last month.'
    )

    pdf.sub_section('Edge Case 5: Loyalty Points Apply/Unapply')
    pdf.speak_script(
        'Customers can apply loyalty points as a discount, then change their mind and remove the discount. '
        'The points are correctly restored to their balance. '
        'This bidirectional flow is handled with proper database transactions.'
    )

    pdf.section_title('Key Differentiators vs Other Teams')

    pdf.bullet('12 specialized agents vs typical 3-4 generic tools')
    pdf.bullet(
        'Real-time WebSocket timeline showing agent activity (visual transparency)')
    pdf.bullet('Autonomous upselling (not prompted by user)')
    pdf.bullet(
        'Two genuinely different flows for online vs offline (not cosmetic difference)')
    pdf.bullet('Price-band fast-path optimization (bypasses LLM for performance)')
    pdf.bullet('Universal CRUD pattern (software engineering best practice)')
    pdf.bullet(
        'Dual database architecture (business data vs chat data separation)')
    pdf.bullet('WhatsApp + Web + Kiosk = true multi-channel (3 channels working)')

    pdf.key_point(
        'Know your differentiators. If a judge asks "What makes you different?", have this list ready.')

    # ==================== SECTION 9: CLOSING ====================
    pdf.add_page()
    pdf.time_marker('28:00 - 30:00', 'CLOSING & FUTURE ROADMAP')

    pdf.section_title('Summary Statement')
    pdf.speak_script(
        'To summarize - we have built a fully functional, multi-agent AI Sales Assistant '
        'that addresses every requirement in the problem statement: '
        'Multi-channel engagement across web, kiosk, and WhatsApp. '
        'Personalized recommendations based on customer history and preferences. '
        'End-to-end orchestration from discovery to post-purchase. '
        'Intelligent upselling to increase AOV. '
        'And genuine omnichannel continuity - not just responsive design, but shared context across channels.'
    )

    pdf.section_title('Future Roadmap (Optional but Impressive)')
    pdf.speak_script(
        'If we had more time, we would add: '
        'Voice assistant integration for hands-free in-store shopping. '
        'Visual search - take a photo and find similar products. '
        'Gift wrapping agent as mentioned in the modular architecture suggestion. '
        'A/B testing of recommendation strategies to continuously optimize AOV. '
        'And integration with actual ABFRL inventory APIs for production deployment.'
    )

    pdf.section_title('Closing Line')
    pdf.speak_script(
        'We did not just build a chatbot. We built a sales associate that never sleeps, '
        'never forgets a customer, works on every channel simultaneously, '
        'and gets smarter with every conversation. '
        'Thank you. We are happy to take questions.'
    )

    pdf.tip_box(
        'End with confidence. Do NOT say "that is all" or "I think that is it." End with a strong statement and "Thank you."')

    # ==================== Q&A PREPARATION ====================
    pdf.add_page()
    pdf.chapter_title('BONUS: Anticipated Judge Questions & Answers')

    pdf.body('Prepare for these questions. Judges WILL ask some of them.')

    qa_pairs = [
        (
            'Q: Why GPT-4o-mini instead of GPT-4 or an open-source model?',
            'A: GPT-4o-mini offers the best balance of intelligence, speed, and cost. It is fast enough for real-time conversations (sub-2-second responses), smart enough to handle complex tool chaining, and costs 90 percent less than GPT-4. For production, we could swap to any model - our architecture is model-agnostic.'
        ),
        (
            'Q: How do you handle hallucination?',
            'A: Our agents operate on STRUCTURED data from the database. The LLM does not generate product information - it queries real data through tools. The LLM only decides WHICH tool to call. Product names, prices, stock levels all come from our SQLite database. This eliminates hallucination for factual data.'
        ),
        (
            'Q: What happens if the API goes down?',
            'A: We have a backup screen recording of the full demo. For production, we would implement retry logic with exponential backoff, fallback to a simpler rule-based system, and queue failed requests for later processing.'
        ),
        (
            'Q: How does session continuity work across channels?',
            'A: All channels share the same customer database and chat history database. When a customer switches from WhatsApp to web, the system loads their conversation history and cart state from the shared database. The customer_id is the unifying key across all channels.'
        ),
        (
            'Q: Can this scale?',
            'A: Yes. FastAPI is asynchronous and can handle thousands of concurrent connections. Each agent call is independent and stateless. For production, we would move from SQLite to PostgreSQL, add Redis for session caching, and deploy on Kubernetes for horizontal scaling.'
        ),
        (
            'Q: How is this different from a regular chatbot?',
            'A: A chatbot follows predefined conversation flows. Our system uses an AI that DYNAMICALLY decides what to do. It can chain 4 tools in one turn, proactively upsell without being asked, and handle unexpected queries like price range filtering that were not explicitly programmed. The LLM is the orchestrator, not a script runner.'
        ),
        (
            'Q: What about data privacy?',
            'A: Customer data stays in our local SQLite database. Only the conversation text goes to OpenAI API. No PII like credit card numbers or addresses are sent to the LLM. For production, we would add encryption at rest and in transit, comply with DPDPA regulations, and offer data deletion on request.'
        ),
        (
            'Q: How do you measure success?',
            'A: Three metrics: AOV increase from upselling, conversion rate improvement from reduced cart abandonment, and customer satisfaction from post-purchase feedback. Our feedback table already collects this data for analysis.'
        ),
        (
            'Q: Why 12 agents? Isn\'t that too many?',
            'A: Each agent follows the Single Responsibility Principle. The Payment Agent ONLY handles payments. The Loyalty Agent ONLY handles points. This makes the system modular - we can update, replace, or add agents without affecting others. The problem statement mentions adding a Gift Wrapping Agent easily. With our architecture, that is literally adding one more @tool decorated function.'
        ),
        (
            'Q: How does the offline flow actually work in a real store?',
            'A: The customer interacts with our kiosk agent in-store. They browse products, add to cart, and select the store for pickup. The system reserves the items and the store staff is notified. Payment happens at the physical POS. This bridges the digital-physical gap without replacing existing store infrastructure.'
        ),
    ]

    for q, a in qa_pairs:
        pdf.sub_section(q)
        pdf.body(a)
        if pdf.get_y() > 260:
            pdf.add_page()

    # ==================== DEMO SCRIPT QUICK REFERENCE ====================
    pdf.add_page()
    pdf.chapter_title('QUICK REFERENCE: Demo Chat Script')
    pdf.body('Copy these exact messages during the demo for a smooth flow:')

    demo_steps = [
        ('Step 1', 'Who am I?', 'Shows customer profile - Agent: customer_info_agent'),
        ('Step 2', 'Show me hoodies',
         'Product search - Agents: inventory_agent -> recommendation_agent'),
        ('Step 3', 'Show me products between 1500 and 2500',
         'Price band filtering - Fast-path optimization'),
        ('Step 4', 'Show me more', 'Deduplication - shows new products only'),
        ('Step 5', 'Add [product_id] quantity 2 size L',
         'Cart management - Agent: add_to_cart_agent'),
        ('Step 6', 'Show my cart',
         'Cart view + AUTO upsell - Agents: view_cart + upsell'),
        ('Step 7', 'Proceed to checkout',
         'Channel selection - Agent: choose_channel_agent'),
        ('Step 8', 'Online', 'Starts online flow - Agent: payment_agent Phase 1'),
        ('Step 9', 'UPI', 'Payment processing - Agent: payment -> fulfillment -> loyalty -> post_purchase'),
        ('Step 10', '[Add new product, choose offline]',
         'Offline flow - Shows stores for pickup'),
    ]

    widths = [20, 65, 105]
    pdf.table_header(['Step', 'Type This', 'What Happens'], widths)
    for step, msg, desc in demo_steps:
        pdf.table_row([step, msg, desc], widths)

    pdf.ln(5)
    pdf.tip_box(
        'Practice the full demo script 10+ times. Know what to say while the system is processing. Dead silence = awkward.')

    # ==================== PRESENTATION TIPS ====================
    pdf.add_page()
    pdf.chapter_title('PRESENTATION TIPS')

    tips = [
        ('Speak with CONFIDENCE', 'You built this. You know it better than anyone. Do not say "basically" or "actually" or "I think." Say "We built. We designed. This does."'),
        ('Make EYE CONTACT', 'Look at the judges, not the screen. Glance at the demo, but talk to the people.'),
        ('PAUSE after key points',
         'After saying something impressive (like the 4-agent chain), pause for 2 seconds. Let it sink in.'),
        ('Use the PROBLEM-SOLUTION framework',
         'For every feature, first state the problem, then show the solution. "Customers abandon carts because checkout is complex. Our agent guides them step by step."'),
        ('Have a BACKUP PLAN', 'If the demo breaks: 1) Stay calm. 2) Switch to screen recording. 3) Say "Let me show you the recording while the system recovers." Never panic.'),
        ('Time MANAGEMENT', 'Keep a timer visible. If you are at 20 minutes and have not started the demo, skip ahead. The demo is more important than slides.'),
        ('Answer Questions CONCISELY', 'Do not ramble. Answer in 30 seconds max. If you do not know, say "Great question, we have not explored that yet, but our architecture supports it."'),
        ('Show ENTHUSIASM', 'If you are not excited about your project, why should the judges be? Show genuine energy.'),
        ('Divide ROLES', 'One person presents, one person drives the demo, one person watches time and handles Q&A. Do not have all 4 people talking.'),
        ('Practice TRANSITIONS', '"Now that you have seen the architecture, let me show you it working live." Smooth transitions show preparation.'),
    ]

    for title, desc in tips:
        pdf.sub_section(title)
        pdf.body(desc)

    # ==================== PPT SLIDE CONTENT ====================
    pdf.add_page()
    pdf.chapter_title('5-SLIDE PPT CONTENT GUIDE')

    pdf.section_title('Slide 1: Problem & Context')
    pdf.bullet('Title: "The Fragmented Retail Experience"')
    pdf.bullet(
        '3 pain points with icons: Channel Disconnection, Missed Revenue, Cart Abandonment')
    pdf.bullet('Key stat: "75% cart abandonment in fashion retail"')
    pdf.bullet('Key stat: "30-40% missed cross-sell opportunities"')

    pdf.section_title('Slide 2: Architecture')
    pdf.bullet('Title: "Agentic AI Architecture"')
    pdf.bullet('Center: Master Sales Agent (GPT-4o-mini + LangGraph)')
    pdf.bullet('Around it: 12 Worker Agents in a wheel/ecosystem diagram')
    pdf.bullet(
        'Bottom: 3 channels (Web Chat, Store Kiosk, WhatsApp) connecting to same backend')
    pdf.bullet('Tech stack badges: Python, FastAPI, LangGraph, React, SQLite')

    pdf.section_title('Slide 3: Agent Ecosystem')
    pdf.bullet('Title: "12 Specialized AI Agents"')
    pdf.bullet(
        'Table mapping: Problem Statement Role -> Our Agent -> Key Capability')
    pdf.bullet(
        'Highlight: "Autonomous Upselling" and "Two-Phase Payment" as innovations')

    pdf.section_title('Slide 4: Live Demo')
    pdf.bullet('Title: "Live Demo: End-to-End Customer Journey"')
    pdf.bullet(
        'Simple flow diagram: Discover -> Cart -> Checkout -> Pay -> Deliver -> Loyalty')
    pdf.bullet(
        'Note: "All operations hitting real database with real AI agent orchestration"')

    pdf.section_title('Slide 5: Impact & Roadmap')
    pdf.bullet('Title: "Business Impact & Future Vision"')
    pdf.bullet(
        '4 impact areas with projected metrics (AOV +15-30%, Abandonment -25%, etc.)')
    pdf.bullet(
        'Future roadmap: Voice, Visual Search, Gift Wrapping Agent, A/B Testing')
    pdf.bullet('Closing: "Not a chatbot. A Sales Associate that never sleeps."')

    # ==================== FINAL PAGE ====================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, 'YOU GOT THIS.', 0, 1, 'C')
    pdf.ln(8)
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, 'Practice the demo. Know your differentiators.', 0, 1, 'C')
    pdf.cell(0, 10, 'Speak with confidence. Show your passion.', 0, 1, 'C')
    pdf.cell(0, 10, 'You built something incredible - now show the world.', 0, 1, 'C')
    pdf.ln(15)
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, 'EY Techathon Retail Agent', 0, 1, 'C')
    pdf.cell(0, 8, 'Semi-Finals Presentation Guide', 0, 1, 'C')
    pdf.cell(
        0, 8, '12 Agents | 25+ Endpoints | 3 Channels | 1 Unified Experience', 0, 1, 'C')

    # Save
    output_path = 'Semi_Finals_Presentation_Guide.pdf'
    pdf.output(output_path)
    print(f"\n{'='*60}")
    print(f"  PDF Generated Successfully!")
    print(f"  File: {output_path}")
    print(f"  Pages: {pdf.page_no()}")
    print(f"{'='*60}")
    return output_path


if __name__ == "__main__":
    create_pdf()
