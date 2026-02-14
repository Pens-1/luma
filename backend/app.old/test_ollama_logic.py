import asyncio
import httpx
import json

async def test_ollama_generation():
    url = "http://luma-ollama:11434/api/generate"
    # 改行をエスケープして1行で記述
    prompt = "今日は 2026-02-13 です。\nあなたはAI秘書のLUMAです。挨拶してください。\nユーザー: こんにちは"
    payload = {
        "model": "qwen3:30b",
        "prompt": prompt,
        "stream": False
    }
    
    print(f"🚀 Testing Ollama generation with model: {payload['model']}...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response: {result.get('response')}")
            else:
                print(f"⚠️ Failed with status {response.status_code}. Trying 14b fallback...")
                payload["model"] = "qwen3:14b"
                response = await client.post(url, json=payload)
                print(f"✅ Fallback Success! Response: {response.json().get('response')}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_generation())
