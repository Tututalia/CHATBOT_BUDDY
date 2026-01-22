"""
Simple test script to verify Google Gemini 2.5 Flash model is working
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("GOOGLE_API_KEY")


def test_gemini():
    """Test Gemini 2.5 Flash model with a simple prompt"""
    try:
        # Initialize the Gemini 2.5 Flash model
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Gemini 2.5 Flash model
            google_api_key=API_KEY,
            temperature=0.7,
        )

        print("🔄 Testing Gemini 2.5 Flash model...")
        print("-" * 50)

        # Send a simple test prompt
        prompt = "Hello! Can you respond with a short greeting and confirm you are Gemini 2.5 Flash?"

        print(f"\n📤 Prompt: {prompt}\n")

        # Get response
        response = llm.invoke(prompt)

        print(f"📥 Response: {response.content}\n")
        print("-" * 50)
        print("✅ Success! Your Gemini LLM is working correctly.")

        return True

    except Exception as e:
        print(f"❌ Error testing LLM: {str(e)}")
        print("\n💡 Make sure:")
        print("1. Your API key is correct")
        print("2. You have internet connection")
        print("3. The langchain-google-genai package is installed")
        return False


if __name__ == "__main__":
    # Check if API key is set
    if not API_KEY:
        print("⚠️  Please set your GOOGLE_API_KEY in .env file!")
        exit(1)

    test_gemini()
