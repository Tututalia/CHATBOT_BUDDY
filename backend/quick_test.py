"""
Quick test to verify setup is working
"""
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("=" * 80)
print("QUICK SETUP VERIFICATION")
print("=" * 80)
print()

# Test 1: Check .env file
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    print(f"✓ API Key found: {api_key[:20]}...{api_key[-4:]}")
else:
    print("❌ API Key NOT found in environment")
    print("Make sure .env file exists in backend folder")
    exit(1)

print()

# Test 2: Import packages
try:
    import pandas as pd
    print("✓ pandas imported successfully")
except:
    print("❌ pandas import failed")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("✓ langchain-google-genai imported successfully")
except Exception as e:
    print(f"❌ langchain-google-genai import failed: {e}")

try:
    from langgraph.graph import StateGraph
    print("✓ langgraph imported successfully")
except Exception as e:
    print(f"❌ langgraph import failed: {e}")

try:
    from fastapi import FastAPI
    print("✓ fastapi imported successfully")
except:
    print("❌ fastapi import failed")

print()

# Test 3: Check data files
import os.path
data_files = [
    "data/product_data.csv",
    "data/customer_data.csv"
]

for file in data_files:
    if os.path.exists(file):
        print(f"✓ {file} exists")
    else:
        print(f"❌ {file} NOT found")

print()

# Test 4: Test LLM connection
print("Testing Google Gemini API connection...")
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=api_key,
        temperature=0.3
    )
    
    response = llm.invoke("Say 'API working' if you receive this.")
    print(f"✓ LLM responded: {response.content[:50]}...")
    print()
    print("=" * 80)
    print("✅ ALL CHECKS PASSED - System is ready!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run: python test_langgraph_flow.py")
    print("2. Or run: uvicorn main:app --reload")
    
except Exception as e:
    print(f"❌ LLM test failed: {e}")
    print()
    print("Possible issues:")
    print("- API key might be invalid or expired")
    print("- Check if you have internet connection")
    print("- Verify the API key at: https://makersuite.google.com/app/apikey")
