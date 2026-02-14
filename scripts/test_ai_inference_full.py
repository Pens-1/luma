import asyncio
import httpx
import sys
import os

OLLAMA_URL = "http://localhost:11434/api/chat"
CHAT_MODEL = "qwen3-coder:30b"

SYSTEM_PROMPT = """
あなたはAI自律エンジニア「LUMA」です。アクションタグ [ACTION:...] を使って自律的に動作します。
利用可能なアクション:
- [ACTION:WEATHER:日数のオフセット]
- [ACTION:NOTION_CREATE:タスク名:期限]
アクションが必要な場合は、タグのみを出力してください。
"""

async def test_ai_reasoning_chain():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    user_input = "明日の天気を調べて、雨なら『傘を持っていく』、晴れなら『洗濯物干す』というタスクをNotionに追加して"
    messages.append({"role": "user", "content": user_input})

    print(f"🚀 User Input: {user_input}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Turn 1
        print("\n--- Turn 1: AI Thinking ---")
        res1 = await client.post(OLLAMA_URL, json={"model": CHAT_MODEL, "messages": messages, "stream": False})
        ai_msg1 = res1.json()["message"]["content"]
        print(f"AI: {ai_msg1}")
        
        if "[ACTION:WEATHER:1]" not in ai_msg1:
            print("❌ FAIL: AI did not request weather forecast.")
            return

        # Turn 2
        weather_result = 'Tool Output [WEATHER]: {"date": "2026-02-15", "suggestion": "雨が降るので傘が必要です", "umbrella_needed": true}'
        print("\n--- Turn 2: Providing Tool Output (Rainy) ---")
        messages.append({"role": "assistant", "content": ai_msg1})
        messages.append({"role": "user", "content": weather_result})
        
        res2 = await client.post(OLLAMA_URL, json={"model": CHAT_MODEL, "messages": messages, "stream": False})
        ai_msg2 = res2.json()["message"]["content"]
        print(f"AI: {ai_msg2}")
        
        if "[ACTION:NOTION_CREATE:傘を持っていく" not in ai_msg2:
            print(f"❌ FAIL: Unexpected AI output: {ai_msg2}")
            return

        # Turn 3
        notion_result = "Tool Output [NOTION_CREATE]: Success. Created Task '傘を持っていく' at http://notion.so/page1"
        print("\n--- Turn 3: Providing Tool Output (Success) ---")
        messages.append({"role": "assistant", "content": ai_msg2})
        messages.append({"role": "user", "content": notion_result})
        
        res3 = await client.post(OLLAMA_URL, json={"model": CHAT_MODEL, "messages": messages, "stream": False})
        ai_msg3 = res3.json()["message"]["content"]
        print(f"AI: {ai_msg3}")
        
        if "登録" in ai_msg3 or "完了" in ai_msg3 or "傘" in ai_msg3:
            print("\n✅ SUCCESS: AI reasoning chain completed perfectly!")
        else:
            print("\n⚠️ PARTIAL: AI completed actions but response was unclear.")

if __name__ == "__main__":
    asyncio.run(test_ai_reasoning_chain())
