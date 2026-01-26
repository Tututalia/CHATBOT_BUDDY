# Quick Setup Guide for Testing the Intelligent Agent

## 1. Set OpenAI API Key

### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY='your-api-key-here'
```

### Linux/Mac:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## 2. Run the Interactive Test

```bash
python test_interactive_agent.py
```

## 3. Test the Graph Visualization

```bash
python visualize_agent_graph.py
```

Then open `agent_graph.html` in your browser to see the visual diagram!

## Example Conversation Flow

```
You: Hi! I'm looking for a winter hoodie
Agent: [Calls recommendation_agent] Here are some hoodies...

You: I want the Being Human Hoodie PRD001
Agent: [Calls inventory_agent] Great! It's available. Buy online or offline?

You: I'll buy it online
Agent: [Calls payment_agent] Payment successful! 
      [Calls fulfillment_agent] Delivery in 3-5 days
      [Calls loyalty_agent] You earned 150 points!
      [Calls post_purchase_agent] Feedback link...
```

## Features

✅ LLM intelligently decides which tools to call
✅ Non-linear conversation flow
✅ Real OpenAI GPT-4 mini integration
✅ 6 agent tools available
✅ Interactive chat mode
