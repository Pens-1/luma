import discord
from discord.ext import commands
import os
import httpx
import asyncio
import re
import datetime
import json
from dotenv import load_dotenv

load_dotenv()

# 設定
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OLLAMA_URL = "http://luma-ollama:11434/api/chat"
API_URL = "http://localhost:8000/api/v1"
EVOLUTION_CHANNEL_ID = 1471837005284507750

# モデル設定
CHAT_MODEL = "gemma3:12b"       # 会話用（高速・日本語得意）
CODER_MODEL = "qwen3-coder:30b" # コーディング・推論用

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 会話履歴を保持する辞書 {channel_id: [{"role": "user", "content": ...}, ...]}
chat_histories = {}

SYSTEM_PROMPT = """
あなたはAI自律エンジニア「LUMA（ルーマ）」です。
「〜ですね」「〜しましょうか？」といった丁寧で親しみやすい日本語で話してください。

あなたの役割：
1. ユーザーの良きパートナーとして、開発やタスク管理をサポートする
2. 必要に応じてツールや機能を呼び出し、自律的に問題を解決する
3. 自身のコードを進化させ、より高度な機能を持てるようにする

利用可能なアクションタグ（回答に含めると実行されます）：
- [ACTION:WEATHER:日数のオフセット] : 天気を調べる (例: [ACTION:WEATHER:0] 今日)
- [ACTION:NOTION:ステータス] : Notionのタスクを確認 (例: [ACTION:NOTION:Not started] 未着手タスク)
- [ACTION:NOTION_CREATE:タスク名:期限] : Notionにタスクを追加 (例: [ACTION:NOTION_CREATE:買い物:2025-10-10])
- [ACTION:EVOLVE:ファイルパス:指示] : コードを修正する (例: [ACTION:EVOLVE:app/bot.py:ログ出力を追加して])
- [ACTION:TEST] : 全機能の自己診断を実行 (例: [ACTION:TEST])

回答は常に日本語で行い、コードブロックは ```言語名 で囲んでください。
"""

async def ask_ollama(channel_id: int, user_input: str) -> str:
    """Ollama Chat API にリクエストを投げる（履歴対応）"""
    global chat_histories
    
    if channel_id not in chat_histories:
        chat_histories[channel_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    # 履歴に追加
    chat_histories[channel_id].append({"role": "user", "content": user_input})
    
    # 履歴が長すぎたら古いものを削除（システムプロンプトは残す）
    if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = [chat_histories[channel_id][0]] + chat_histories[channel_id][-9:]

    payload = {
        "model": CHAT_MODEL,
        "messages": chat_histories[channel_id],
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_ctx": 4096
        }
    }

    print(f"🤖 Calling Ollama API: {CHAT_MODEL}, History Len: {len(chat_histories[channel_id])}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload)
            print(f"🔄 Ollama Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                bot_reply = result.get("message", {}).get("content", "")
                
                # Botの返答も履歴に追加
                chat_histories[channel_id].append({"role": "assistant", "content": bot_reply})
                print(f"💡 AI Answer Length: {len(bot_reply)}")
                return bot_reply
            else:
                print(f"❌ Ollama API Error: {response.text}")
                return f"⚠️ Ollama Error: {response.text}"
        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"❌ Connection Error: {str(e)}"

async def send_split_message(messageable, text):
    """2000文字を超えるメッセージを分割して送信"""
    if len(text) <= 2000:
        await messageable.reply(text)
        return

    # コードブロックの検出など、より賢い分割も可能だがまずは単純分割
    chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
    for chunk in chunks:
        await messageable.send(chunk)

@bot.event
async def on_ready():
    print(f"✅ LUMA Local Bot logged in as {bot.user}")
    print(f"🧠 Chat Model: {CHAT_MODEL} / Coder Model: {CODER_MODEL}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"📨 Reading Message from {message.author} (Channel: {message.channel}): {message.content}")

    # コマンド処理
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # メンションなしでも反応（全メッセージに応答）
    # ただし、他のBotのメッセージや、空メッセージは無視しても良いかも
    if message.author.bot:
        return

    print(f"📩 Message received from {message.author}: {message.content}")
    async with message.channel.typing():
        # メンション部分を除去（もしあれば）
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content:
            # メンションのみの場合は挨拶
            clean_content = "こんにちは"

        today_str = datetime.date.today().isoformat()
        
        # コンテキストに日時情報を注入
        context_input = f"（現在日時: {today_str}）\n{clean_content}"
        print(f"📝 Asking Ollama: {clean_content}")
        
        answer = await ask_ollama(message.channel.id, context_input)

    # --- アクション処理 ---
    
    # 天気
    weather_match = re.search(r"\[ACTION:WEATHER:(\d+)\]", answer)
    if weather_match:
        day_index = int(weather_match.group(1))
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(f"{API_URL}/plugins/weather-clothing/?day_index={day_index}")
                if res.status_code == 200:
                    data = res.json()
                    day_label = data.get("day_label", "指定日")
                    weather_info = (
                        f"\n\n🌍 **{day_label}（{data.get('date', '')}）の天気予報**\n"
                        f"🌡️ 気温: {data['today']['min_temp']}℃ 〜 {data['today']['max_temp']}℃\n"
                        f"💡 **服装アドバイス**: {data['suggestion']}\n"
                        f"☔ **傘の必要性**: {'必要です ☔' if data.get('umbrella_needed') else '不要です ☀️'}"
                    )
                    answer = re.sub(r"\[ACTION:WEATHER:\d+\]", weather_info, answer)
            except Exception as e:
                answer += f"\n(天気情報の取得に失敗しました: {e})"

    # Notion Todo
    notion_match = re.search(r"\[ACTION:NOTION:([^\]]+)\]", answer)
    if notion_match:
        status_query = notion_match.group(1).strip() # "Not started" など
        if status_query == "TODO": status_query = "Not started" # エイリアス
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(f"{API_URL}/plugins/notion/todos", params={"status": status_query})
                if res.status_code == 200:
                    data = res.json()
                    if "error" in data:
                        notion_info = f"\n⚠️ Notion Error: {data['error']}"
                    else:
                        tasks = data.get("tasks", [])
                        if not tasks:
                            notion_info = f"\n\n📝 **{status_query} のタスクはありません** 🎉"
                        else:
                            task_list = "\n".join([f"- [{t['priority']}] {t['title']} (Due: {t['due_date'] or 'No Date'})" for t in tasks[:5]])
                            notion_info = f"\n\n📝 **Notion タスク一覧 ({status_query})**\n{task_list}\n(他 {len(tasks)-5} 件)" if len(tasks) > 5 else f"\n\n📝 **Notion タスク一覧 ({status_query})**\n{task_list}"
                    
                    answer = re.sub(r"\[ACTION:NOTION:[^\]]+\]", notion_info, answer)
            except Exception as e:
                    answer += f"\n(Notion情報の取得に失敗しました: {e})"

    # Self-Test
    if "[ACTION:TEST]" in answer:
        await message.channel.send("🔍 **自己診断を開始します...**")
        report = ["🔍 **LUMA Self-Diagnosis Report**"]
        
        async with httpx.AsyncClient() as client:
            # 1. Weather API
            try:
                res = await client.get(f"{API_URL}/plugins/weather-clothing/")
                if res.status_code == 200:
                    report.append(f"✅ Weather API: OK ({res.status_code})")
                else:
                    report.append(f"❌ Weather API: Error ({res.status_code})")
            except Exception as e:
                report.append(f"❌ Weather API: Failed ({str(e)})")

            # 2. Notion API (Read)
            try:
                res = await client.get(f"{API_URL}/plugins/notion/todos?status=Not+started")
                if res.status_code == 200:
                    data = res.json()
                    if "error" in data:
                        report.append(f"⚠️ Notion API (Read): Logic Error ({data['error']})")
                    else:
                        report.append(f"✅ Notion API (Read): OK ({len(data.get('tasks', []))} tasks found)")
                else:
                    report.append(f"❌ Notion API (Read): Error ({res.status_code})")
            except Exception as e:
                report.append(f"❌ Notion API (Read): Failed ({str(e)})")
        
        report.append("\nDiagnosis Completed.")
        answer = "\n".join(report)

    # Notion Todo Create
    # 形式: [ACTION:NOTION_CREATE:タスク名] または [ACTION:NOTION_CREATE:タスク名:期限]
    notion_create_match = re.search(r"\[ACTION:NOTION_CREATE:([^:\]]+)(?::([^\]]+))?\]", answer)
    if notion_create_match:
        title = notion_create_match.group(1).strip()
        due_date = notion_create_match.group(2).strip() if notion_create_match.group(2) else None
        
        async with httpx.AsyncClient() as client:
            try:
                # FastAPIのエンドポイント定義に合わせてQueryパラメータとして送る
                params = {"title": title}
                if due_date:
                    params["due_date"] = due_date
                
                res = await client.post(f"{API_URL}/plugins/notion/todos", params=params)
                
                # --- AI評価ループ (Self-Correction) ---
                from app.services.evaluator import evaluate_execution
                intent = f"Create a Notion task titled '{title}' with due_date '{due_date}'."
                result_text = f"Status Code: {res.status_code}\nResponse Body: {res.text}"
                
                # 結果をAIに評価させる
                evaluation = await evaluate_execution(intent, result_text, context="Target File: app/plugins/notion_query.py")
                
                if evaluation.get("success", False):
                    # 成功判定
                    data = res.json()
                    notion_msg = f"\n\n✅ **Notionタスクを作成しました**\n📌 [{data.get('title', title)}]({data.get('url', '')})"
                    answer = re.sub(r"\[ACTION:NOTION_CREATE:[^\]]+\]", notion_msg, answer)
                else:
                    # 失敗判定 (APIエラーまたは論理エラー)
                    reason = evaluation.get("reason", "Unknown Error")
                    fix_instruction = evaluation.get("fix_instruction", "Please fix the code based on the error.")
                    
                    # 報告: 分析結果
                    analysis_msg = (
                        f"🚫 **Action Failed**\n"
                        f"🤔 **Analysis**: {reason}\n"
                        f"💡 **Proposed Fix**: {fix_instruction}\n"
                        f"🚀 **Starting LUMA-Cycle (Auto-Repair)**..."
                    )
                    await message.channel.send(analysis_msg)
                    
                    # 失敗時はOllamaの嘘メッセージを上書き
                    answer = "🚨 エラーが発生したため、自動修復プロセスに移行しました。" 
                    
                    from app.services.aider_evolver import run_aider_evolution
                    # 修正を実行
                    result_msg = await run_aider_evolution(fix_instruction, "app/plugins/notion_query.py")
                    
                    final_report = f"\n🔧 **修正完了**\n{result_msg}"
                    await message.channel.send(final_report)
                    
                    if "Aider" in result_msg:
                        await message.channel.send("🔄 **修正を適用するため再起動します**。")

            except Exception as e:
                answer += f"\n(タスク作成失敗: {e})"
    
    # 自己進化
    # 形式: [ACTION:EVOLVE:対象ファイル:指示内容] または [ACTION:EVOLVE]
    evolve_match = re.search(r"\[ACTION:EVOLVE(:([^:]+):(.+))?\]", answer)
    if evolve_match:
        target_file = evolve_match.group(2) or "app/bot.py"
        instruction = evolve_match.group(3) or "現状の機能を維持したまま、コードを整理・最適化してください。"
        
        await message.channel.send(f"🚀 **自己進化プロセスを開始しました (Aider)**\nターゲット: `{target_file}`\n指示: {instruction}\n(これには数分かかる場合があります...)")
        
        from app.services.aider_evolver import run_aider_evolution
        result_msg = await run_aider_evolution(instruction, target_file)
        
        await send_split_message(message, result_msg)
        
        # 自分自身を変更した場合は再起動通知（start.shが検知して再起動する）
        if "bot.py" in target_file and "Aider" in result_msg:
            await message.channel.send("🔄 **システムの再起動を検知しました**。数秒後に復活します。")

    await send_split_message(message, answer)

@bot.command()
async def weather(ctx):
    """今日の天気を教えます"""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{API_URL}/plugins/weather-clothing/")
            data = res.json()
            await ctx.reply(f"🌡️ 今日は {data['today']['min_temp']}℃ 〜 {data['today']['max_temp']}℃ だよ。\n{data['suggestion']}")
        except:
            await ctx.reply("天気情報の取得に失敗しました。")

@bot.command()
async def clear(ctx):
    """会話履歴をクリアします"""
    global chat_histories
    if ctx.channel.id in chat_histories:
        del chat_histories[ctx.channel.id]
        await ctx.reply("🧹 会話履歴を忘れました。新しい話題で話しましょう！")
    else:
        await ctx.reply("履歴はまだありません。")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    # Discordのログを詳細に出す
    logging.getLogger("discord").setLevel(logging.DEBUG)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.state").setLevel(logging.INFO)

    bot.run(DISCORD_TOKEN)
