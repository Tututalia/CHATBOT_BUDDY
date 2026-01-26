"""
Test the chat API endpoint directly
"""
import requests
import json


def test_chat_endpoint():
    """Test the /api/chat endpoint"""

    url = "http://localhost:8000/api/chat"

    payload = {
        "customer_id": "CUST001",
        "message": "Show me some hoodies",
        "conversation_history": []
    }

    print("Testing Chat API Endpoint")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)

    try:
        response = requests.post(url, json=payload, timeout=30)

        print(f"\nStatus Code: {response.status_code}")
        print("=" * 60)

        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2))
            print("=" * 60)
            print("\n✅ API endpoint is working!")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend!")
        print("Make sure the backend server is running:")
        print("  python -m uvicorn main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    test_chat_endpoint()
