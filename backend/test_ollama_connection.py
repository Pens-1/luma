import httpx
import asyncio
import json

OLLAMA_URL = "http://luma-ollama:11434/api/chat"
CHAT_MODEL = "gemma3:12b"

async def test_chat():
    payload = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": "こんにちは"}],
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_ctx": 4096
        }
    }
    
    print(f"Sending request to {OLLAMA_URL}...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("Response Data:", json.dumps(data, ensure_ascii=False, indent=2))
                content = data.get("message", {}).get("content", "")
                print(f"Content: {content}")
            else:
                print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
