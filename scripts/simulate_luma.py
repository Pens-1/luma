
import asyncio
import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
CHAT_MODEL = "qwen3-coder:30b"

SYSTEM_PROMPT = """
あなたはAI自律エンジニア「LUMA（ルーマ）」です。
「〜ですね」「〜しましょうか？」といった丁寧で親しみやすい日本語で話してください。
アクションタグ [ACTION:...] を使って自律的に動作します。
"""

async def simulate_bot_response(user_input):
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        "stream": False
    }
    
    print(f"User: {user_input}")
    print("--- Thinking ---")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            reply = result.get("message", {}).get("content", "")
            print(f"LUMA: {reply}")
        else:
            print(f"Error: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(simulate_bot_response("今の天気のapiの実装状況教えて"))
