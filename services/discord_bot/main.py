"""
Discord Bot Service - The "Brain"
Ollamaと直接会話・思考し、Tools API (luma-fast-service) を呼び出して実行する
"""
import discord
import os
import re
import json
import httpx
from datetime import datetime

# 設定
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")
TOOLS_API_URL = "http://luma-fast-service:8000"
AIDER_API_URL = os.getenv("AIDER_API_URL", "http://luma-aider-service:8003")

# ベースとなるシステムプロンプト
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

# 現在のシステムプロンプト
current_system_prompt = BASE_SYSTEM_PROMPT

# ツール定義 (Ollama形式)
ollama_tools = []

# 会話履歴管理
# channel_id -> List[dict]
conversation_history = {}
MAX_HISTORY_LENGTH = 10  # 保持するメッセージ数 (往復)

# Discord Client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def fetch_tools():
    """Tools APIからツール一覧を取得し、Ollama形式に変換する"""
    global ollama_tools
    print("🔄 Fetching tools from API...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            resp = await http_client.get(f"{TOOLS_API_URL}/tools")
            
            if resp.status_code == 200:
                tools_list = resp.json()
                print(f"✅ Loaded {len(tools_list)} tools from API")
                
                new_tools = []
                for tool in tools_list:
                    # APIのレスポンス形式をOllamaのJSON Schema形式に変換
                    # api_tool: {name, description, parameters: {key: type_desc}}
                    
                    props = {}
                    required = []
                    
                    # パラメータ記述のパース (簡易実装)
                    # "day_index": "int (0=Today)" -> type: integer, description: ...
                    for p_name, p_desc in tool.get('parameters', {}).items():
                        p_type = "string"
                        if "int" in p_desc.lower():
                            p_type = "integer"
                        
                        props[p_name] = {
                            "type": p_type,
                            "description": p_desc
                        }
                        required.append(p_name)

                    tool_def = {
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
                    }
                    new_tools.append(tool_def)

                # Aider tool (Manual addition)
                new_tools.append({
                    "type": "function",
                    "function": {
                        "name": "aider_fix",
                        "description": "コードの修正や機能追加を行う。具体的な指示を与えること。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "instruction": {
                                    "type": "string",
                                    "description": "修正内容の具体的な指示 (例: 'weatherツールに湿度を追加して')"
                                }
                            },
                            "required": ["instruction"]
                        }
                    }
                })
                
                ollama_tools = new_tools
                print(f"📝 Converted to {len(ollama_tools)} Ollama tools.")
                
            else:
                print(f"⚠️ Failed to fetch tools: Status {resp.status_code}")
                
    except Exception as e:
        print(f"❌ Error fetching tools: {e}")


@client.event
async def on_ready():
    print(f"✅ Discord Bot Ready: {client.user}")
    print(f"🧠 Connected to Ollama at {OLLAMA_URL}")
    print(f"🔧 Connected to Tools API at {TOOLS_API_URL}")
    
    # 起動時にツールを取得
    await fetch_tools()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()
    if not content:
        return

    print(f"📨 Received: {content}")
    
    try:
        await message.add_reaction("👀")
    except Exception as e:
        pass

    try:
        # ツールが未ロードなら強制ロード (Debug)
        if not ollama_tools:
           print("⚠️ Tools not loaded yet. Forcing fetch...")
           await fetch_tools()

        # 会話履歴の取得 (なければ初期化)
        if message.channel.id not in conversation_history:
            conversation_history[message.channel.id] = []
        
        # 履歴のコピーを作成して、今回のセッション用メッセージを構築
        history = conversation_history.get(message.channel.id, [])
        
        # メッセージ構築: System + History + Current User
        messages = [{"role": "system", "content": current_system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": content})
        
        MAX_TURNS = 5
        turn_count = 0
        
        async with message.channel.typing():
            while turn_count < MAX_TURNS:
                turn_count += 1
                
                # 1. Ollama で思考 (Toolsあり)
                response_data = await chat_with_ollama(messages, tools=ollama_tools)
                
                response_msg = response_data.get("message", {})
                response_content = response_msg.get("content", "")
                tool_calls = response_msg.get("tool_calls", [])
                
                # 今回のやり取りログに追加
                messages.append(response_msg)
                
                # ツール呼び出しがあるか？
                if tool_calls:
                    print(f"⚙️ Tool Calls detected: {len(tool_calls)}")
                    
                    for tool_call in tool_calls:
                        function_name = tool_call['function']['name']
                        arguments = tool_call['function']['arguments']
                        
                        # 実行して結果を取得
                        tool_result_str = await execute_tool_call(function_name, arguments, message)
                        
                        # 結果を履歴に追加 (Role: tool)
                        messages.append({
                            "role": "tool",
                            "content": tool_result_str,
                        })
                    
                    # ループ継続 (結果を受けてBotが再思考)
                    continue
                
                else:
                    # ツール呼び出しがなければ、それが最終回答
                    if response_content:
                        await message.channel.send(response_content)
                        await message.add_reaction("✅")
                        
                        # --- 履歴の更新 (Commit to History) ---
                        # 今回のターンで増えたメッセージを履歴に保存する
                        
                        # [重要] Native Tool Callingの場合、
                        # User -> Assistant(ToolCalls) -> Tool(Result) -> Assistant(Final)
                        # という流れを全て保持しないと、次回リクエスト時にコンテキスト不整合(「ツール結果があるのに呼び出し元がない」等)でエラーになる可能性がある
                        
                        # 1. User発言を履歴に追加
                        conversation_history[message.channel.id].append({"role": "user", "content": content})
                        
                        # 2. 以降のやり取り (SystemとHistoryより後ろの部分) を追加
                        # messages = [System, ...History..., User, Bot, Tool, Bot...]
                        # System(1) + OldHistory(len) + User(1)
                        start_index = len(history) + 2
                        new_interactions = messages[start_index:]
                        
                        conversation_history[message.channel.id].extend(new_interactions)
                        
                        # 履歴制限
                        if len(conversation_history[message.channel.id]) > MAX_HISTORY_LENGTH * 2:
                             conversation_history[message.channel.id] = conversation_history[message.channel.id][-(MAX_HISTORY_LENGTH * 2):]
                        
                    else:
                        print("⚠️ Empty response without tool calls.")
                    
                    break
            
            if turn_count >= MAX_TURNS:
                await message.channel.send("思考がループしてしまったため中断しました。")
                await message.add_reaction("😵")

    except Exception as e:
        print(f"❌ Error: {e}")
        await message.channel.send(f"❌ エラー: {str(e)}")
        await message.add_reaction("❌")


async def chat_with_ollama(messages: list, tools: list = None) -> dict:
    """Ollama APIを呼び出す (Tools対応)"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        if tools:
            payload["tools"] = tools
        
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        resp.raise_for_status()
        
        return resp.json()


async def execute_tool_call(name: str, args: dict, message) -> str:
    """ツールを実行し、結果を文字列で返す"""
    print(f"🔧 Executing Tool: {name} args={args}")
    
    try:
        if name == "aider_fix":
            await message.add_reaction("🛠️")
            instruction = args.get("instruction", "")
            await message.channel.send(f"🛠️ Aiderに依頼しました: 「{instruction}」")
            
            result_log = await call_aider_api(instruction)
            return f"Aider Result:\n{result_log[-1000:]}" # Limit log size
            
        else:
            # 汎用的なツール実行 (Weather, Forecast, および新規追加ツール)
            print(f"🔧 Generic Tool Execution: {name}")
            await message.add_reaction("🔧")
            
            # 引数の型変換 (簡易的)
            # day_indexなど数値が必要な場合があるが、
            # call_tool_apiはそのままJSONで投げるので、受け手(FastAPI)側でPydanticがよしなにしてくれるはず
            # ただし、day_indexが文字列で来るとFastAPIがバリデーションエラーになる可能性もあるのでケアする
            if name == "weather" and "day_index" in args:
                if isinstance(args["day_index"], str) and args["day_index"].isdigit():
                    args["day_index"] = int(args["day_index"])
            
            result = await call_tool_api(name, args)
            return json.dumps(result, ensure_ascii=False)


    except Exception as e:
        return f"Error executing tool {name}: {str(e)}"


async def call_tool_api(tool_name: str, params: dict) -> dict:
    """Tools API (luma-fast-service) を呼び出す"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{TOOLS_API_URL}/tools/{tool_name}",
                json={"parameters": params}
            )
            resp.raise_for_status()
            return resp.json().get("result", {})
    except Exception as e:
        return {"error": str(e)}


async def call_aider_api(instruction: str) -> str:
    """Aider Serviceを呼び出す"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Make Aider aware of the guide and FORCE file locations
            prefix = (
                "IMPORTANT RULES:\n"
                "1. If creating a new tool, create the file in 'tools/<tool_name>.py'.\n"
                "2. You MUST register the new tool in 'main.py' (import it, add to ToolInfo list, add to execute_tool logic).\n"
                "3. Do NOT create standalone scripts in the root directory.\n"
                "4. Read TOOL_CREATION_GUIDE.md for details.\n\n"
                "Request: "
            )
            full_instruction = f"{prefix}{instruction}"
            
            resp = await client.post(
                f"{AIDER_API_URL}/fix",
                json={"instruction": full_instruction},
            )
            # ログが長いのでテキストとして全て取得
            full_log = ""
            async for chunk in resp.aiter_text():
                full_log += chunk
            return full_log
    except Exception as e:
        return f"Error calling Aider: {str(e)}"


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN is missing")
    else:
        print("🚀 Starting Discord Bot (Native Tools + History)...")
        client.run(DISCORD_BOT_TOKEN)
