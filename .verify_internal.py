import asyncio
import httpx
import os
import json
from datetime import datetime

# Mimic the real config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")
TOOLS_API_URL = "http://luma-fast-service:8000"

BASE_SYSTEM_PROMPT = f"""
あなたはAI自律エンジニア「LUMA（ルーマ）」です。
現在日時: {datetime.now().strftime("%Y年%m月%d日 (%A) %H:%M")}

【役割】
ユーザーの良きパートナーとして、タスク管理と開発サポートを行います。
丁寧で親しみやすい日本語で話してください。

【重要：ツール利用について】
あなたは「weather（天気取得）」や「aider_fix（コード修正）」などの強力なツールを持っています。
ユーザーから天気や実装の依頼があった場合は、**必ず** これらのツールを使用してください。
「できません」と答える前に、利用可能なツールを確認してください。

【ツール利用の判断】
- ユーザーが明確に指示した場合や、情報が必要な場合にツールを使用してください。
- 挨拶、質問、機能の説明、雑談の場合はツールを使用せず会話してください。
- Notionやタスク管理に関する質問には「現在、タスク管理機能は無効化されています」と答えること。
"""

async def fetch_tools():
    print("🔄 Fetching tools from API...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{TOOLS_API_URL}/tools")
            if resp.status_code == 200:
                tools_list = resp.json()
                print(f"✅ Loaded {len(tools_list)} tools: {[t['name'] for t in tools_list]}")
                
                # Convert to Ollama format
                new_tools = []
                for tool in tools_list:
                    props = {}
                    required = []
                    for p_name, p_desc in tool.get('parameters', {}).items():
                        p_type = "string"
                        if "int" in p_desc.lower():
                            p_type = "integer"
                        props[p_name] = {"type": p_type, "description": p_desc}
                        required.append(p_name)

                    new_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool['name'],
                            "description": tool['description'],
                            "parameters": {
                                "type": "object",
                                "properties": props,
                                "required": required
                            }
                        }
                    })
                
                # Add Aider (Manual)
                new_tools.append({
                    "type": "function",
                    "function": {
                        "name": "aider_fix",
                        "description": "コードの修正や機能追加を行う。",
                        "parameters": {
                            "type": "object",
                            "properties": {"instruction": {"type": "string", "description": "指示内容"}},
                            "required": ["instruction"]
                        }
                    }
                })
                return new_tools
            else:
                print(f"❌ Failed to fetch tools: {resp.status_code}")
                return []
    except Exception as e:
        print(f"❌ Error fetching tools: {e}")
        return []

async def test_ollama_call(tools, prompt):
    print(f"\n🧠 Testing Ollama with prompt: '{prompt}'")
    messages = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.0}, # Low temp for consistency
        "tools": tools
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            if resp.status_code != 200:
                print(f"❌ Ollama error: {resp.text}")
                return None
            
            data = resp.json()
            msg = data.get("message", {})
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])
            
            print(f"📝 Response content: {content}")
            print(f"⚙️ Tool calls: {tool_calls}")
            
            if tool_calls:
                return tool_calls
            elif "ACTION:" in content:
                print("⚠️ Regex-style action detected (should use native tools!)")
                return None
            else:
                print("⚠️ No tool calls generated.")
                return None
                
    except Exception as e:
        print(f"❌ Error calling Ollama: {e}")
        return None

async def run_verify():
    print("🚀 Starting Internal Verification...")
    
    # 1. Fetch Tools
    tools = await fetch_tools()
    if not tools:
        print("❌ Tools fetching failed. Stopping.")
        return

    # 2. Test Weather Request
    print("\n--- Test Case 1: Weather Request ---")
    tool_calls = await test_ollama_call(tools, "今日の京都の天気は？")
    if tool_calls and tool_calls[0]["function"]["name"] in ["weather", "forecast"]:
        print("✅ Weather tool call generated successfully!")
    else:
        print("❌ Weather tool call FAILED.")

    # 3. Test Aider Request
    print("\n--- Test Case 2: Aider Request ---")
    tool_calls = await test_ollama_call(tools, "Aider、weatherツールに湿度の項目を追加して")
    if tool_calls and tool_calls[0]["function"]["name"] == "aider_fix":
         print("✅ Aider tool call generated successfully!")
    else:
         print("❌ Aider tool call FAILED.")

if __name__ == "__main__":
    asyncio.run(run_verify())
