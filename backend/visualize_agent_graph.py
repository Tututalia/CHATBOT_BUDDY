"""
Generate Visual Graph Diagram for Intelligent Agent System
Creates a Mermaid diagram and HTML visualization
"""


def generate_mermaid_diagram():
    """Generate and display Mermaid diagram of the graph"""

    print("\n" + "="*70)
    print(" "*15 + "🎨 GENERATING VISUAL GRAPH DIAGRAM")
    print("="*70 + "\n")

    # Create Mermaid diagram manually
    mermaid_code = """%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#4CAF50','primaryTextColor':'#fff','primaryBorderColor':'#2E7D32','lineColor':'#1976D2','secondaryColor':'#2196F3','tertiaryColor':'#FFC107'}}}%%
graph TD
    START([🚀 START]):::startNode
    AGENT[🤖 AGENT NODE<br/>LLM Decision Engine<br/>OpenAI GPT-4 mini]:::agentNode
    TOOLS[🛠️ TOOLS NODE<br/>Execute Agent Tools]:::toolsNode
    END([✅ END]):::endNode
    
    START --> AGENT
    AGENT -->|Needs Tools| TOOLS
    AGENT -->|Complete| END
    TOOLS -->|Return Results| AGENT
    
    subgraph "Available Agent Tools"
        T1[📦 recommendation_agent]:::toolBox
        T2[📊 inventory_agent]:::toolBox
        T3[💳 payment_agent]:::toolBox
        T4[🚚 fulfillment_agent]:::toolBox
        T5[🎁 loyalty_agent]:::toolBox
        T6[📝 post_purchase_agent]:::toolBox
    end
    
    TOOLS -.-> T1
    TOOLS -.-> T2
    TOOLS -.-> T3
    TOOLS -.-> T4
    TOOLS -.-> T5
    TOOLS -.-> T6
    
    classDef startNode fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    classDef agentNode fill:#2196F3,stroke:#1565C0,stroke-width:3px,color:#fff
    classDef toolsNode fill:#FF9800,stroke:#E65100,stroke-width:3px,color:#fff
    classDef endNode fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px,color:#fff
    classDef toolBox fill:#FFF9C4,stroke:#F57F17,stroke-width:2px,color:#333
"""

    print("✅ Mermaid Diagram Generated!\n")
    print("="*70)
    print("MERMAID DIAGRAM CODE:")
    print("="*70)
    print(mermaid_code)
    print("="*70)

    # Save to file
    with open("agent_graph.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    print("\n✅ Saved to: agent_graph.mmd")

    # Create HTML file for viewing
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Intelligent Agent Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        h3 {{
            text-align: center;
            color: #666;
            font-weight: normal;
            margin-bottom: 30px;
        }}
        .mermaid {{
            background-color: #fafafa;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .info-box {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .tool-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .tool-card {{
            background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #F57F17;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .tool-card h4 {{
            margin: 0 0 10px 0;
            color: #E65100;
        }}
        .tool-card p {{
            margin: 5px 0;
            font-size: 0.9em;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Intelligent Sales Agent Graph</h1>
        <h3>LangGraph StateGraph with OpenAI GPT-4 mini</h3>
        
        <div class="info-box">
            <strong>💡 How it works:</strong> The LLM intelligently decides which agent tools to call based on user queries. 
            Tools are invoked dynamically - not in a fixed sequence!
        </div>
        
        <div class="mermaid">
{mermaid_code}
        </div>
        
        <h2 style="margin-top: 40px; color: #333;">🛠️ Available Agent Tools</h2>
        
        <div class="tool-list">
            <div class="tool-card">
                <h4>📦 recommendation_agent</h4>
                <p><strong>Purpose:</strong> Shows product recommendations</p>
                <p><strong>Triggered:</strong> User wants to browse products</p>
            </div>
            
            <div class="tool-card">
                <h4>📊 inventory_agent</h4>
                <p><strong>Purpose:</strong> Checks product availability</p>
                <p><strong>Triggered:</strong> User selects a product</p>
            </div>
            
            <div class="tool-card">
                <h4>💳 payment_agent</h4>
                <p><strong>Purpose:</strong> Processes online payment</p>
                <p><strong>Triggered:</strong> User chooses online purchase</p>
            </div>
            
            <div class="tool-card">
                <h4>🚚 fulfillment_agent</h4>
                <p><strong>Purpose:</strong> Handles order fulfillment</p>
                <p><strong>Triggered:</strong> After payment or offline selection</p>
            </div>
            
            <div class="tool-card">
                <h4>🎁 loyalty_agent</h4>
                <p><strong>Purpose:</strong> Awards loyalty points & coupons</p>
                <p><strong>Triggered:</strong> After order fulfillment</p>
            </div>
            
            <div class="tool-card">
                <h4>📝 post_purchase_agent</h4>
                <p><strong>Purpose:</strong> Sends feedback & support info</p>
                <p><strong>Triggered:</strong> Final step after loyalty</p>
            </div>
        </div>
        
        <div class="info-box" style="background-color: #f3e5f5; border-left-color: #9C27B0; margin-top: 30px;">
            <strong>⚡ Key Features:</strong>
            <ul style="margin: 10px 0;">
                <li>Non-linear flow - LLM decides tool calls dynamically</li>
                <li>Context-aware - Remembers entire conversation</li>
                <li>Intelligent routing - Tools called only when needed</li>
                <li>Natural conversation - Feels human-like, not scripted</li>
            </ul>
        </div>
    </div>
    
    <script>
        mermaid.initialize({{ 
            startOnLoad: true, 
            theme: 'base',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>"""

    with open("agent_graph.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Saved HTML visualization to: agent_graph.html")
    print("\n📖 To view the graph:")
    print("   1. Open 'agent_graph.html' in your browser")
    print("   2. Or copy the Mermaid code above to https://mermaid.live/")
    print("\n🌐 Opening in browser...")

    # Try to open in browser
    import webbrowser
    import os
    try:
        file_path = os.path.abspath("agent_graph.html")
        webbrowser.open(f'file://{file_path}')
        print(f"✅ Opened in browser: {file_path}")
    except:
        print("⚠️  Could not auto-open browser. Please open agent_graph.html manually.")

    # Also show text representation
    print("\n" + "="*70)
    print("TEXT REPRESENTATION:")
    print("="*70)
    create_text_graph()


def create_text_graph():
    """Create a detailed text-based graph representation"""

    graph_ascii = """
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                    INTELLIGENT AGENT GRAPH                        ║
    ║                   (LangGraph StateGraph)                          ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    
                            ┌──────────────┐
                            │    START     │
                            │   (Entry)    │
                            └──────┬───────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       AGENT NODE             │
                    │  ┌────────────────────────┐  │
                    │  │  LLM Decision Engine   │  │
                    │  │  (OpenAI GPT-4 mini)   │  │
                    │  └────────────────────────┘  │
                    │                              │
                    │  • Analyzes user query       │
                    │  • Reviews conversation      │
                    │  • Decides tool calls        │
                    └─────┬──────────────────┬─────┘
                          │                  │
                 (needs tools)          (complete)
                          │                  │
                          ▼                  ▼
           ┌──────────────────────┐    ┌─────────┐
           │    TOOLS NODE        │    │   END   │
           │                      │    │ (Exit)  │
           │  ┌────────────────┐  │    └─────────┘
           │  │ Tool Executor  │  │
           │  └────────────────┘  │
           │                      │
           │  Available Tools:    │
           │  • recommendation    │
           │  • inventory         │
           │  • payment           │
           │  • fulfillment       │
           │  • loyalty           │
           │  • post_purchase     │
           └──────────┬───────────┘
                      │
                      │ (return results)
                      │
                      └──────┐
                             │
                             ▼
                    (Loop back to AGENT)
    
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                        GRAPH CHARACTERISTICS                      ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    🔄 FLOW TYPE: Conditional Loop
       → Agent can call tools multiple times
       → Flow continues until conversation ends
    
    🧠 DECISION MAKER: LLM (GPT-4 mini)
       → Analyzes context at each step
       → Chooses which tools to invoke
    
    ⚡ EXECUTION: Asynchronous
       → Non-blocking operations
       → Efficient processing
    
    📊 STATE MANAGEMENT: Centralized
       → Messages history
       → Customer data
       → Order information
       → Transaction state
    
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                         TOOL INVOCATION FLOW                      ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    Example: "I want to buy a hoodie online"
    
    Step 1: START → AGENT
            ↓
            LLM analyzes: "user wants product recommendations"
            ↓
    Step 2: AGENT → TOOLS (recommendation_agent)
            ↓
            Tool returns product list
            ↓
    Step 3: TOOLS → AGENT
            ↓
            LLM processes results, responds to user
            ↓
    Step 4: User selects product
            ↓
    Step 5: AGENT → TOOLS (inventory_agent)
            ↓
            Tool checks stock & shows options
            ↓
    Step 6: TOOLS → AGENT
            ↓
            LLM presents options
            ↓
    Step 7: User chooses "online"
            ↓
    Step 8: AGENT → TOOLS (payment_agent)
            ↓
            Tool processes payment
            ↓
    Step 9: TOOLS → AGENT → TOOLS (fulfillment_agent)
            ↓
            Tool confirms delivery
            ↓
    Step 10: TOOLS → AGENT → TOOLS (loyalty_agent)
            ↓
            Tool awards points
            ↓
    Step 11: TOOLS → AGENT → TOOLS (post_purchase_agent)
            ↓
            Tool sends feedback link
            ↓
    Step 12: TOOLS → AGENT
            ↓
            LLM concludes conversation
            ↓
            AGENT → END
    
    """

    print(graph_ascii)
    print("\n" + "="*70)
    print("✅ Text-based graph representation displayed above")
    print("="*70 + "\n")


if __name__ == "__main__":
    generate_mermaid_diagram()
