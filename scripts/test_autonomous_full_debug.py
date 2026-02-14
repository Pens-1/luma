import asyncio
import httpx
import json
import os
import subprocess

OLLAMA_URL = "http://localhost:11434/api/chat"
CHAT_MODEL = "qwen3-coder:30b"

SYSTEM_PROMPT = """
あなたはAI自律エンジニア「LUMA」です。
不備（タスクが見えない等）があれば、[ACTION:NOTION]で調査し、[ACTION:EVOLVE]で自らコードを修正してください。
"""

async def run_full_debug_cycle():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    user_input = "Notionのタスクが全部Unknownになってて見えないよ！原因を調べて、app/plugins/notion_query.py を修正して完璧に直して。"
    messages.append({"role": "user", "content": user_input})

    print(f"🚀 User: {user_input}")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        print("\n--- Step 1: AI Analysis ---")
        res1 = await client.post(OLLAMA_URL, json={"model": CHAT_MODEL, "messages": messages, "stream": False})
        ai_msg1 = res1.json()["message"]["content"]
        print(f"LUMA: {ai_msg1}")
        
        tool_output = "Tool Output [NOTION_LIST]: {\"tasks\": [{\"title\": \"Task1\", \"status\": \"Unknown\"}], \"note\": \"All statuses are Unknown due to a bug in property extraction.\"}"
        print("\n--- Step 2: Providing Buggy Output ---")
        messages.append({"role": "assistant", "content": ai_msg1})
        messages.append({"role": "user", "content": tool_output})
        
        print("\n--- Step 3: AI Decision (Evolution) ---")
        res2 = await client.post(OLLAMA_URL, json={"model": CHAT_MODEL, "messages": messages, "stream": False})
        ai_msg2 = res2.json()["message"]["content"]
        print(f"LUMA: {ai_msg2}")
        
        if "[ACTION:EVOLVE" in ai_msg2:
            print("\n✅ TEST PASSED: LUMA autonomously decided to evolve/fix the code!")
            
            print("\n--- Step 4: Actually Running Aider to Fix ---")
            instruction = "In app/plugins/notion_query.py, find the line with '# BUG' and restore the correct logic to extract status name from Notion properties. Remove the hardcoded 'Unknown'."
            cmd = f"docker exec luma-fastapi python3 -c \"import asyncio; from app.services.aider_evolver import run_aider_evolution; asyncio.run(run_aider_evolution('{instruction}', 'app/plugins/notion_query.py'))\""
            subprocess.run(cmd, shell=True)
            
            print("\n--- Step 5: Verification ---")
            verify_cmd = "docker exec luma-fastapi grep 'BUG' /app/app/plugins/notion_query.py"
            result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
            if "BUG" not in result.stdout:
                print("✅ FINAL SUCCESS: The bug has been eradicated by Aider!")
            else:
                print("❌ FINAL FAIL: The bug still exists.")
        else:
            print("\n❌ TEST FAILED: LUMA did not suggest evolution.")

if __name__ == "__main__":
    asyncio.run(run_full_debug_cycle())
